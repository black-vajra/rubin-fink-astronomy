#!/usr/bin/env python3
"""Rubin public-API evidence collector. No authentication or discovery claims.

Uses the existing RubinWatchPilot SQLite tables without replacing them.
Heuristic thresholds are for review, not probabilities or confirmed discoveries.
"""
import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import fcntl
import hashlib
import html
import io
import json
import math
from pathlib import Path
import sqlite3
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

try:
    import numpy as np
    from astropy.time import Time
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(f'{exc}\nRun with ~/rubin-watch/venv/bin/python (the Fink environment).')

VERSION = '1.0.0'
BASE = 'https://api.lsst.fink-portal.org/api/v1/'
TAGS = ['hostless_candidate', 'extragalactic_new_candidate', 'extragalactic_lt20mag_candidate']
FLAGS = ['psfFlux_flag', 'centroid_flag', 'pixelFlags_bad',
         'pixelFlags_saturatedCenter', 'pixelFlags_crCenter',
         'pixelFlags_nodata', 'pixelFlags_edge', 'isDipole',
         'pixelFlags_injected', 'pixelFlags_injected_template', 'glint_trail']
CORE_FLAGS = ['psfFlux_flag', 'centroid_flag', 'pixelFlags_bad',
              'pixelFlags_saturatedCenter', 'pixelFlags_crCenter', 'pixelFlags_nodata']
LIMITATIONS = [
    'Selected public-API samples, not the complete Rubin survey. A full-sized response '
    'means possible omissions. Even overlapping samples cannot prove complete coverage.',
    'Newly downloaded is not newly observed. Historical observations remain labelled historical.',
    'Photometry uses signed difference-image flux in nJy, separated by filter. '
    'It is not total brightness. Thresholds are exploratory and uncorrected for selection/multiple tests.',
    'Position fits are within one broker-associated object, within one filter, on short arcs. '
    'They can reflect mis-association, centroid errors, parallax, proper motion, or artifacts. '
    'No cross-object linking or orbit fitting is performed; this is not a Planet Nine search.',
    'Broker catalog matches are recorded when present. No independent catalog search, '
    'image-cutout inspection, or scientific confirmation is performed automatically.',
    'Quality flags may be absent or unpopulated. Unknown quality is retained, '
    'but those measurements are excluded from the watchlist. Reliability is displayed, not trusted as a gate.',
    'Daily reports use a rolling 24-hour schedule while this program runs. '
    'Stopping the computer stops collection; the next run reports the elapsed gap.',
]


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def log(message):
    # Remove terminal escape/control codes from remote text.
    clean = ''.join(c for c in str(message) if c.isprintable() or c == '\n')
    print(f'[{now()}] {clean}', flush=True)


def num(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def ident(value, optional=False):
    # Never round an identifier through floating point.
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError('Missing/unsafe integer identifier (float IDs rejected)')
    value = str(value)
    if not value.isascii() or not value.isdecimal() or len(value) > 30:
        raise ValueError('Invalid identifier')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def utc(mjd):
    return Time(mjd, format='mjd', scale='tai').utc.isot + 'Z'


def age_days(mjd):
    return float(Time.now().tai.mjd - mjd)


def freshness(mjd):
    if mjd is None:
        return 'NO OBSERVATION TIME'
    age = age_days(mjd)
    if age < -0.01:
        return 'FUTURE TIME: CHECK DATA'
    return f'{"HISTORICAL" if age > 2 else "RECENT"} | age {max(age, 0):.1f} days | {utc(mjd)}'


def normalize(row):
    if not isinstance(row, dict):
        raise ValueError('Detection must be a JSON object')
    sid = ident(row.get('r:diaSourceId'))
    oid = ident(row.get('r:diaObjectId'), optional=True)
    if oid == '0':
        oid = None
    values = {name: num(row.get('r:' + name)) for name in (
        'midpointMjdTai', 'psfFlux', 'psfFluxErr', 'scienceFlux', 'scienceFluxErr',
        'ra', 'dec', 'raErr', 'decErr', 'reliability', 'trailLength')}
    reasons, missing = [], []
    for flag in FLAGS:
        value = row.get('r:' + flag)
        if value is True or (isinstance(value, int) and value == 1):
            reasons.append(flag)
        if flag in CORE_FLAGS and not (isinstance(value, bool) or
                (isinstance(value, int) and value in (0, 1))):
            missing.append(flag)
    withdrawn = num(row.get('r:timeWithdrawnMjdTai'))
    if withdrawn is not None and withdrawn > 0:
        reasons.append('withdrawn')
    if values['midpointMjdTai'] is None or not 50000 < values['midpointMjdTai'] < 100000:
        reasons.append('invalid_time')
    if values['psfFlux'] is None or values['psfFluxErr'] is None or values['psfFluxErr'] <= 0:
        reasons.append('invalid_flux_or_error')
    band = row.get('r:band')
    if band not in list('ugrizy'):
        reasons.append('invalid_band')
    matches = {k: v for k, v in row.items() if k.startswith('f:xm_') and
               v is not None and str(v).strip() not in ('', 'Fail', 'Unknown')}
    ssid = row.get('r:ssObjectId')
    known_sso = ssid is not None and str(ssid) not in ('0', '-1', 'None', '')
    return dict(values, sid=sid, oid=oid, band=band,
                visit=str(row.get('r:visit') or ''), bad=reasons, missing=missing,
                usable=not reasons and not missing, matches=matches, known_sso=known_sso)


def connect(path):
    existed = path.exists() and path.stat().st_size > 0
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    if existed and db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rw_meta'").fetchone() is None:
        backup_dir = path.parent/'backups'
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir/('rubin-before-public-watch-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.sqlite3')
        with sqlite3.connect(backup_path) as backup:
            db.backup(backup)
        log('Pilot database backup: ' + str(backup_path))
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS fetches (
      id INTEGER PRIMARY KEY, retrieved_utc TEXT NOT NULL, selection TEXT NOT NULL,
      url TEXT NOT NULL, returned_count INTEGER, error TEXT);
    CREATE TABLE IF NOT EXISTS detections (
      source_id TEXT PRIMARY KEY, first_seen_utc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS record_versions (
      source_id TEXT NOT NULL REFERENCES detections(source_id), payload_hash TEXT NOT NULL,
      first_fetch_id INTEGER NOT NULL REFERENCES fetches(id), payload_json TEXT NOT NULL,
      PRIMARY KEY(source_id,payload_hash));
    CREATE TABLE IF NOT EXISTS fetch_records (
      fetch_id INTEGER NOT NULL REFERENCES fetches(id), source_id TEXT NOT NULL,
      payload_hash TEXT NOT NULL, PRIMARY KEY(fetch_id,source_id,payload_hash),
      FOREIGN KEY(source_id,payload_hash) REFERENCES record_versions(source_id,payload_hash));
    CREATE TABLE IF NOT EXISTS rw_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS rw_measurements (
      sid TEXT PRIMARY KEY, oid TEXT, mjd REAL, band TEXT, normalized TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS rw_object ON rw_measurements(oid);
    CREATE TABLE IF NOT EXISTS rw_history (
      oid TEXT PRIMARY KEY, attempted REAL NOT NULL, status TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS rw_selection (
      oid TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY(oid,tag));
    CREATE TABLE IF NOT EXISTS rw_coverage (
      id INTEGER PRIMARY KEY, utc TEXT NOT NULL, selection TEXT NOT NULL,
      detail TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS rw_candidates (
      key TEXT PRIMARY KEY, oid TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
      first_flagged TEXT NOT NULL, changed TEXT NOT NULL, fingerprint TEXT NOT NULL,
      evidence TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS rw_evidence (
      id INTEGER PRIMARY KEY, utc TEXT NOT NULL, candidate_key TEXT NOT NULL,
      status TEXT NOT NULL, evidence TEXT NOT NULL);
    ''')
    if db.execute("SELECT value FROM rw_meta WHERE key='pilot_imported'").fetchone() is None:
        with db:
            records = db.execute('SELECT payload_json FROM record_versions ORDER BY first_fetch_id')
            count = 0
            for record in records:
                try:
                    m = normalize(json.loads(record[0]))
                except ValueError:
                    continue
                save_normal(db, m)
                count += 1
            # Recover pilot tag memberships without rewriting its archived rows.
            db.execute('''INSERT OR IGNORE INTO rw_selection
              SELECT m.oid,f.selection FROM rw_measurements m
              JOIN fetch_records r ON m.sid=r.source_id JOIN fetches f ON f.id=r.fetch_id
              WHERE m.oid IS NOT NULL AND f.selection NOT LIKE 'history:%' ''')
            meta(db, 'pilot_imported', now())
        log(f'Imported {count} existing record versions into analysis; originals preserved.')
    return db


def meta(db, key, value=None):
    if value is not None:
        db.execute('INSERT OR REPLACE INTO rw_meta VALUES (?,?)', (key, str(value)))
        return value
    row = db.execute('SELECT value FROM rw_meta WHERE key=?', (key,)).fetchone()
    return row[0] if row else None


def save_normal(db, m):
    db.execute('INSERT OR REPLACE INTO rw_measurements VALUES (?,?,?,?,?)',
               (m['sid'], m['oid'], m['midpointMjdTai'], m['band'], canonical(m)))


class Collector:
    def __init__(self, db):
        self.db = db
        self.next_request = 0
        self.failures = 0

    def request(self, endpoint, **params):
        time.sleep(max(0, self.next_request - time.monotonic()))
        url = BASE + endpoint + ('?' + urlencode(params) if params else '')
        try:
            req = Request(url, headers={'User-Agent': 'RubinPublicWatch/' + VERSION,
                                       'Accept': 'application/json'})
            with urlopen(req, timeout=30) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError('Response exceeds 20 MB limit; nothing partially imported')
            return json.loads(raw), url
        except HTTPError as exc:
            if exc.code == 429:
                wait = min(3600, max(60, num(exc.headers.get('Retry-After')) or 300))
                self.next_request = time.monotonic() + wait
            raise
        finally:
            self.next_request = max(self.next_request, time.monotonic() + 2)

    def fetch(self, selection, endpoint, **params):
        started = now()
        url = BASE + endpoint + '?' + urlencode(params)
        try:
            rows, url = self.request(endpoint, **params)
            if not isinstance(rows, list):
                raise ValueError('API did not return a detection list')
            prepared = []
            for row in rows:
                m = normalize(row)
                if selection.startswith('history:') and m['oid'] != selection.split(':', 1)[1]:
                    raise ValueError('History returned a different object ID')
                payload = canonical(row)
                prepared.append((m, payload, hashlib.sha256(payload.encode()).hexdigest()))
            added = versions = overlap = 0
            with self.db:
                fid = self.db.execute('''INSERT INTO fetches
                    (retrieved_utc,selection,url,returned_count) VALUES (?,?,?,?)''',
                    (started, selection, url, len(rows))).lastrowid
                for m, payload, digest in prepared:
                    n = self.db.execute('INSERT OR IGNORE INTO detections VALUES (?,?)',
                                        (m['sid'], started)).rowcount
                    added += n
                    overlap += int(not n)
                    versions += self.db.execute('INSERT OR IGNORE INTO record_versions VALUES (?,?,?,?)',
                                                 (m['sid'], digest, fid, payload)).rowcount
                    self.db.execute('INSERT OR IGNORE INTO fetch_records VALUES (?,?,?)',
                                    (fid, m['sid'], digest))
                    save_normal(self.db, m)
                    if not selection.startswith('history:') and m['oid']:
                        self.db.execute('INSERT OR IGNORE INTO rw_selection VALUES (?,?)',
                                        (m['oid'], selection))
            times = [m['midpointMjdTai'] for m, _, _ in prepared if m['midpointMjdTai']]
            latest = max(times) if times else None
            log(f'{selection}: {len(rows)} returned | {added} new detections | '
                f'{versions} new versions | {overlap} already known')
            log('  ' + freshness(latest))
            if endpoint == 'tags':
                full = len(rows) >= int(params['n'])
                detail = dict(returned=len(rows), new=added, overlapping=overlap,
                              sample_limit=int(params['n']), limit_reached=full,
                              latest_mjd_tai=latest, completeness='UNVERIFIED')
                with self.db:
                    self.db.execute('INSERT INTO rw_coverage(utc,selection,detail) VALUES (?,?,?)',
                                    (started, selection, canonical(detail)))
                if full:
                    log('  COVERAGE WARNING: sample limit reached; additional records may be missing.')
            return True
        except Exception as exc:
            self.failures += 1
            message = f'{type(exc).__name__}: {exc}'
            with self.db:
                self.db.execute('''INSERT INTO fetches(retrieved_utc,selection,url,error)
                                 VALUES (?,?,?,?)''', (started, selection, url, message))
            log(f'SOURCE ERROR [{selection}]: {message}')
            return False


def unique_visits(rows):
    # One best-S/N measurement per exposure/filter, even if multiple source IDs exist.
    visits = {}
    for r in rows:
        key = (r['band'], r['visit'] or r['midpointMjdTai'])
        previous = visits.get(key)
        if previous is None or abs(r['psfFlux']) / r['psfFluxErr'] > abs(previous['psfFlux']) / previous['psfFluxErr']:
            visits[key] = r
    return sorted(visits.values(), key=lambda r: r['midpointMjdTai'])


def weighted_line(t, y, errors):
    t, y, errors = [np.asarray(a, dtype=float) for a in (t, y, errors)]
    t = t - np.mean(t)
    A = np.column_stack([np.ones(len(t)), t]) / errors[:, None]
    fit, _, rank, _ = np.linalg.lstsq(A, y / errors, rcond=None)
    if rank != 2:
        raise ValueError('Degenerate position fit')
    cov = np.linalg.inv(A.T @ A)
    residual = y - np.column_stack([np.ones(len(t)), t]) @ fit
    reduced = float(np.sum((residual / errors) ** 2) / (len(t) - 2))
    slope_error = math.sqrt(float(cov[1, 1]) * max(1, reduced))
    return float(fit[1]), slope_error, reduced


def screen(oid, rows, tags):
    usable = unique_visits([r for r in rows if r['usable'] and
                            abs(r['psfFlux']) / r['psfFluxErr'] >= 5])
    found = []
    by_band = defaultdict(list)
    for r in usable:
        by_band[r['band']].append(r)
    for band, group in sorted(by_band.items()):
        days = defaultdict(list)
        for r in group:
            days[math.floor(r['midpointMjdTai'])].append(r)
        bins = []
        for day, values in sorted(days.items()):
            f = np.array([r['psfFlux'] for r in values])
            e = np.array([r['psfFluxErr'] for r in values])
            w = 1 / e**2
            mean = float(np.sum(w * f) / np.sum(w))
            # Increase uncertainty when within-day scatter exceeds stated errors.
            scale = max(1, float(np.sum(w * (f-mean)**2) / max(1, len(f)-1)))
            err = math.sqrt(scale / float(np.sum(w)))
            bins.append((day, mean, err, len(values)))
        if len(bins) >= 3 and len(group) >= 4:
            low, high = min(bins, key=lambda b: b[1]), max(bins, key=lambda b: b[1])
            change = high[1] - low[1]
            score = change / math.hypot(low[2], high[2])
            if score >= 7:
                found.append((f'flux:{band}', dict(
                    band=band, heuristic_change_sigma=round(score, 2),
                    difference_flux_range_njy=round(change, 3),
                    tai_day_bins=len(bins), independent_visits=len(group),
                    explanation='Same-filter difference-flux change across >=3 TAI calendar-day bins; review images and calibration.')))
        # A repeat is evidence of persistence, not proof of an unusual transient.
        if 'hostless_candidate' in tags and len(group) >= 3 and len(days) >= 2:
            found.append((f'repeated-hostless:{band}', dict(
                band=band, independent_visits=len(group), tai_day_bins=len(days),
                explanation='Repeated >=5-S/N detections in a broker hostless selection; hostlessness and novelty remain unverified.')))
        # Small-angle same-band centroid diagnostic, never an inferred orbit/distance.
        pos = [r for r in group if all(r[k] is not None for k in ('ra', 'dec', 'raErr', 'decErr'))
               and 0 <= r['ra'] < 360 and abs(r['dec']) < 85
               and r['raErr'] > 0 and r['decErr'] > 0]
        if pos:
            cutoff = max(r['midpointMjdTai'] for r in pos) - 30
            pos = [r for r in pos if r['midpointMjdTai'] >= cutoff]
        if len(pos) < 5 or any(r['known_sso'] for r in group):
            continue
        times = [r['midpointMjdTai'] for r in pos]
        span = max(times) - min(times)
        if not 1 <= span <= 30 or len({math.floor(t) for t in times}) < 3:
            continue
        ra0, dec0 = pos[0]['ra'], pos[0]['dec']
        cosine = math.cos(math.radians(dec0))
        x = [((r['ra']-ra0+180) % 360-180) * 3600 * cosine for r in pos]
        y = [(r['dec']-dec0) * 3600 for r in pos]
        # 0.10 arcsec per-axis systematic floor; RA/Dec errors are in degrees.
        xe = [math.hypot(r['raErr'] * 3600 * cosine, .10) for r in pos]
        ye = [math.hypot(r['decErr'] * 3600, .10) for r in pos]
        if max(map(abs, x+y)) > 60:
            continue
        try:
            vx, ex, cx = weighted_line(times, x, xe)
            vy, ey, cy = weighted_line(times, y, ye)
        except (ValueError, np.linalg.LinAlgError):
            continue
        snr = math.hypot(vx/ex, vy/ey)
        speed = math.hypot(vx, vy)
        if snr >= 5 and max(cx, cy) <= 5 and speed * span >= .5:
            found.append((f'position:{band}', dict(
                band=band, rate_arcsec_day=round(speed, 5),
                heuristic_motion_sigma=round(snr, 2), span_days=round(span, 3),
                independent_visits=len(pos), reduced_chi2_x=round(cx, 3),
                reduced_chi2_y=round(cy, 3),
                explanation='Centroid drift within ONE associated object/filter; review association and images. Not an unknown-body identification.')))
    latest = max((r['midpointMjdTai'] for r in rows if r['midpointMjdTai']), default=None)
    matches = {}
    for r in rows:
        matches.update(r['matches'])
    return [(kind, dict(e, object_id=oid, latest_mjd_tai=latest,
                       tags=sorted(tags), catalog_metadata=matches,
                       confirmation='UNVERIFIED: images and independent catalog checks needed'))
            for kind, e in found]


def analyze(db):
    groups, tags = defaultdict(list), defaultdict(set)
    for row in db.execute('SELECT normalized FROM rw_measurements WHERE oid IS NOT NULL'):
        m = json.loads(row[0]); groups[m['oid']].append(m)
    for row in db.execute('SELECT oid,tag FROM rw_selection'):
        tags[row[0]].add(row[1])
    flagged = {oid + '/' + kind: (oid, kind, evidence)
               for oid, rows in groups.items() for kind, evidence in screen(oid, rows, tags[oid])}
    changes = Counter()
    with db:
        previous = {r['key']: r for r in db.execute('SELECT * FROM rw_candidates')}
        for key, (oid, kind, evidence) in flagged.items():
            encoded = canonical(evidence)
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            old = previous.get(key)
            if old and old['fingerprint'] == digest and old['status'] == 'review':
                continue
            stamp = now()
            db.execute('INSERT OR REPLACE INTO rw_candidates VALUES (?,?,?,?,?,?,?,?)',
                       (key, oid, kind, 'review', old['first_flagged'] if old else stamp,
                        stamp, digest, encoded))
            db.execute('INSERT INTO rw_evidence(utc,candidate_key,status,evidence) VALUES (?,?,?,?)',
                       (stamp, key, 'review', encoded))
            changes['updated' if old else 'new'] += 1
        for key, old in previous.items():
            if key not in flagged and old['status'] == 'review':
                db.execute("UPDATE rw_candidates SET status='not_currently_flagged',changed=? WHERE key=?", (now(), key))
                db.execute('INSERT INTO rw_evidence(utc,candidate_key,status,evidence) VALUES (?,?,?,?)',
                           (now(), key, 'not_currently_flagged', old['evidence']))
                changes['no_longer_flagged'] += 1
    log(f'WATCHLIST: {len(flagged)} review flags on {len({v[0] for v in flagged.values()})} objects | changes {dict(changes)}')
    return groups


def plot_object(rows, oid):
    good = unique_visits([r for r in rows if r['usable']])
    fig, ax = plt.subplots(figsize=(8, 3.5), constrained_layout=True)
    for band in 'ugrizy':
        subset = [r for r in good if r['band'] == band]
        if subset:
            ax.errorbar([r['midpointMjdTai'] for r in subset], [r['psfFlux'] for r in subset],
                        yerr=[r['psfFluxErr'] for r in subset], fmt='o', ms=4, capsize=2, label=band)
    ax.axhline(0, color='gray', lw=.7)
    ax.set(xlabel='MJD (TAI)', ylabel='Difference PSF flux (nJy)', title='Object ' + oid)
    if good:
        ax.legend(title='Filter', ncol=6, fontsize=8)
    output = io.BytesIO(); fig.savefig(output, format='png', dpi=115); plt.close(fig)
    return base64.b64encode(output.getvalue()).decode()


def report(db, folder, groups):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = folder / 'reports' / stamp
    dest.mkdir(parents=True)
    candidates = [dict(r) for r in db.execute("SELECT * FROM rw_candidates ORDER BY status,oid,kind")]
    for r in candidates:
        r['evidence'] = json.loads(r['evidence'])
    fetches = [dict(r) for r in db.execute('SELECT * FROM fetches ORDER BY id DESC LIMIT 100')]
    coverage = [dict(r) for r in db.execute('SELECT * FROM rw_coverage ORDER BY id DESC LIMIT 60')]
    for c in coverage:
        c['detail'] = json.loads(c['detail'])
    totals = dict(detections=db.execute('SELECT count(*) FROM detections').fetchone()[0],
                  objects=len(groups), usable=sum(m['usable'] for rows in groups.values() for m in rows),
                  stored_versions=db.execute('SELECT count(*) FROM record_versions').fetchone()[0])
    latest = db.execute('SELECT max(mjd) FROM rw_measurements').fetchone()[0]
    payload = dict(version=VERSION, generated_utc=now(), latest_observation=freshness(latest),
                   totals=totals, limitations=LIMITATIONS, candidates=candidates,
                   recent_fetches=fetches, coverage=coverage)
    (dest / 'report.json').write_text(json.dumps(payload, indent=2, allow_nan=False))
    with (dest / 'watchlist.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['object_id', 'kind', 'status', 'latest_observation_utc', 'evidence_json'])
        for r in candidates:
            mjd = r['evidence']['latest_mjd_tai']
            writer.writerow([r['oid'], r['kind'], r['status'], utc(mjd) if mjd else '', canonical(r['evidence'])])
    esc = lambda x: html.escape(str(x), quote=True)
    active = [r for r in candidates if r['status'] == 'review']
    sections, plotted = [], set()
    for r in active:
        e = r['evidence']; oid = r['oid']
        portal = 'https://lsst.fink-portal.org/' + quote(oid, safe='')
        plot = ''
        if oid not in plotted and len(plotted) < 12:
            plot = '<img alt="Difference-flux light curve" src="data:image/png;base64,' + plot_object(groups[oid], oid) + '">'
            plotted.add(oid)
        sections.append(f'<article><h3>{esc(oid)} · {esc(r["kind"])}</h3>'
                        f'<p class="badge">{esc(freshness(e["latest_mjd_tai"]))}</p>'
                        f'<p>{esc(e["explanation"])}</p><p><a href="{portal}" target="_blank" rel="noopener noreferrer">Open Fink object &amp; image review ↗</a></p>'
                        f'{plot}<details><summary>Evidence and broker catalog metadata</summary><pre>{esc(json.dumps(e, indent=2))}</pre></details></article>')
    covrows = ''.join(f'<tr><td>{esc(c["utc"])}</td><td>{esc(c["selection"])}</td>'
                      f'<td>{c["detail"]["returned"]}</td><td>{esc(c["detail"]["limit_reached"])}</td></tr>'
                      for c in [x for x in coverage if 'returned' in x['detail']][:12])
    gaphtml = ''.join(f'<li>{esc(c["utc"])}: {c["detail"]["hours"]:.2f} hours between cycles.</li>'
                      for c in coverage if c['selection'] == 'collector-gap')
    errors = [r for r in fetches if r['error']]
    errorhtml = ''.join(f'<li>{esc(r["retrieved_utc"])} · {esc(r["selection"])} · {esc(r["error"])}</li>' for r in errors[:10]) or '<li>No errors in the latest 100 requests.</li>'
    unflagged = len(candidates)-len(active)
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1"><title>Rubin public watch · {stamp}</title>
    <style>body{{margin:0;background:#0b151d;color:#e6eef3;font:16px/1.6 system-ui,sans-serif}}
    main{{max-width:1000px;margin:auto;padding:35px 24px}}h1,h2,h3{{line-height:1.2}}
    h1{{font-size:36px}}a{{color:#73e4cd}}.badge{{color:#ffd58c}}article,section{{background:#14232e;border:1px solid #2d4352;border-radius:12px;padding:22px;margin:20px 0}}
    img{{max-width:100%;background:white;border-radius:6px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}}table{{width:100%;font-size:13px;border-collapse:collapse}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #2d4352}}.scroll{{overflow-x:auto}}li{{margin:10px 0}}</style>
    <main><p>RUBIN / FINK · PUBLIC API · REVIEW REPORT</p><h1>Evidence worth another look.</h1>
    <p>Generated {esc(payload['generated_utc'])} · version {VERSION}</p><p class="badge">{esc(payload['latest_observation'])}</p>
    <section><h2>Collection and review</h2><p>{totals['detections']:,} distinct detections · {totals['objects']:,} associated objects · {len(active)} active review flags · {unflagged} retained flags no longer meeting thresholds.</p>
    <p>These are review suggestions. Zero flags does not mean no unusual phenomena exist. Raw record versions, source URLs, and fetch times remain in SQLite.</p></section>
    <section><h2>Coverage and interpretation</h2><ul>{''.join('<li>'+esc(s)+'</li>' for s in LIMITATIONS)}</ul></section>
    <h2>Watchlist</h2>{''.join(sections) or '<p>No candidates currently meet the configured review thresholds.</p>'}
    <section><h2>Recent tag queries</h2><div class="scroll"><table><tr><th>Retrieved UTC</th><th>Selection</th><th>Rows</th><th>Limit reached</th></tr>{covrows}</table></div></section>
    <section><h2>Recent collection gaps</h2><ul>{gaphtml or '<li>No gap recorded in the latest coverage entries. Coverage remains unverified.</li>'}</ul></section>
    <section><h2>Recent source errors</h2><ul>{errorhtml}</ul></section>
    <p>Full machine-readable output: <a href="report.json">JSON report</a> · <a href="watchlist.csv">CSV watchlist</a></p>
    <p>Sources: <a href="https://doc.lsst.fink-broker.org/services/api/tagsearch/">tag and history access</a> · <a href="https://doc.lsst.fink-broker.org/data/photometry/">photometry</a> · <a href="https://doc.lsst.fink-broker.org/data/issues/">known issues</a></p></main></html>'''
    (dest / 'index.html').write_text(document)
    (folder / 'reports' / 'latest.html').write_text(
        f'<!doctype html><meta charset="utf-8"><title>Latest Rubin report</title>'
        f'<a href="{stamp}/index.html">Open latest report: {stamp}</a>')
    with db:
        meta(db, 'last_report', time.time())
    log('REPORT: ' + str(dest / 'index.html'))
    return dest


def cycle(db, args):
    previous = num(meta(db, 'last_cycle'))
    if previous is not None and time.time()-previous > args.interval*2:
        gap = (time.time()-previous)/3600
        log(f'COLLECTION GAP: {gap:.2f} hours since last completed cycle; missed data possible.')
        with db:
            db.execute('INSERT INTO rw_coverage(utc,selection,detail) VALUES (?,?,?)',
                       (now(), 'collector-gap', canonical(dict(hours=gap, completeness='GAP'))))
    collector = Collector(db)
    for tag in args.tags:
        collector.fetch(tag, 'tags', tag=tag, n=args.sample, **{'output-format': 'json'})
    # Round-robin due objects: bounded work and persistent cooldown across restarts.
    todo = db.execute('''SELECT DISTINCT m.oid,coalesce(h.attempted,0) attempted
        FROM rw_measurements m LEFT JOIN rw_history h ON h.oid=m.oid
        WHERE m.oid IS NOT NULL AND coalesce(h.attempted,0) < ?
        ORDER BY attempted,m.oid LIMIT ?''', (time.time()-6*3600, args.histories)).fetchall()
    for row in todo:
        oid = row['oid']
        ok = collector.fetch('history:'+oid, 'sources', diaObjectId=oid, **{'output-format': 'json'})
        with db:
            db.execute('INSERT OR REPLACE INTO rw_history VALUES (?,?,?)',
                       (oid, time.time(), 'ok' if ok else 'error'))
    groups = analyze(db)
    last = num(meta(db, 'last_report'))
    if args.report or last is None or time.time()-last >= 86400:
        report(db, args.data_dir, groups)
    with db:
        meta(db, 'last_cycle', time.time())
    log('Totals: ' + str(db.execute('SELECT count(*) FROM detections').fetchone()[0]) +
        ' detections | reports: ' + str(args.data_dir/'reports'/'latest.html'))
    return collector.failures


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=Path.home()/'rubin-watch')
    p.add_argument('--interval', type=int, default=600, help='Seconds between completed polls (minimum 300).')
    p.add_argument('--sample', type=int, default=100, help='Latest alerts per tag (1..1000); never complete-survey coverage.')
    p.add_argument('--histories', type=int, default=6, help='Objects whose histories to retrieve per cycle (0..20).')
    p.add_argument('--tags', nargs='+', default=TAGS)
    p.add_argument('--once', action='store_true', help='Collect/analyze once and exit.')
    p.add_argument('--report', action='store_true', help='Force report after collection; use with --once for an immediate report.')
    p.add_argument('--report-only', action='store_true', help='No network calls; analyze existing DB and make a report.')
    args = p.parse_args()
    if args.interval < 300 or not 1 <= args.sample <= 1000 or not 0 <= args.histories <= 20:
        p.error('Require interval >=300, sample 1..1000, histories 0..20.')
    args.data_dir = args.data_dir.expanduser().resolve()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    with (args.data_dir/'rubin-public-watch.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another Rubin Public Watch process is using this data directory.')
        db = connect(args.data_dir/'rubin.sqlite3')
        try:
            log(f'RUBIN PUBLIC WATCH {VERSION} | database: {args.data_dir/"rubin.sqlite3"}')
            log('Real public measurements; selected coverage; all flags UNVERIFIED.')
            if args.report_only:
                report(db, args.data_dir, analyze(db))
                return 0
            while True:
                try:
                    failures = cycle(db, args)
                except Exception as exc:
                    db.rollback()
                    log(f'CYCLE ERROR: {type(exc).__name__}: {exc}. Committed data retained.')
                    failures = 1
                if args.once:
                    return 2 if failures else 0
                delay = min(3600, args.interval * (2 if failures else 1))
                log(f'Next cycle in {delay}s. Ctrl+C to stop. Source errors logged in SQLite.')
                deadline = time.monotonic()+delay
                while time.monotonic() < deadline:
                    time.sleep(min(1, max(0, deadline-time.monotonic())))
        except KeyboardInterrupt:
            log('Stopped; committed records preserved.')
            return 0
        finally:
            db.close()


if __name__ == '__main__':
    sys.exit(main())

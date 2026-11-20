#!/usr/bin/env python3
"""Bounded public Rubin/Fink distant-body candidate linker, not an orbit solver."""
import argparse
import base64
from collections import defaultdict
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
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import rw_core as core
import numpy as np
from astropy import units as u
from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
from astropy.time import Time
import matplotlib.pyplot as plt

VERSION = '0.2.0'
ARCSEC = 206264.806247
AU_KM = 149597870.7
RADII = [50, 80, 120, 200, 300, 400, 600, 900, 1500, 2500]
WARNINGS = [
 'Experimental linkage proposals, not confirmed objects or discoveries. A trial heliocentric radius is a MODEL INPUT, not a measured distance.',
 'Public cones return the latest alert per indexed object. Histories are fetched separately and in a limited rotation. Truly unassociated detections not indexed as objects may be inaccessible.',
 'Default fields are small patches around existing alert locations, not a published Planet Nine probability map or an all-sky survey. Positive detections below the alert threshold are absent; image-level shift-and-stack is not performed.',
 'No orbit fit, acceleration fit, radial-velocity solution, mass measurement, or planetary classification. Fixed-radius short-arc models can be degenerate and can produce accidental linkages.',
 'One filter at a time; >=6 visits on >=4 UTC-noon night bins spanning 7–90 days. These cuts sacrifice sensitivity. Capped samples, point/seed budgets, and historical data are explicitly recorded.',
 'A missing ssObjectId or absent catalog match does not prove novelty. SkyBoT is checked only for a bounded number of top proposals; service failures remain UNCHECKED. Image inspection and independent orbital follow-up are required.',
 'Size scenarios assume all measured science flux belongs to one unblended reflecting body, zero phase angle, an SDSS-r solar proxy, and r-band geometric albedo 0.04–0.60. They are not measured sizes, masses, or probabilities.',
 'The model uses a geocentric observer and builtin solar ephemerides, a 0.20 arcsec per-axis systematic error floor, and a 20% angular-speed allowance. Topocentric offsets, light-time dynamics, RA–Dec covariance, calibration systematics, and full gravitational dynamics are not modeled.',
]


def schema(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS dw_fields(label TEXT PRIMARY KEY,ra REAL NOT NULL,
      dec REAL NOT NULL,radius REAL NOT NULL,attempted REAL DEFAULT 0,description TEXT);
    CREATE TABLE IF NOT EXISTS dw_members(label TEXT NOT NULL,oid TEXT NOT NULL,PRIMARY KEY(label,oid));
    CREATE TABLE IF NOT EXISTS dw_runs(id INTEGER PRIMARY KEY,utc TEXT,kind TEXT,detail TEXT);
    CREATE TABLE IF NOT EXISTS dw_tracks(id TEXT PRIMARY KEY,status TEXT,first_seen TEXT,
      updated TEXT,fingerprint TEXT,evidence TEXT);
    CREATE TABLE IF NOT EXISTS dw_audit(id INTEGER PRIMARY KEY,utc TEXT,track TEXT,status TEXT,evidence TEXT);
    CREATE TABLE IF NOT EXISTS dw_skybot(url TEXT PRIMARY KEY,checked REAL,result TEXT,raw BLOB);
    ''')


def record(db, kind, data):
    with db:
        db.execute('INSERT INTO dw_runs(utc,kind,detail) VALUES (?,?,?)',
                   (core.now(), kind, core.canonical(data)))


def vectors(ra, dec):
    a, d = np.radians(ra), np.radians(dec)
    return np.column_stack([np.cos(d)*np.cos(a), np.cos(d)*np.sin(a), np.sin(d)])


def basis(ra, dec):
    a, d = math.radians(ra), math.radians(dec)
    return (np.array([math.cos(d)*math.cos(a), math.cos(d)*math.sin(a), math.sin(d)]),
            np.array([-math.sin(a), math.cos(a), 0]),
            np.array([-math.sin(d)*math.cos(a), -math.sin(d)*math.sin(a), math.cos(d)]))


def project(v, b):
    normal, east, north = b
    den = v @ normal
    if np.any(den <= 0):
        raise ValueError('Projection crosses the tangent-plane horizon')
    return np.column_stack([v @ east/den, v @ north/den]) * ARCSEC


def earth_positions(mjd):
    times = Time(mjd, format='mjd', scale='tai')
    with solar_system_ephemeris.set('builtin'):
        return (get_body_barycentric('earth', times) - get_body_barycentric('sun', times)).xyz.to_value(u.au).T


def deparallax(n, earth, radius, b):
    # Ray/sphere intersection in heliocentric ICRS coordinates.
    en = np.sum(earth*n, axis=1)
    delta = -en + np.sqrt(en**2 + radius**2 - np.sum(earth**2, axis=1))
    return project(earth + delta[:, None]*n, b), delta


def eligible(m):
    return (m['usable'] and not m['known_sso'] and m['psfFlux'] > 0 and
            m['psfFlux']/m['psfFluxErr'] >= 5 and
            all(m[k] is not None for k in ('ra','dec','raErr','decErr')) and
            0 <= m['ra'] < 360 and abs(m['dec']) < 85 and
            0 < m['raErr']*3600 <= .5 and 0 < m['decErr']*3600 <= .5)


def fit_line(t, xy, error):
    t = np.asarray(t); t0 = float(np.mean(t)); dt = t-t0
    A = np.column_stack([np.ones(len(t)),dt])
    coef, _, rank, _ = np.linalg.lstsq(A/error[:,None], xy/error[:,None], rcond=None)
    if rank < 2:
        raise ValueError('Degenerate time baseline')
    pred = A @ coef
    chi2 = float(np.sum(((xy-pred)/error[:,None])**2))
    return t0, coef, chi2/max(1,2*len(t)-4), pred


def independent(mask, distances, rows):
    chosen = {}
    for i in np.flatnonzero(mask):
        key = rows[i]['visit'] or rows[i]['midpointMjdTai']
        if key not in chosen or distances[i] < distances[chosen[key]]:
            chosen[key] = i
    return np.array(sorted(chosen.values()), dtype=int)


def link_band(rows, field, args):
    diagnostics = dict(field=field['label'], band=rows[0]['band'] if rows else '',
                       input_points=len(rows), point_limit_hit=False, seed_limit_hit=False,
                       tested_pairs=0, trial_radii_au=args.radii)
    if len(rows) < 6:
        return [], diagnostics
    latest = max(r['midpointMjdTai'] for r in rows)
    rows = sorted([r for r in rows if r['midpointMjdTai'] >= latest-90], key=lambda r:r['midpointMjdTai'])
    if len(rows) > args.points:
        diagnostics['point_limit_hit'] = True
        rows = rows[-args.points:]
    diagnostics['used_points'] = len(rows)
    if len(rows) < 6:
        return [], diagnostics
    t = np.array([r['midpointMjdTai'] for r in rows])
    nights = np.floor(Time(t, format='mjd', scale='tai').utc.mjd-.5).astype(int)
    if len(set(nights)) < 4 or np.ptp(t) < 7:
        return [], diagnostics
    b = basis(field['ra'],field['dec'])
    n = vectors([r['ra'] for r in rows],[r['dec'] for r in rows])
    original = project(n,b)
    earth = earth_positions(t)
    dec = np.radians([r['dec'] for r in rows])
    error = np.hypot(.20, np.maximum(np.array([r['raErr'] for r in rows])*np.cos(dec),
                                   np.array([r['decErr'] for r in rows]))*3600)
    results = []
    for radius in args.radii:
        xy, delta = deparallax(n,earth,radius,b)
        vmax = 1.2 * math.sqrt(2)*.01720209895/radius**1.5*ARCSEC
        tested = 0; signatures = set()
        for i in range(len(rows)-1):
            dt = t-t[i]
            possible = (dt >= 1) & (dt <= 30) & (nights != nights[i])
            displacement = np.linalg.norm(xy-xy[i],axis=1)
            possible &= displacement <= vmax*np.maximum(dt,0)+2*args.tolerance
            for j in np.flatnonzero(possible):
                if tested >= args.seeds:
                    diagnostics['seed_limit_hit'] = True
                    break
                tested += 1
                slope = (xy[j]-xy[i])/dt[j]
                pred = xy[i]+dt[:,None]*slope
                dist = np.linalg.norm(xy-pred,axis=1)
                idx = independent(dist <= args.tolerance,dist,rows)
                for _ in range(3):
                    if len(idx) < 6:
                        break
                    t0,coef,chi2,_ = fit_line(t[idx],xy[idx],error[idx])
                    pred = coef[0]+(t-t0)[:,None]*coef[1]
                    dist = np.linalg.norm(xy-pred,axis=1)
                    idx = independent(dist <= args.tolerance,dist,rows)
                if len(idx)<6 or len(set(nights[idx]))<4 or np.ptp(t[idx])<7:
                    continue
                signature = tuple(rows[k]['sid'] for k in idx)
                if signature in signatures:
                    continue
                signatures.add(signature)
                t0,coef,chi2,pred = fit_line(t[idx],xy[idx],error[idx])
                speed = float(np.linalg.norm(coef[1]))
                if chi2 > 4 or speed > vmax:
                    continue
                # Stationary-sky comparison uses original observed coordinates.
                weights = 1/error[idx]**2
                fixed = np.average(original[idx],axis=0,weights=weights)
                static_chi = float(np.sum(((original[idx]-fixed)/error[idx,None])**2))
                if static_chi-chi2*(2*len(idx)-4)<30 or np.ptp(original[idx],axis=0).max()<1:
                    continue
                # Leave-one-night-out consistency. This is not independent confirmation.
                max_heldout = 0
                for night in set(nights[idx]):
                    train = idx[nights[idx]!=night]; test = idx[nights[idx]==night]
                    if len(train)<4 or np.ptp(t[train])<1:
                        max_heldout = math.inf;break
                    tc,cc,_,_ = fit_line(t[train],xy[train],error[train])
                    residue = np.linalg.norm(xy[test]-(cc[0]+(t[test]-tc)[:,None]*cc[1]),axis=1)
                    max_heldout = max(max_heldout,float(residue.max()))
                if max_heldout > args.tolerance*1.5:
                    continue
                selected = [rows[k] for k in idx]
                matches = {k:v for r in selected for k,v in r['matches'].items()
                           if k in ('f:xm_gaiadr3_DR3Name','f:xm_tns_fullname','f:xm_simbad_otype')}
                results.append(dict(field=field['label'], band=rows[0]['band'],
                    source_ids=list(signature),object_ids=sorted({r['oid'] for r in selected if r['oid']}),
                    trial_radius_au=radius,trial_geocentric_distance_au=float(np.median(delta[idx])),
                    trial_angular_rate_arcsec_day=round(speed,5),bound_rate_arcsec_day=round(vmax,5),
                    independent_visits=len(idx),night_bins=len(set(nights[idx])),
                    span_days=round(float(np.ptp(t[idx])),3),reduced_chi2=round(chi2,4),
                    max_heldout_residual_arcsec=round(max_heldout,4),catalog_metadata=matches,
                    latest_mjd_tai=float(t[idx].max()),rows=selected))
            if tested >= args.seeds:
                break
        diagnostics['tested_pairs'] += tested
    return results,diagnostics


def size_scenario(track):
    if track['band'] != 'r':
        return {'status':'Not computed: requires r-band science-image flux, not difference flux.'}
    measurements = [r['scienceFlux'] for r in track['rows'] if r.get('science_usable',False) and r['scienceFlux'] is not None
                    and r['scienceFluxErr'] is not None and r['scienceFluxErr']>0
                    and r['scienceFlux']/r['scienceFluxErr']>=5]
    if len(measurements)<3:
        return {'status':'Not computed: fewer than three positive r-band science-flux measurements at S/N>=5.'}
    magnitude = 31.4-2.5*math.log10(float(np.median(measurements)))
    r = track['trial_radius_au']; delta = track['trial_geocentric_distance_au']
    # SDSS-r AB apparent solar magnitude proxy, Willmer 2018. Rubin color terms omitted.
    scale = 2*AU_KM*r*delta*10**(-.2*(magnitude-(-26.93)))
    return dict(status='Conditional reflected-light scenario; not a measured size.',
                science_r_ab=round(magnitude,3),trial_radius_au=r,
                diameter_km_if_albedo_060=round(scale/math.sqrt(.60)),
                diameter_km_if_albedo_004=round(scale/math.sqrt(.04)),
                allows_earth_diameter=scale/math.sqrt(.04)>=12742,
                assumptions='All science flux from one unblended body; zero phase; SDSS-r solar proxy; albedo 0.04–0.60. No mass inferred.')


def merge_tracks(tracks):
    # Collapse radius-grid/field duplicates; do not present them as separate objects.
    merged = []
    for t in sorted(tracks,key=lambda x:(-x['independent_visits'],x['reduced_chi2'])):
        ids = set(t['source_ids'])
        old = next((m for m in merged if len(ids & set(m['source_ids']))/min(len(ids),len(m['source_ids']))>=.8),None)
        hypothesis = {k:v for k,v in t.items() if k not in ('rows','source_ids','object_ids','catalog_metadata')}
        if old:
            old['compatible_trials'].append(hypothesis)
        else:
            t['compatible_trials'] = [hypothesis]
            merged.append(t)
    for t in merged:
        t['size_scenario'] = size_scenario(t)
        t['size_scenarios'] = [size_scenario(dict(t,trial_radius_au=h['trial_radius_au'],
             trial_geocentric_distance_au=h['trial_geocentric_distance_au']))
             for h in t['compatible_trials']]
        t['deep_trial_compatible'] = any(h['trial_radius_au']>=200 for h in t['compatible_trials'])
        t['planet_scale_scenario_compatible'] = any(
            s.get('allows_earth_diameter',False) and s.get('trial_radius_au',0)>=200
            for s in t['size_scenarios'])
        t['classification'] = 'LINKAGE PROPOSAL — UNVERIFIED'
    return sorted(merged,key=lambda t:(-int(t['deep_trial_compatible']),
                  -int(t['planet_scale_scenario_compatible']),-t['night_bins'],
                  -t['independent_visits'],t['reduced_chi2']))


def all_measurements(db):
    return [json.loads(r[0]) for r in db.execute('SELECT normalized FROM rw_measurements')]


def setup_fields(db,args,collector):
    if args.fields:
        data = json.loads(args.fields.read_text())
        if not isinstance(data,list) or not 1<=len(data)<=20:
            raise ValueError('Fields JSON must be a list of 1–20 sky patches')
        fields = []
        for f in data:
            label = str(f['label']);ra=float(f['ra']);dec=float(f['dec']);radius=float(f['radius_arcsec'])
            if not label or len(label)>100 or not 0<=ra<360 or not -80<=dec<=30 or not 30<=radius<=1800:
                raise ValueError('Invalid field: require RA0..360, Dec-80..30, radius30..1800 arcsec')
            fields.append((label,ra,dec,radius,0,'User-selected patch; no inferred survey completeness.'))
        with db:
            old={f['label']:dict(f) for f in db.execute('SELECT * FROM dw_fields')}
            names={f[0] for f in fields}
            for label in set(old)-names:
                db.execute('DELETE FROM dw_fields WHERE label=?',(label,))
                db.execute('DELETE FROM dw_members WHERE label=?',(label,))
            for f in fields:
                prior=old.get(f[0])
                if prior and (prior['ra'],prior['dec'],prior['radius'])==f[1:4]:
                    continue
                db.execute('DELETE FROM dw_members WHERE label=?',(f[0],))
                db.execute('INSERT OR REPLACE INTO dw_fields VALUES (?,?,?,?,?,?)',f)
        return
    if db.execute('SELECT count(*) FROM dw_fields').fetchone()[0]:
        return
    if args.report_only:
        return
    # This bootstrap chooses actual observed patches; it is NOT a planet selection.
    if not collector.fetch('bootstrap:hostless_candidate','tags',tag='hostless_candidate',n=12,**{'output-format':'json'}):
        raise RuntimeError('Could not bootstrap field locations; retry or supply --fields')
    rows = [m for m in all_measurements(db) if m['ra'] is not None and m['dec'] is not None and -80<=m['dec']<=30]
    fields = []
    for m in rows:
        n = vectors([m['ra']],[m['dec']])[0]
        if all(np.linalg.norm(n-vectors([f[1]],[f[2]])[0])>math.radians(1) for f in fields):
            fields.append((f'pilot-{len(fields)+1}',m['ra'],m['dec'],600,0,
                           'Automatic patch around a public hostless-alert position; NOT a Planet Nine predicted region.'))
        if len(fields)==3:break
    if not fields:
        raise RuntimeError('No usable field locations returned')
    with db:
        db.executemany('INSERT INTO dw_fields VALUES (?,?,?,?,?,?)',fields)
    (args.data_dir/'fields.auto.json').write_text(json.dumps([
        dict(label=f[0],ra=f[1],dec=f[2],radius_arcsec=f[3],description=f[5]) for f in fields],indent=2))
    core.log('Created three small pilot fields around known alert locations, not predicted planet coordinates.')


def collect(db,args):
    collector=core.Collector(db)
    setup_fields(db,args,collector)
    fields=db.execute('SELECT * FROM dw_fields ORDER BY attempted,label LIMIT ?', (args.fields_per_cycle,)).fetchall()
    for f in fields:
        selection='field:'+f['label']
        ok=collector.fetch(selection,'conesearch',ra=f['ra'],dec=f['dec'],radius=f['radius'],
                           n=args.sample,kind='across',**{'output-format':'json'})
        with db:
            db.execute('UPDATE dw_fields SET attempted=? WHERE label=?',(time.time(),f['label']))
            db.execute('''INSERT OR IGNORE INTO dw_members SELECT ?,oid FROM rw_selection WHERE tag=?''',
                       (f['label'],selection))
        row=db.execute('SELECT returned_count,error FROM fetches WHERE selection=? ORDER BY id DESC LIMIT 1',(selection,)).fetchone()
        if ok and row['returned_count']>=args.sample:
            core.log(f'  COVERAGE WARNING: requested n={args.sample}, received {row["returned_count"]}; server row-limit behavior and completeness UNVERIFIED.')
        record(db,'cone',dict(field=f['label'],success=ok,returned=row['returned_count'],
                             requested_n=args.sample,requested_limit_reached=bool(ok and row['returned_count']>=args.sample),
                             note='Latest alert per indexed object; completeness not established.'))
    todo=db.execute('''SELECT DISTINCT m.oid,coalesce(h.attempted,0) attempted
        FROM dw_members m LEFT JOIN rw_history h ON h.oid=m.oid
        WHERE coalesce(h.attempted,0)<? ORDER BY attempted,m.oid LIMIT ?''',
        (time.time()-86400,args.histories)).fetchall()
    for r in todo:
        oid=r['oid'];ok=collector.fetch('history:'+oid,'sources',diaObjectId=oid,**{'output-format':'json'})
        with db:db.execute('INSERT OR REPLACE INTO rw_history VALUES (?,?,?)',(oid,time.time(),'ok' if ok else 'error'))
    return collector.failures


def analyze(db,args):
    records=all_measurements(db);usable=[r for r in records if eligible(r)]
    results=[];stats=[]
    for f in db.execute('SELECT * FROM dw_fields'):
        center=vectors([f['ra']],[f['dec']])[0]
        # Histories can move outside the discovery cone; include a modest 0.5-degree buffer.
        radius=math.radians(f['radius']/3600+.5)
        local=[r for r in usable if np.linalg.norm(vectors([r['ra']],[r['dec']])[0]-center)<=2*math.sin(radius/2)]
        for band in 'ugrizy':
            group=[r for r in local if r['band']==band]
            found,diagnostic=link_band(group,f,args)
            results.extend(found);stats.append(diagnostic)
    merged=merge_tracks(results)
    record(db,'analysis',dict(total_records=len(records),eligible=len(usable),proposals=len(merged),budgets=stats))
    core.log(f'DISTANT WATCH: {len(records)} stored | {len(usable)} eligible | {len(merged)} unverified linkage proposals')
    return merged,stats


def parse_skybot(raw,ra,dec):
    root=ET.fromstring(raw)
    tag=lambda x:x.tag.rsplit('}',1)[-1]
    messages=[(x.attrib.get('value',''),x.text or '') for x in root.iter()
              if tag(x)=='INFO' and x.attrib.get('name')=='QUERY_STATUS']
    if any('No solar system object was found' in msg for _,msg in messages):
        return dict(status='no_catalog_match',objects=[])
    if not messages or any(val.upper()=='ERROR' for val,_ in messages):
        return dict(status='unchecked',error=str(messages),objects=[])
    fields=[x.attrib.get('name',x.attrib.get('ID','')) for x in root.iter() if tag(x)=='FIELD']
    objects=[]
    for tr in root.iter():
        if tag(tr)=='TR':
            values=[(x.text or '').strip() for x in tr if tag(x)=='TD']
            objects.append(dict(zip(fields,values)))
    return dict(status='catalog_objects_near_position' if objects else 'no_catalog_match',objects=objects)


def skybot(db,track):
    rows=sorted(track['rows'],key=lambda r:r['midpointMjdTai'])
    checks=[]
    for row in [rows[0],rows[len(rows)//2],rows[-1]]:
        params={'-ep':core.utc(row['midpointMjdTai']).rstrip('Z'),'-ra':row['ra'],'-dec':row['dec'],
                '-rs':10,'-mime':'votable','-output':'all','-observer':'X05','-filter':0,'-from':'RubinDistantWatch'}
        url='https://ssp.imcce.fr/webservices/skybot/api/conesearch.php?'+urlencode(params)
        cached=db.execute('SELECT checked,result FROM dw_skybot WHERE url=?',(url,)).fetchone()
        if cached and time.time()-cached['checked']<7*86400:
            result=json.loads(cached['result'])
        else:
            raw=b''
            try:
                req=Request(url,headers={'User-Agent':'RubinDistantWatch/'+VERSION})
                with urlopen(req,timeout=25) as response:raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError('SkyBoT response exceeds 2 MB')
                result=parse_skybot(raw,row['ra'],row['dec'])
            except Exception as exc:
                result=dict(status='unchecked',error=f'{type(exc).__name__}: {exc}',objects=[])
            with db:db.execute('INSERT OR REPLACE INTO dw_skybot VALUES (?,?,?,?)',
                               (url,time.time(),core.canonical(result),raw))
            time.sleep(2)
        checks.append(dict(source_id=row['sid'],epoch_utc=core.utc(row['midpointMjdTai']),url=url,result=result))
    statuses=[c['result']['status'] for c in checks]
    status=('unchecked' if 'unchecked' in statuses else
            'known_object_proximity_needs_review' if 'catalog_objects_near_position' in statuses else
            'no_match_in_three_10_arcsec_catalog_queries')
    return dict(status=status,checks=checks,note='Nearby catalog entries are not automated identity matches; no match does not prove novelty.')


def persist(db,tracks):
    old=[dict(r) for r in db.execute('SELECT * FROM dw_tracks')]
    used=set();changed=0
    with db:
        for t in tracks:
            ids=set(t['source_ids'])
            match=None
            for r in old:
                if r['id'] in used:continue
                prev=set(json.loads(r['evidence'])['source_ids'])
                if len(ids&prev)>=3 and len(ids&prev)/min(len(ids),len(prev))>=.8:
                    match=r;break
            key=match['id'] if match else hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()[:16]
            used.add(key);t['track_id']=key
            encoded=core.canonical(t);fingerprint=hashlib.sha256(encoded.encode()).hexdigest()
            if match and match['fingerprint']==fingerprint and match['status']=='review':continue
            stamp=core.now()
            db.execute('INSERT OR REPLACE INTO dw_tracks VALUES (?,?,?,?,?,?)',
                       (key,'review',match['first_seen'] if match else stamp,stamp,fingerprint,encoded))
            db.execute('INSERT INTO dw_audit(utc,track,status,evidence) VALUES (?,?,?,?)',(stamp,key,'review',encoded));changed+=1
        for r in old:
            if r['id'] not in used and r['status']=='review':
                db.execute("UPDATE dw_tracks SET status='not_reproduced',updated=? WHERE id=?",(core.now(),r['id']))
                db.execute('INSERT INTO dw_audit(utc,track,status,evidence) VALUES (?,?,?,?)',
                           (core.now(),r['id'],'not_reproduced',r['evidence']))
    return changed


def plot_track(t):
    rows=t['rows'];b=basis(rows[0]['ra'],rows[0]['dec'])
    n=vectors([r['ra'] for r in rows],[r['dec'] for r in rows]);mjd=np.array([r['midpointMjdTai'] for r in rows])
    xy=project(n,b);corrected,_=deparallax(n,earth_positions(mjd),t['trial_radius_au'],b)
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,pos,title in zip(axes,[xy,corrected],['Observed sky positions','Trial-radius deparallaxed positions']):
        scatter=ax.scatter(pos[:,0]-pos[0,0],pos[:,1]-pos[0,1],c=mjd-mjd.min(),cmap='viridis')
        ax.set(xlabel='East offset (arcsec)',ylabel='North offset (arcsec)',title=title)
        fig.colorbar(scatter,ax=ax,label='Days from first point')
    stream=io.BytesIO();fig.savefig(stream,format='png',dpi=115);plt.close(fig)
    return base64.b64encode(stream.getvalue()).decode()


def report(db,args,tracks,stats):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=args.data_dir/'reports'/stamp;dest.mkdir(parents=True)
    fields=[dict(f) for f in db.execute('SELECT * FROM dw_fields')]
    runs=[dict(r) for r in db.execute('SELECT * FROM dw_runs ORDER BY id DESC LIMIT 40')]
    for r in runs:r['detail']=json.loads(r['detail'])
    latest=db.execute('SELECT max(mjd) FROM rw_measurements').fetchone()[0]
    warnings = WARNINGS
    if core.meta(db, 'dw_avro_import'):
        warnings = [warning for index, warning in enumerate(WARNINGS) if index not in (1, 2)]
        warnings += [
            'The AVRO run uses the current detection from each saved packet. Embedded histories are not ingested.',
            'The saved topic is a sampled stream. Analysis covers only the configured sky patches and does not establish survey completeness.',
        ]
    data=dict(version=VERSION,generated_utc=core.now(),freshness=core.freshness(latest),fields=fields,
              warnings=warnings,analysis_budgets=stats,proposals=tracks,recent_runs=runs,
              fetch_errors=[dict(r) for r in db.execute('SELECT * FROM fetches WHERE error IS NOT NULL ORDER BY id DESC LIMIT 20')])
    (dest/'report.json').write_text(json.dumps(data,indent=2,allow_nan=False))
    with (dest/'observations.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['track','source_id','broker_object_id','UTC','RA_deg','Dec_deg','band','observatory'])
        for t in tracks:
            for r in t['rows']:writer.writerow([t['track_id'],r['sid'],r['oid'],core.utc(r['midpointMjdTai']),r['ra'],r['dec'],r['band'],'X05'])
    esc=lambda s:html.escape(str(s),quote=True)
    sections=[]
    for index,t in enumerate(tracks):
        plot='<img alt="Observed and trial-deparallaxed positions" src="data:image/png;base64,'+plot_track(t)+'">' if index<6 else ''
        links=' · '.join(f'<a target="_blank" rel="noopener noreferrer" href="https://lsst.fink-portal.org/{oid}">{oid}</a>' for oid in t['object_ids'])
        evidence={k:v for k,v in t.items() if k!='rows'}
        sections.append(f'<article><h2>Proposal {esc(t["track_id"])}</h2><p class="warn">{esc(t["classification"])}</p>'
            f'<p>{t["independent_visits"]} visits · {t["night_bins"]} night bins · {t["span_days"]} days · filter {esc(t["band"])}</p>'
            f'<p>Compatible trial radii: {esc(sorted({h["trial_radius_au"] for h in t["compatible_trials"]}))} AU. These are tested assumptions, not distance measurements.</p>'
            f'<p>SkyBoT: {esc(t.get("skybot",{}).get("status","unchecked"))}</p><p>Fink image review: {links}</p>{plot}'
            f'<details><summary>Evidence and conditional size scenario</summary><pre>{esc(json.dumps(evidence,indent=2))}</pre></details></article>')
    fieldhtml=''.join(f'<tr><td>{esc(f["label"])}</td><td>{f["ra"]:.5f}</td><td>{f["dec"]:.5f}</td><td>{f["radius"]}</td></tr>' for f in fields)
    budgethit=any(s.get('point_limit_hit') or s.get('seed_limit_hit') for s in stats)
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Rubin Distant Watch</title><style>body{{background:#08151e;color:#e8f0f4;font:16px/1.65 system-ui;margin:0}}main{{max-width:1060px;margin:auto;padding:32px 22px}}article,section{{background:#122734;border:1px solid #294557;border-radius:12px;padding:22px;margin:24px 0}}h1{{font-size:38px;line-height:1.2}}h2{{line-height:1.3}}a{{color:#79e4cf}}.warn{{color:#ffd08a}}img{{max-width:100%;border-radius:6px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}}li{{margin:12px 0}}td,th{{text-align:left;padding:8px;border-bottom:1px solid #294557}}table{{width:100%}}</style>
    <main><p>RUBIN / FINK · DISTANT-BODY PILOT</p><h1>Follow the motion.<br>Keep the uncertainty.</h1><p>Generated {esc(data['generated_utc'])} · v{VERSION}</p>
    <p class="warn">{esc(data['freshness'])}</p><section><h2>{len(tracks)} linkage proposals for review</h2><p>No confirmed discoveries. Zero proposals does not exclude any planet.</p><p>Analysis budget reached: {budgethit}. Query limits and all exclusions are retained in report.json.</p></section>
    <section><h2>Where we actually looked</h2><table><tr><th>Field</th><th>RA</th><th>Dec</th><th>Radius, arcsec</th></tr>{fieldhtml}</table><p>Field origins, history coverage, and capped queries are recorded in the JSON report.</p></section>
    <section><h2>What the evidence can support</h2><ul>{''.join('<li>'+esc(w)+'</li>' for w in warnings)}</ul></section>
    {''.join(sections) or '<section><p>No stored detections currently satisfy the linkage cuts. The model and tests still run; synthetic test objects are never inserted into this observing database.</p></section>'}
    <section><h2>Downloads</h2><p><a href="report.json">Full evidence and coverage JSON</a> · <a href="observations.csv">Proposed-track observations CSV</a></p></section></main></html>'''
    (dest/'index.html').write_text(doc)
    (args.data_dir/'reports'/'latest.html').write_text(f'<!doctype html><meta charset="utf-8"><a href="{stamp}/index.html">Latest distant-body report</a>')
    with db:core.meta(db,'dw_last_report',time.time())
    core.log('REPORT: '+str(dest/'index.html'))


def cycle(db,args):
    previous=core.num(core.meta(db,'dw_last_cycle'))
    if previous and time.time()-previous>args.interval*2:
        record(db,'gap',dict(hours=(time.time()-previous)/3600,note='Observations may have been missed.'))
    failures=0 if args.report_only else collect(db,args)
    tracks,stats=analyze(db,args)
    for i,t in enumerate(tracks):
        if not args.report_only and i<args.skybot:
            t['skybot']=skybot(db,t)
        else:
            # Preserve existing checks only when the exact set of detections matches.
            old=db.execute('SELECT evidence FROM dw_tracks').fetchall()
            matched=next((json.loads(r[0]) for r in old if set(json.loads(r[0])['source_ids'])==set(t['source_ids'])),None)
            t['skybot']=matched.get('skybot',{'status':'unchecked'}) if matched else {'status':'unchecked'}
    changes=persist(db,tracks);core.log(f'Evidence updates: {changes}')
    last=core.num(core.meta(db,'dw_last_report'))
    if args.report or args.report_only or last is None or time.time()-last>=86400:
        report(db,args,tracks,stats)
    if not args.report_only:
        with db:core.meta(db,'dw_last_cycle',time.time())
    return failures


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,default=Path.home()/'rubin-distant-watch')
    p.add_argument('--fields',type=Path,help='JSON list: label,ra,dec,radius_arcsec. Without it, creates 3 small observed pilot fields.')
    p.add_argument('--avro', type=Path, nargs='+', help='Import LSST Avro files or directories, then generate one local report.')
    p.add_argument('--sample',type=int,default=100)
    p.add_argument('--histories',type=int,default=6)
    p.add_argument('--fields-per-cycle',type=int,default=2)
    p.add_argument('--interval',type=int,default=1800)
    p.add_argument('--radii',type=float,nargs='+',default=RADII)
    p.add_argument('--points',type=int,default=1000,help='Maximum eligible points per field/filter over its latest 90 observed days.')
    p.add_argument('--seeds',type=int,default=1500,help='Maximum tested seed pairs per field/filter/trial radius.')
    p.add_argument('--tolerance',type=float,default=.8,help='Link residual tolerance, arcsec.')
    p.add_argument('--skybot',type=int,default=2,help='Top proposals to check at three epochs per cycle; 0 disables.')
    p.add_argument('--once',action='store_true')
    p.add_argument('--report',action='store_true')
    p.add_argument('--report-only',action='store_true')
    args=p.parse_args()
    if args.avro and not args.fields:
        p.error('--avro requires a --fields JSON file')
    if not (1<=args.sample<=1000 and 0<=args.histories<=20 and 1<=args.fields_per_cycle<=10
            and args.interval>=900 and 6<=args.points<=3000 and 10<=args.seeds<=10000
            and .3<=args.tolerance<=2 and 0<=args.skybot<=5
            and 1<=len(args.radii)<=30 and all(math.isfinite(r) and 50<=r<=5000 for r in args.radii)):
        p.error('Invalid bounds; see README. Keep interval>=900 and trial radii 50–5000 AU.')
    args.data_dir=args.data_dir.expanduser().resolve();args.data_dir.mkdir(parents=True,exist_ok=True)
    with (args.data_dir/'distant-watch.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another distant-watch process is using this directory.')
        db=core.connect(args.data_dir/'rubin-distant.sqlite3');schema(db)
        try:
            core.log(f'RUBIN DISTANT WATCH {VERSION} | {args.data_dir}')
            core.log('Selected sky patches; unknown-body hypotheses only. No inferred planet masses.')
            if args.avro:
                from live_avro import ingest

                setup_fields(db, args, None)
                results = ingest(db, args.avro)
                record(db, 'avro_ingest', results)
                with db:
                    core.meta(db, 'dw_avro_import', '1')
                core.log(f"AVRO IMPORT: {results['packets']} packets | "
                         f"{results['known_sso']} known Solar System | "
                         f"{results['unassociated']} without a Solar System match | "
                         f"{results['inserted']} inserted | {results['updated']} updated | "
                         f"{results['unchanged']} unchanged")
                for error in results['errors']:
                    core.log(f'AVRO ERROR: {error}')
                args.report_only = True
                cycle(db, args)
                return 2 if results['errors'] or not results['packets'] else 0
            if args.report_only:return cycle(db,args)
            while True:
                try:failures=cycle(db,args)
                except Exception as exc:
                    db.rollback();core.log(f'CYCLE ERROR: {type(exc).__name__}: {exc}');failures=1
                    record(db,'error',dict(error=f'{type(exc).__name__}: {exc}'))
                if args.once:return 2 if failures else 0
                delay=min(7200,args.interval*(2 if failures else 1));core.log(f'Next cycle in {delay}s; Ctrl+C stops.')
                deadline=time.monotonic()+delay
                while time.monotonic()<deadline:time.sleep(min(1,max(0,deadline-time.monotonic())))
        except KeyboardInterrupt:
            core.log('Stopped; committed evidence retained.');return 0
        finally:db.close()


if __name__=='__main__':sys.exit(main())

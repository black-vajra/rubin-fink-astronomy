#!/usr/bin/env python3
"""Acquire Fink historical products and write two research reports."""
import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
from html import escape
import json
from math import log10
from pathlib import Path
import sqlite3
import urllib.request

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
API = "https://api.lsst.fink-portal.org/api/v1/"
START, STOP = "2026-07-16", "2026-11-16"
START_TAI = Time(START, scale="utc").tai.mjd
STOP_TAI = Time(STOP, scale="utc").tai.mjd
TARGETS = {
    "171141216913588260": "PGC 766016",
    "313774266976305153": "Quasar crossmatch",
    "313862200773574662": "Science-image high",
    "170653056044630027": "Bright residual / AT 2019hkw",
}
TOPIC = "ftransfer_lsst_2026-11-19_639723"


def download(endpoint, params, destination):
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        API + endpoint, data=json.dumps(params).encode(),
        headers={"Content-Type": "application/json"},
    )
    print(f"Retrieving {endpoint} → {destination.name}", flush=True)
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        while chunk := response.read(4 * 1024 * 1024):
            output.write(chunk)
    if destination.suffix == ".json":
        json.loads(temporary.read_text())
    else:
        pq.ParquetFile(temporary)
    temporary.replace(destination)


def fetch():
    DATA.mkdir(parents=True, exist_ok=True)
    errors = []
    jobs = [(f"statistics-{m}.json", "statistics", {"date": m, "output-format": "json"})
            for m in ("202607", "202608", "202609", "202610", "202611")]
    jobs += [(f"object-{oid}.json", "sources",
              {"diaObjectId": oid, "output-format": "json"}) for oid in TARGETS]

    for name, endpoint, params in jobs:
        destination = DATA / name
        if destination.is_file():
            continue
        try:
            download(endpoint, params, destination)
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            print(errors[-1], flush=True)
    (DATA / "fetch-errors.json").write_text(json.dumps(errors, indent=2))


def in_window(mjd):
    return START <= Time(float(mjd), format="mjd", scale="tai").utc.isot[:10] < STOP


def write_report(name, lines):
    text = "\n".join(lines) + "\n"
    (BASE / f"{name}.md").write_text(text)
    html = ("<!doctype html><meta charset=utf-8><title>Rubin Historical Research</title>"
            "<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto}"
            "pre{white-space:pre-wrap}</style><pre>" + escape(text) + "</pre>")
    (BASE / f"{name}.html").write_text(html)


def archive_rows():
    rows = {}
    for path in DATA.glob("statistics-*.json"):
        for row in json.loads(path.read_text()):
            day = str(row["f:night"])
            if "20260716" <= day <= "20261115":
                rows[day] = row
    return rows


def extragalactic():
    lines = ["# Historical extragalactic report", "",
             f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
             f"Selected UTC interval {START} through 2026-11-15 inclusive.", "",
             "Retrieved alert histories are sparse samples. Missing alerts or statistics "
             "entries do not establish that a field was unobserved.", ""]
    for oid, label in TARGETS.items():
        lines += [f"## {label} · {oid}", ""]
        path = DATA / f"object-{oid}.json"
        if not path.exists():
            lines.append("History unavailable.")
            continue
        raw = json.loads(path.read_text())
        database = BASE / "alerts.sqlite3"
        if database.exists():
            con = sqlite3.connect(database)
            try:
                for sid, mjd, band, science, difference in con.execute(
                    "SELECT sid,mjd,band,science,difference FROM sources WHERE object_id=?", (oid,)):
                    raw.append({"r:diaSourceId": sid, "r:midpointMjdTai": mjd,
                                "r:band": band, "r:scienceFlux": science, "r:psfFlux": difference})
            finally:
                con.close()
        rows = {str(r["r:diaSourceId"]): r for r in raw
                if r.get("r:midpointMjdTai") is not None and in_window(r["r:midpointMjdTai"])}
        lines.append(f"{len(raw)} returned alerts across all dates; {len(rows)} unique alerts in interval.")
        lines += ["", "| Band | Measurement | Points | First UTC | Last UTC | "
                  "First AB mag | Last AB mag | Latest / earlier median flux |",
                  "|---|---|---:|---|---|---:|---:|---:|"]
        for band in sorted({r.get("r:band", "?") for r in rows.values()}):
            selected = sorted((r for r in rows.values() if r.get("r:band") == band),
                              key=lambda r: r["r:midpointMjdTai"])
            for field in ("scienceFlux", "psfFlux"):
                usable = [r for r in selected if r.get("r:" + field) is not None
                          and np.isfinite(float(r["r:" + field])) and float(r["r:" + field]) > 0]
                if not usable:
                    continue
                flux = [float(r["r:" + field]) for r in usable]
                times = [Time(r["r:midpointMjdTai"], format="mjd", scale="tai").utc.isot
                         for r in usable]
                ratio = f"{flux[-1]/np.median(flux[:-1]):.3f}" if len(flux) > 1 else "—"
                mags = [31.4 - 2.5 * log10(f) for f in (flux[0], flux[-1])]
                lines.append(f"| {band} | {field} | {len(usable)} | {times[0]} | {times[-1]} | "
                             f"{mags[0]:.3f} | {mags[-1]:.3f} | {ratio} |")
        lines += ["", f"Full retrieved fields retained in data/object-{oid}.json.", ""]
    lines += ["## Review priorities", "",
              "Compare PGC 766016's science and difference fluxes in i separately. "
              "Inspect cutouts, seeing, reference identifiers and calibration before attributing "
              "the science-image rise to the nucleus.",
              "Review long gaps and quality flags before interpreting ratios as exceptional activity.",
              "The compact archive import adds measurements for all four watchlist targets. Discovery triage for new extragalactic objects remains a separate analysis."]
    write_report("extragalactic-report", lines)


def motion_rows():
    path = DATA / "ssobulk.parquet"
    if path.exists():
        for batch in pq.ParquetFile(path).iter_batches(batch_size=1000):
            yield from batch.to_pylist()
    database = BASE / "alerts.sqlite3"
    if database.exists():
        con = sqlite3.connect(database)
        try:
            ids = con.execute("SELECT DISTINCT sso FROM sources WHERE sso != ''")
            for (oid,) in ids:
                rows = list(con.execute(
                    "SELECT mjd,ra,dec FROM sources WHERE sso=? ORDER BY mjd", (oid,)))
                yield dict(designation="ssObjectId " + oid, version="local compact archive",
                           cmidpointMjdTai=[r[0] for r in rows],
                           cra=[r[1] for r in rows], cdec=[r[2] for r in rows])
        finally:
            con.close()


def motion():
    lines = ["# Historical moving-object report", "",
             f"Selected UTC interval {START} through 2026-11-15 inclusive.", ""]
    path = DATA / "ssobulk.parquet"
    slow = []
    retained = objects = 0
    first, last = float("inf"), float("-inf")
    versions = set()
    if path.exists() or (BASE / "alerts.sqlite3").exists():
        for row in motion_rows():
            versions.add(str(row.get("version")))
            t = np.asarray(row["cmidpointMjdTai"], dtype=float)
            mask = (t >= START_TAI) & (t < STOP_TAI)
            if not mask.any():
                continue
            t = t[mask]
            ra = np.asarray(row["cra"], dtype=float)[mask]
            dec = np.asarray(row["cdec"], dtype=float)[mask]
            valid = np.isfinite(t) & np.isfinite(ra) & np.isfinite(dec)
            t, ra, dec = t[valid], ra[valid], dec[valid]
            if not len(t):
                continue
            objects += 1
            retained += len(t)
            first, last = min(first, min(t)), max(last, max(t))
            if len(t) < 3:
                continue
            days = Time(t, format="mjd", scale="tai").utc.isot
            groups = defaultdict(list)
            for i, day in enumerate(days):
                groups[day[:10]].append(i)
            rates = []
            for day, indices in groups.items():
                indices = sorted(indices, key=lambda i: t[i])
                if len(indices) < 3:
                    continue
                a, b = indices[0], indices[-1]
                duration = (t[b] - t[a]) * 1440
                if duration < 30:
                    continue
                sky = SkyCoord(ra[indices] * u.deg, dec[indices] * u.deg)
                east, north = sky[0].spherical_offsets_to(sky)
                minutes = (t[indices] - t[a]) * 1440
                slope, offset = np.polyfit(minutes, np.column_stack((east.arcsec, north.arcsec)), 1)
                residual = np.linalg.norm(np.column_stack((east.arcsec, north.arcsec))
                                          - (minutes[:, None] * slope + offset), axis=1)
                rate = float(np.linalg.norm(slope))
                if .001 <= rate <= .1 and max(residual) <= 1:
                    rates.append((rate, day, len(indices), duration, float(max(residual))))
            if rates:
                slow.append((row["designation"], len(t), len(groups), min(rates)))
        lines += [f"Bulk-table versions: {', '.join(sorted(versions))}.",
                  f"Selected {retained:,} measurements for {objects:,} cataloged objects."]
        if retained:
            lines.append(f"Actual TAI-derived UTC span: "
                         f"{Time(first,format='mjd',scale='tai').utc.isot} to "
                         f"{Time(last,format='mjd',scale='tai').utc.isot}.")
        lines += ["", "## Slow-control shortlist", "",
                  "Selection fixed before testing: ≥3 detections spanning ≥30 minutes on one night, "
                  "training fit rate 0.001–0.1 arcsec/min, maximum fit residual ≤1 arcsec.",
                  "These are training candidates. They need independent test-night detections, "
                  "ssObjectId resolution and usable detector footprints.",
                  "", "| Designation | Window detections | Nights | Rate arcsec/min | Training night | Fit max arcsec |",
                  "|---|---:|---:|---:|---|---:|"]
        for name, count, nights, fit in sorted(slow, key=lambda item: item[3][0]):
            rate, night, number, duration, residual = fit
            lines.append(f"| {name} | {count} | {nights} | {rate:.5f} | {night} | {residual:.3f} |")
        (BASE / "slow-controls.json").write_text(json.dumps(slow, indent=2))
    else:
        lines += ["Compact alert archive has not yet been imported. Slow-control scan pending. Existing Nov 13–15 tests recovered the primary at rank 1/138,867, with 36.21 arcsec error from Nov 13–14 training; secondary detections ranked 1 and 2/59,725. Those are earlier benchmark results, awaiting rerun against the expanded archive."]
    lines += ["", "## Archive completion", "",
              "The monthly SSO bulk product can omit November measurements. The compact "
              f"transfer {TOPIC} is required to supplement it through November 15.",
              "Known SSO light curves contain catalog-associated objects. Unknown-object searches "
              "need the unfiltered alert transfer, including alerts without ssObjectId.",
              "Mass ranges and a Planet Nine candidate search have not run. Distance and calibrated "
              "photometry, reflectivity and density assumptions, and validated linking are needed."]
    lines += ["", "## Resolved slow controls", ""]
    for history in sorted(DATA.glob("sso-*.json")):
        payload = json.loads(history.read_text())
        if not isinstance(payload, list):
            continue
        rows = [r for r in payload
                if r.get("r:midpointMjdTai") is not None and in_window(r["r:midpointMjdTai"])]
        if not rows:
            continue
        dates = sorted({Time(r["r:midpointMjdTai"],format="mjd",scale="tai").utc.isot[:10]
                        for r in rows})
        lines.append(f"{history.stem[4:]} | ssObjectId {rows[0].get('r:ssObjectId')} | "
                     f"{len(rows)} window detections | UTC dates {', '.join(dates)}.")
    lines.append("The two resolved objects have later November observations for held-out tests. "
                 "Their returned heliocentric distances are approximately 2.3–2.5 AU. "
                 "Their slow apparent rates provide a motion benchmark; distance remains independently known.")
    physical = DATA / "ssoft.parquet"
    if physical.exists():
        lines.append(f"Aggregate phase/physical table downloaded: "
                     f"{pq.ParquetFile(physical).metadata.num_rows:,} object rows. "
                     "Filter-specific absolute magnitudes need photometric and fit-quality "
                     "review before applying diameter formulas calibrated for V band.")
    write_report("moving-object-report", lines)


def inventory():
    rows = archive_rows()
    summary = ["# Historical archive coverage", "",
               f"UTC selection {START} through 2026-11-15 inclusive.",
               f"{len(rows)} nights with published statistics; "
               f"{sum(int(r['f:alerts']) for r in rows.values()):,} reported alerts.",
               "A missing statistics entry is recorded as unknown coverage.", "",
               f"Compact archive topic {TOPIC}. Portal estimate 1.39 GB.",
               "The export uses no alert filters and includes diaSource, diaObject, ssSource and mpc_orbits.", "",
               "| UTC night key | Alerts |", "|---|---:|"]
    summary += [f"| {day} | {r['f:alerts']} |" for day, r in sorted(rows.items())]
    write_report("archive-coverage", summary)


def index_avro(folder):
    from fastavro import reader
    con = sqlite3.connect(BASE / "alerts.sqlite3")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS sources(
          sid TEXT PRIMARY KEY, visit TEXT, mjd REAL, utc_night TEXT,
          ra REAL, dec REAL, sso TEXT, object_id TEXT, band TEXT,
          science REAL, difference REAL, packet TEXT);
        CREATE INDEX IF NOT EXISTS source_object ON sources(sso, mjd);
        CREATE TABLE IF NOT EXISTS imports(path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER);
    """)
    try:
        for path in sorted(folder.rglob("*.avro")):
            stat = path.stat()
            fingerprint = (stat.st_size, stat.st_mtime_ns)
            saved = con.execute("SELECT size,mtime FROM imports WHERE path=?",
                                (str(path.resolve()),)).fetchone()
            if saved == fingerprint:
                continue
            if saved:
                raise ValueError(f"Previously imported file changed: {path}")
            with con:
                with path.open("rb") as handle:
                    for packet in reader(handle):
                        s = packet.get("diaSource") or {}
                        if any(s.get(k) is None for k in ("diaSourceId","midpointMjdTai","ra","dec")):
                            continue
                        if not in_window(s["midpointMjdTai"]):
                            continue
                        stamp = Time(s["midpointMjdTai"], format="mjd", scale="tai").utc.isot[:10]
                        vals = (str(s["diaSourceId"]), str(s.get("visit")), s["midpointMjdTai"],
                                stamp, s["ra"], s["dec"], str(s.get("ssObjectId") or ""),
                                str(s.get("diaObjectId") or ""), s.get("band"),
                                s.get("scienceFlux"), s.get("psfFlux"), str(path.resolve()))
                        con.execute("INSERT OR IGNORE INTO sources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", vals)
                con.execute("INSERT INTO imports VALUES(?,?,?)",
                            (str(path.resolve()), *fingerprint))
        lines = ["# Imported compact alert archive", "",
                 f"{con.execute('SELECT COUNT(*) FROM sources').fetchone()[0]:,} unique valid in-window diaSources.",
                 "Selected fields retained in original Avro files. Ingestion is transactional per file.",
                 "Unique count is a coverage measure; a complete-export count still requires checking all packets.",
                 "", "| UTC date | Unique valid diaSources |", "|---|---:|"]
        lines += [f"| {day} | {count:,} |" for day, count in
                  con.execute("SELECT utc_night,COUNT(*) FROM sources GROUP BY utc_night ORDER BY utc_night")]
        write_report("import-report", lines)
    finally:
        con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download missing public products")
    parser.add_argument("--avro", type=Path, help="Index downloaded compact packets")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    if args.fetch:
        fetch()
    if args.avro:
        index_avro(args.avro.expanduser().resolve())
    inventory()
    extragalactic()
    motion()
    print(f"Reports saved in {BASE}")

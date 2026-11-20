#!/usr/bin/env python3
"""Read the Pots archive and compare measured motion, empirical fits and JPL ephemerides."""
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import io
import json
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

ROOT = Path.home() / "rubin-historical-2026"
RADIUS = 60.0
CONTROLS = [
    ("2014 WV203", "21164724125905750", ("2026-11-12", "2026-11-15")),
    ("2013 CR7", "21164719493625682", ("2026-11-12",)),
]
CACHE = ROOT / "ephemeris-cache"
OUTPUT = ROOT / "slow-control-recovery.md"
LOG = []


def say(message):
    print(message, flush=True)
    LOG.append(message)


def sky(rows):
    return SkyCoord([r[3] for r in rows] * u.deg, [r[4] for r in rows] * u.deg)


def fit_positions(training, tested, degree):
    origin = sky(training[:1])[0]
    epoch = training[0][2]
    x, y = origin.spherical_offsets_to(sky(training))
    coefficients = np.polyfit(
        np.array([r[2] - epoch for r in training]),
        np.column_stack((x.arcsec, y.arcsec)), degree,
    )
    t = np.array([r[2] - epoch for r in tested])
    xy = np.column_stack([np.polyval(coefficients[:, axis], t) for axis in (0, 1)])
    return origin.spherical_offsets_by(xy[:, 0] * u.arcsec, xy[:, 1] * u.arcsec)


def score(label, rows, predicted, target):
    errors = predicted.separation(sky(rows)).arcsec
    ranked = np.argsort(errors, kind="stable")
    inside = errors <= RADIUS
    say(f"{label}: {len(rows):,} test alerts | {np.count_nonzero(inside)} inside {RADIUS:g} arcsec.")
    recovered = 0
    for rank, i in enumerate(ranked, 1):
        if rows[i][5] == target:
            recovered += int(inside[i])
            say(f"  Control {rows[i][0]} | visit {rows[i][1]} | rank {rank:,} | "
                f"miss {errors[i]:.3f} arcsec | inside radius {bool(inside[i])}")
    say(f"  Recovered labeled detections inside radius: {recovered}.")
    say("  Coverage-normalized false-match rate remains unavailable without detector footprints.")


def horizons(name, epochs):
    """Get independent astrometric ICRF predictions from Rubin's topocenter."""
    parameters = {
        "format": "json", "COMMAND": f"'DES={name};'", "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'X05@399'", "TLIST": "'" + "\n".join(f"{jd:.10f}" for jd in epochs) + "'",
        "QUANTITIES": "'1,3'", "ANG_FORMAT": "'DEG'", "CSV_FORMAT": "'YES'",
        "EXTRA_PREC": "'YES'", "REF_SYSTEM": "'ICRF'", "TIME_DIGITS": "'FRACSEC'",
        "TIME_TYPE": "'UT'",
    }
    query = urllib.parse.urlencode(parameters)
    cache = CACHE / (hashlib.sha256(query.encode()).hexdigest() + ".json")
    if cache.exists():
        payload = json.loads(cache.read_text())
    else:
        with urllib.request.urlopen(
            "https://ssd.jpl.nasa.gov/api/horizons.api?" + query, timeout=45
        ) as response:
            payload = json.load(response)
        if "error" in payload:
            raise ValueError(payload["error"])
        result = payload.get("result", "")
        if "$$SOE" not in result or "$$EOE" not in result:
            raise ValueError("Horizons returned no uniquely identified ephemeris")
        cache.write_text(json.dumps(payload, indent=2))
    if payload.get("error"):
        raise ValueError(payload["error"])
    result = payload["result"]
    body = result.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    data = [r for r in csv.reader(io.StringIO(body)) if r and r[0].strip()]
    if len(data) != len(epochs):
        raise ValueError("Horizons epoch count differs from request")
    parsed = []
    for row in data:
        returned = Time(datetime.strptime(row[0].strip(), "%Y-%b-%d %H:%M:%S.%f"),
                        scale="utc").jd
        parsed.append((returned, *(float(row[i]) for i in (3, 4, 5, 6))))
    parsed = np.array(parsed)
    ordered = []
    for jd in epochs:
        nearest = int(np.argmin(np.abs(parsed[:, 0] - jd)))
        if abs(parsed[nearest, 0] - jd) * 86400 > .02:
            raise ValueError("Horizons returned an unexpected epoch")
        ordered.append(parsed[nearest, 1:])
    return np.array(ordered)


def main():
    if not (ROOT / "alerts.sqlite3").exists():
        raise SystemExit(f"Missing archive database in {ROOT}")
    CACHE.mkdir(exist_ok=True)
    con = sqlite3.connect((ROOT / "alerts.sqlite3").as_uri() + "?mode=ro", uri=True)
    try:
        say("# Slow-control recovery")
        say(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        say(f"Radius fixed before scoring: {RADIUS:g} arcsec.")
        test_cache = {}
        for name, target, days in CONTROLS:
            say(f"\n## {name}")
            observed = con.execute(
                "SELECT sid,visit,mjd,ra,dec,sso,utc_night FROM sources "
                "WHERE sso=? ORDER BY mjd", (target,)
            ).fetchall()
            for day in sorted({r[6] for r in observed}):
                rows = [r for r in observed if r[6] == day]
                if len(rows) < 2:
                    say(f"{day}: {len(rows)} detection; nightly rate unavailable.")
                    continue
                minutes = (rows[-1][2] - rows[0][2]) * 1440
                if minutes <= 0:
                    continue
                origin = sky(rows[:1])[0]
                x, y = origin.spherical_offsets_to(sky(rows))
                t = (np.array([r[2] for r in rows]) - rows[0][2]) * 1440
                slope, offset = np.polyfit(t, np.column_stack((x.arcsec, y.arcsec)), 1)
                say(f"{day}: {len(rows)} detections over {minutes:.2f} min | "
                    f"east {slope[0]:+.5f}, north {slope[1]:+.5f} arcsec/min | "
                    f"speed {np.linalg.norm(slope):.5f} arcsec/min.")
                if minutes < 30:
                    say("  Short baseline: rate is sensitive to positional errors.")

            for day in days:
                if day not in test_cache:
                    test_cache[day] = con.execute(
                        "SELECT sid,visit,mjd,ra,dec,sso FROM sources "
                        "WHERE utc_night=? ORDER BY visit,mjd,sid", (day,)
                    ).fetchall()
                tested = test_cache[day]
                if not tested:
                    say(f"{day}: no alerts to score.")
                    continue
                if name == "2014 WV203" and day == "2026-11-15":
                    training = [r for r in observed if r[6] in ("2026-10-30", "2026-11-12")]
                    if len(training) >= 4:
                        for degree, model in ((1, "linear"), (2, "quadratic")):
                            score(f"{day}, Oct 30 + Nov 12 {model} empirical fit",
                                  tested, fit_positions(training, tested, degree), target)

                visits = {}
                for row in tested:
                    visits.setdefault(row[1], []).append(row[2])
                visit_ids = sorted(visits)
                mjds = [float(np.median(visits[visit])) for visit in visit_ids]
                epochs = Time(mjds, format="mjd", scale="tai").utc.jd
                say(f"Requesting JPL topocentric predictions for {len(visits)} visits on {day}...")
                predictions = {}
                for start in range(0, len(visit_ids), 25):
                    end = start + 25
                    values = horizons(name, epochs[start:end])
                    predictions.update(zip(visit_ids[start:end], zip(mjds[start:end], values)))
                reference = np.array([
                    (predictions[row[1]][0], *predictions[row[1]][1]) for row in tested
                ])
                hours = (np.array([row[2] for row in tested]) - reference[:, 0]) * 24
                if np.max(np.abs(hours)) * 3600 > 60:
                    raise ValueError("Visit timestamps differ by over 60 seconds from median")
                centers = SkyCoord(reference[:, 1] * u.deg, reference[:, 2] * u.deg)
                positions = centers.spherical_offsets_by(
                    reference[:, 3] * hours * u.arcsec,
                    reference[:, 4] * hours * u.arcsec)
                score(f"{day}, JPL known-orbit recovery", tested, positions, target)
        say("\nQuadratic fits are empirical extrapolations. JPL predictions use an external known orbit.")
        say("These checks assess matching and prediction models. Unknown-object orbit linking remains pending.")
        say("Source https://ssd-api.jpl.nasa.gov/doc/horizons.html")
    finally:
        con.close()
        OUTPUT.write_text("\n".join(LOG) + "\n")
        OUTPUT.with_suffix(".html").write_text(
            "<!doctype html><meta charset=utf-8><title>Slow-control recovery</title>"
            "<pre style='white-space:pre-wrap'>" + escape("\n".join(LOG)) + "</pre>"
        )
        print(f"Report saved: {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()

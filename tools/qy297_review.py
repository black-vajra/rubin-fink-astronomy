#!/usr/bin/env python3
"""Reproduce the QY297 check; optionally score every local November 12 alert.

Catalog-known recovery, not discovery or an orbit fitted from Rubin astrometry.
Input identifiers are parsed as Python integers and written as strings.
"""
import argparse
from datetime import datetime, timezone
from html import escape
import importlib.util
import json
from pathlib import Path
import sqlite3

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

NAME = "2001 QY297"
TARGET = "21163611629303641"
RADIUS = 60.0  # Existing project radius, not tuned to this target's residuals.
TEST_DATE = "2026-11-12"


def positions(rows):
    return SkyCoord([r["r:ra"] for r in rows] * u.deg,
                    [r["r:dec"] for r in rows] * u.deg)


def fit_predict(rows, selected, degree):
    """Unweighted tangent-plane diagnostic. Excludes the final observation."""
    t = np.array([r["r:midpointMjdTai"] for r in rows])
    t -= np.mean(t[selected])
    sky = positions(rows)
    x, y = sky[0].spherical_offsets_to(sky)
    coefficients = np.polyfit(t[selected],
                             np.column_stack((x.arcsec[selected], y.arcsec[selected])), degree)
    xy = [np.polyval(coefficients[:, axis], t[-1]) for axis in (0, 1)]
    return sky[0].spherical_offsets_by(xy[0] * u.arcsec, xy[1] * u.arcsec)


def score_archive(db, helper):
    """Predict at every represented visit, then score all rows on the test date."""
    with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as con:
        rows = con.execute(
            "SELECT sid,visit,mjd,ra,dec,sso FROM sources WHERE utc_night=? "
            "ORDER BY visit,mjd,sid", (TEST_DATE,)).fetchall()
    if not rows:
        raise ValueError(f"No indexed alerts for {TEST_DATE}")
    if any(not np.all(np.isfinite(r[2:5])) for r in rows):
        raise ValueError("Invalid time or coordinate in the indexed test night")
    visits = {}
    for r in rows:
        visits.setdefault(str(r[1]), []).append(float(r[2]))
    ids = sorted(visits)
    medians = [float(np.median(visits[v])) for v in ids]
    epochs = Time(medians, format="mjd", scale="tai").utc.jd
    predictions = {}
    for start in range(0, len(ids), 25):
        stop = start + 25
        print(f"JPL visits {start + 1}–{min(stop, len(ids))}/{len(ids)}", flush=True)
        pred = helper.horizons(NAME, epochs[start:stop])
        predictions.update(zip(ids[start:stop], zip(medians[start:stop], pred)))
    reference = np.array([(predictions[str(r[1])][0], *predictions[str(r[1])][1])
                          for r in rows])
    hours = (np.array([r[2] for r in rows]) - reference[:, 0]) * 24
    if np.max(np.abs(hours)) * 3600 > 60:
        raise ValueError("Visit timestamp differs by more than 60 seconds from median")
    centers = SkyCoord(reference[:, 1] * u.deg, reference[:, 2] * u.deg)
    pred = centers.spherical_offsets_by(reference[:, 3] * hours * u.arcsec,
                                        reference[:, 4] * hours * u.arcsec)
    observed = SkyCoord([r[3] for r in rows] * u.deg, [r[4] for r in rows] * u.deg)
    errors = pred.separation(observed).arcsec
    order = np.argsort(errors, kind="stable")
    ranks = np.empty(len(rows), dtype=int)
    ranks[order] = np.arange(1, len(rows) + 1)
    labeled = []
    for i, r in enumerate(rows):
        if str(r[5]) == TARGET:
            labeled.append({"sid": str(r[0]), "visit": str(r[1]),
                            "rank": int(ranks[i]), "error_arcsec": float(errors[i]),
                            "inside_radius": bool(errors[i] <= RADIUS)})
    inside = [{"sid": str(rows[i][0]), "visit": str(rows[i][1]),
               "ssObjectId": str(rows[i][5]), "error_arcsec": float(errors[i])}
              for i in order if errors[i] <= RADIUS]
    return {"UTC_date": TEST_DATE, "alerts_scored": len(rows), "visits": len(ids),
            "radius_arcsec": RADIUS, "labeled_detections": labeled,
            "all_detections_inside_radius": inside,
            "other_label_or_unassociated_inside": sum(str(r["ssObjectId"]) != TARGET for r in inside),
            "database": str(db.resolve()),
            "database_modified_UTC": datetime.fromtimestamp(db.stat().st_mtime, timezone.utc).isoformat(),
            "limitations": "No usable detector masks/footprints; no coverage-normalized false-match rate. "
                           "Scores only alerts already in this archive, not all physical detections."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--db", type=Path, help="Optional Pots archive, opened read-only")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.db and not args.db.is_file():
        raise SystemExit(f"Missing database: {args.db}")
    helper_path = Path(__file__).resolve().parents[1] / "src/historical/slow-control-recovery.py"
    spec = importlib.util.spec_from_file_location("slow_recovery", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.CACHE = args.data_dir / "ephemeris-cache"
    helper.CACHE.mkdir(exist_ok=True)
    raw = json.loads((args.data_dir / "fink-name.json").read_text())
    by_number = json.loads((args.data_dir / "fink-number.json").read_text())
    if {str(r["r:diaSourceId"]) for r in raw} != {str(r["r:diaSourceId"]) for r in by_number}:
        raise ValueError("Name/number queries disagree")
    if len({str(r["r:diaSourceId"]) for r in raw}) != len(raw):
        raise ValueError("Duplicate diaSourceId in source history")
    rows = sorted(raw, key=lambda r: r["r:midpointMjdTai"])
    if len(rows) != 10 or any(str(r["r:ssObjectId"]) != TARGET for r in rows):
        raise ValueError("Unexpected source history; review before using this fixed diagnostic")
    times = Time([r["r:midpointMjdTai"] for r in rows], format="mjd", scale="tai").utc
    if times[-1].isot[:10] != TEST_DATE or np.count_nonzero([s[:10] == TEST_DATE for s in times.isot]) != 1:
        raise ValueError("Unexpected holdout epoch")
    pred = helper.horizons(NAME, times.jd)
    errors = SkyCoord(pred[:, 0] * u.deg, pred[:, 1] * u.deg).separation(positions(rows)).arcsec
    diagnostic = []
    for label, selected, degree in [
        ("October 30 only, linear", np.array([6, 7, 8]), 1),
        ("June 27–October 30, linear", np.arange(9), 1),
        ("June 27–October 30, quadratic", np.arange(9), 2),
    ]:
        miss = float(fit_predict(rows, selected, degree).separation(positions(rows)[-1]).arcsec)
        diagnostic.append({"model": label, "training_points": len(selected),
                           "holdout_error_arcsec": miss, "inside_radius": miss <= RADIUS})
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = {"generated_UTC": generated, "target": NAME, "number": "275809",
              "ssObjectId": TARGET, "radius_arcsec": RADIUS,
              "catalog_position_check": [
                  {"sid": str(r["r:diaSourceId"]), "visit": str(r["r:visit"]),
                   "UTC": str(t), "band": r["r:band"], "ra": r["r:ra"], "dec": r["r:dec"],
                   "JPL_error_arcsec": float(e)} for r, t, e in zip(rows, times.isot, errors)],
              "empirical_diagnostics": diagnostic,
              "full_night_recovery": score_archive(args.db, helper) if args.db else None}
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# 2001 QY297 · distant-binary investigation", "", f"Generated {generated}.", "",
        "Identity: **275809 (2001 QY297)**; Fink ssObjectId **21163611629303641**.", "",
        "Ten unique returned detections on six UTC dates, June 27–November 12. Name and number queries agree. "
        "Only four detections (October 30 and November 12) fall inside the original July 16–November 15 interval. "
        "The earlier six explicitly extend this target's investigation outside that interval. Returned history is not a completeness guarantee.", "",
        "## Position check against JPL", "",
        "Rubin topocenter X05; astrometric ICRF positions. TAI measurement times converted to UTC before Horizons queries. "
        "No time shift or positional offset fitted. This is an external known-orbit check, not an independent orbit solution.", "",
        "| UTC | Band | Source ID | JPL miss (arcsec) |", "|---|---|---|---:|"]
    lines.extend(f"| {r['UTC']} | {r['band']} | {r['sid']} | {r['JPL_error_arcsec']:.4f} |"
                 for r in result["catalog_position_check"])
    clean = all(not r.get(k, True) for r in rows for k in ("r:pixelFlags", "r:centroid_flag", "r:isDipole"))
    lines += ["", f"All ten have pixelFlags=False, centroid_flag=False and isDipole=False: **{clean}**. "
              "These checks do not certify all astrometric or image-quality effects.", "",
        "## Training-only angular prediction diagnostics", "",
        "November 12 is excluded from each fit. The project radius remains **60 arcsec**, established before these scores. "
        "These retrospective diagnostics were selected after the catalog detection was known; they are not a prospective blind search. "
        "Polynomials fit unweighted offsets on the sky and omit observer parallax and orbital dynamics.", "",
        "| Fit | Training points | November 12 miss (arcsec) | Inside 60 arcsec? |", "|---|---:|---:|---|"]
    lines.extend(f"| {d['model']} | {d['training_points']} | {d['holdout_error_arcsec']:.3f} | {d['inside_radius']} |"
                 for d in diagnostic)
    lines += [f"| External JPL orbit | Not fitted here | {errors[-1]:.4f} | {bool(errors[-1] <= RADIUS)} |", "",
        "Adding a longer arc to an unsuitable angular model did not improve extrapolation. "
        "Next independent prediction gate: a physical orbit fit using earlier measurements, with observer motion, light travel time and uncertainty, tested on withheld epochs.", "",
        "## Full-night recovery against the local archive", ""]
    archive = result["full_night_recovery"]
    if archive:
        lines += [f"Scored **{archive['alerts_scored']:,} alerts** in **{archive['visits']} visits** on {TEST_DATE}. "
                  f"**{len(archive['all_detections_inside_radius'])}** fell within 60 arcsec of the known-orbit prediction; "
                  f"**{archive['other_label_or_unassociated_inside']}** carried another label or no matching label.", ""]
        for r in archive["labeled_detections"]:
            lines.append(f"- Control {r['sid']}; visit {r['visit']}; rank {r['rank']:,}; "
                         f"miss {r['error_arcsec']:.4f} arcsec; inside radius: {r['inside_radius']}.")
        if not archive["labeled_detections"]:
            lines.append("No QY297-labeled rows in this archive night; no labeled-recovery success asserted.")
        lines += ["", archive["limitations"]]
    else:
        lines += ["**Not run in this report.** The complete Pots database is not present in this workspace. "
                  "Use --db with the local archive to perform this test. The 0.094 arcsec catalog match alone is not a rank against all 235,039 November 12 alerts."]
    lines += ["", "## Published binary and mass benchmark", "",
        "JPL classifies this as a trans-Neptunian object: osculating heliocentric semimajor axis **43.7575 AU**, "
        "perihelion **40.1882 AU**, aphelion **47.3268 AU**, period **289.46 years** "
        "(SBDB solution 23; element epoch JD 2461200.5 TDB). These are orbit parameters, not its instantaneous distance.", "",
        "Grundy et al. (2011), Table 8, report a resolved **binary mutual** period **138.110 ± 0.023 days**, "
        "relative semimajor axis **9,960 ± 31 km**, and **total system mass (4.105 ± 0.038) × 10^18 kg**. "
        "This is a literature measurement from Hubble/Keck observations, not a mass measured by our Rubin analysis. "
        "The mutual and heliocentric orbits are distinct. Recomputing 4π²a³/(G P²) from the rounded published a and P "
        "gives approximately 4.104 × 10^18 kg; it reuses their measurements, so it is not independent validation.", "",
        "This provides an external dynamical-mass benchmark. Rubin alert astrometry/brightness alone has not "
        "resolved the mutual orbit, measured component masses, or established sizes/densities. "
        "If blended, orbital photocenter motion can contribute astrometric scatter; this report does not quantify it.", "",
        "## What remains", "",
        ("1. Repeat recovery across additional withheld nights and known TNO controls."
         if archive else "1. Execute the full-night local recovery and inspect all competing matches inside the fixed radius."),
        "2. Fit a physical orbit to pre-test observations and propagate prediction uncertainty; add more withheld nights/controls.",
        "3. Obtain usable detector footprints and masks before interpreting matched-footprint comparison counts or false-match rates.",
        "4. Only then extend to unknown slow movers. QY297 is a known binary, with no Planet Nine identification or new mass claim.", "",
        "## Sources and provenance", "",
        "- Fink SSO API: https://api.lsst.fink-portal.org/api/v1/sso ; POST queries by designation and number retained in provenance.json.",
        "- JPL SBDB: https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=275809&full-prec=true ; original JSON retained.",
        "- JPL Horizons: https://ssd.jpl.nasa.gov/horizons/ ; raw responses cached; exact request parameters in the source helper.",
        "- Grundy et al. 2011: https://arxiv.org/abs/1103.2751 ; DOI https://doi.org/10.1016/j.icarus.2011.03.012 ; Table 8.", ""]
    md = "\n".join(lines)
    (args.output / "report.md").write_text(md)
    (args.output / "report.html").write_text(
        "<!doctype html><meta charset=utf-8><title>QY297 investigation</title>"
        "<pre style='white-space:pre-wrap;max-width:1000px;margin:2em auto;font:16px/1.5 system-ui'>" + escape(md) + "</pre>")
    print(f"Report: {args.output / 'report.html'}", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the local Rubin morning research report from Fink and saved Avro."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from math import log10
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from fastavro import reader

ROOT = Path.home() / "rubin-live"
REPORT = ROOT / "research" / "latest.html"
API = "https://api.lsst.fink-portal.org/api/v1"
PGC = "171141216913588260"
TOPICS = {
    "ftransfer_lsst_2026-11-16_279371": 13,
    "ftransfer_lsst_2026-11-16_296945": 14,
    "ftransfer_lsst_2026-11-18_944532": 15,
}
EXPECTED = {13: 76350, 14: 59725, 15: 138867}
PRIMARY, SECONDARY = 21163624428155461, 21164723755430479


def query(endpoint, **params):
    request = Request(
        f"{API}/{endpoint}",
        data=json.dumps({"output-format": "json", **params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=25) as response:
        rows = json.load(response)
    if not isinstance(rows, list):
        raise ValueError(f"Fink returned an unexpected {endpoint} payload")
    return rows


def utc(mjd):
    return Time(mjd, format="mjd", scale="tai").utc.isot + "Z"


def pgc_history():
    fields = ("diaSourceId", "midpointMjdTai", "band", "scienceFlux",
              "scienceFluxErr", "psfFlux", "psfFluxErr", "pixelFlags",
              "pixelFlags_saturated", "pixelFlags_bad", "isDipole")
    rows = query("sources", diaObjectId=PGC, columns=",".join(f"r:{f}" for f in fields))
    i_band = sorted(
        {r["r:diaSourceId"]: r for r in rows
         if r.get("r:band") == "i" and r.get("r:midpointMjdTai") is not None}.values(),
        key=lambda row: float(row["r:midpointMjdTai"]),
    )
    if not i_band:
        return ["Fink returned no usable i-band alert history."]

    def measure(row, field):
        flux = row.get(f"r:{field}")
        error = row.get(f"r:{field}Err")
        if flux is None:
            return "unavailable"
        flux = float(flux)
        value = f"{flux:,.0f} nJy"
        if error is not None:
            value += f" ± {float(error):,.0f} nJy"
        if flux > 0:
            value += f" (AB {31.4 - 2.5 * log10(flux):.3f})"
        return value

    lines = [f"{len(i_band)} i-band alerts in Fink's retrieved history.",
             "Epoch UTC | science image | difference image | flags returned"]
    for row in i_band:
        flags = [
            f"{field}={row['r:' + field]}" for field in fields[7:]
            if row.get("r:" + field) is not None
        ]
        lines.append(
            f"{utc(float(row['r:midpointMjdTai']))} | "
            f"{measure(row, 'scienceFlux')} | {measure(row, 'psfFlux')} | "
            f"{', '.join(flags) or 'unavailable'}"
        )
    for field, name in (("scienceFlux", "Science"), ("psfFlux", "Difference")):
        values = [float(row[f"r:{field}"]) for row in i_band[:-1]
                  if row.get(f"r:{field}") is not None]
        latest = i_band[-1].get(f"r:{field}")
        if values and latest is not None:
            lines.append(f"{name} latest minus earlier median: "
                         f"{float(latest) - np.median(values):+,.0f} nJy "
                         f"({len(values)} earlier values).")
    lines.append("Alert detections only. The comparison is descriptive.")
    return lines


def scan_batches():
    controls = defaultdict(dict)
    test_rows = {14: {}, 15: {}}
    counts = {}
    lines = []
    for folder in sorted((ROOT / "alerts").glob("ftransfer_lsst_*")):
        if not folder.is_dir():
            continue
        night = TOPICS.get(folder.name)
        files = sorted(folder.rglob("*.avro"))
        count, errors = 0, 0
        first, last = float("inf"), float("-inf")
        for path in files:
            try:
                with path.open("rb") as handle:
                    for packet in reader(handle):
                        count += 1
                        source = packet.get("diaSource") or {}
                        row = tuple(source.get(key) for key in (
                            "diaSourceId", "visit", "midpointMjdTai", "ra", "dec", "ssObjectId"
                        ))
                        if None in row[:5] or not all(np.isfinite(row[2:5])):
                            continue
                        first, last = min(first, row[2]), max(last, row[2])
                        if night in test_rows:
                            test_rows[night].setdefault(row[0], row)
                        if night and row[5] in (PRIMARY, SECONDARY):
                            controls[night, row[5]].setdefault(row[0], row)
            except Exception as exc:
                errors += 1
                if errors == 1:
                    lines.append(f"{folder.name}: first Avro error in {path.name}: {exc}")
        span = f"{utc(first)} to {utc(last)}" if first <= last else "no usable timestamps"
        timing_ok = False
        if night and first <= last:
            expected_date = f"2026-11-{night:02d}"
            timing_ok = utc(first).startswith(expected_date) and utc(last).startswith(expected_date)
        verified = night is not None and not errors and count == EXPECTED[night] and timing_ok
        if night:
            counts[night] = verified
        status = "benchmark batch verified" if verified else "full-night completeness unverified"
        lines.append(f"{folder.name} | {len(files):,} files | {count:,} records | "
                     f"{errors} file errors | {span} | {status}")
    return lines or ["No local Fink Data Transfer folders found."], counts, controls, test_rows


def benchmark(counts, controls, test_rows):
    def score(label, target, training, tested, expected):
        if len(training) != expected or not tested:
            return [f"{label}: expected {expected} training detections; found "
                    f"{len(training)} and {len(tested)} test alerts."]
        training = sorted(training, key=lambda row: row[2])
        origin = SkyCoord(training[0][3] * u.deg, training[0][4] * u.deg)
        epoch = training[0][2]

        def minutes(rows):
            return (np.array([r[2] for r in rows]) - epoch) * 1440

        def sky(rows):
            return SkyCoord([r[3] for r in rows] * u.deg, [r[4] for r in rows] * u.deg)

        east, north = origin.spherical_offsets_to(sky(training))
        slope, intercept = np.polyfit(minutes(training),
                                      np.column_stack((east.arcsec, north.arcsec)), 1)
        times, observed = minutes(tested), sky(tested)

        def residuals(shift):
            xy = (times[:, None] + shift) * slope + intercept
            prediction = origin.spherical_offsets_by(xy[:, 0] * u.arcsec, xy[:, 1] * u.arcsec)
            return prediction.separation(observed).arcsec

        errors = residuals(0)
        ranked = np.argsort(errors, kind="stable")
        lines = [f"{label}: ranked {len(tested):,} alerts across all test-night visits.",
                 f"Closest alert {tested[ranked[0]][0]} at {errors[ranked[0]]:.2f} arcsec."]
        matches = [(rank, idx) for rank, idx in enumerate(ranked, 1) if tested[idx][5] == target]
        if not matches:
            return lines + ["Catalog check: control absent."]
        for rank, idx in matches:
            lines.append(f"Control alert {tested[idx][0]} | visit {tested[idx][1]} | "
                         f"rank {rank:,}/{len(tested):,} | {errors[idx]:.2f} arcsec.")
        threshold = float(errors[matches[0][1]])
        unrelated = np.array([row[5] != target for row in tested])
        shifted = [f"{shift:+d} min: {np.count_nonzero((residuals(shift) <= threshold) & unrelated)}"
                   for shift in (-60, -30, -15, 15, 30, 60)]
        lines.append(f"Unrelated alerts within {threshold:.2f} arcsec in six shifted "
                     f"predictions: {', '.join(shifted)}. Diagnostic counts only.")
        return lines

    lines = []
    if counts.get(13) and counts.get(15):
        first = list(controls[13, PRIMARY].values())
        second = list(controls[14, PRIMARY].values())
        tested = list(test_rows[15].values())
        lines.extend(score("Primary, Nov 13 fit → Nov 15", PRIMARY, first, tested, 3))
        if counts.get(14) and (len(first), len(second)) == (3, 2):
            lines.extend(score("Primary, Nov 13–14 fit → Nov 15", PRIMARY,
                               first + second, tested, 5))
    if counts.get(13) and counts.get(14):
        lines.extend(score("Secondary, Nov 13 fit → Nov 14", SECONDARY,
                           list(controls[13, SECONDARY].values()),
                           list(test_rows[14].values()), 3))
    return lines or ["Verified November 13–15 benchmark batches needed."]


def detector_polygon(vertices):
    """Return oriented inward normals for a convex ICRS polygon."""
    coords = np.asarray(vertices, dtype=float)
    if coords.ndim != 2 or coords.shape[1] != 2 or len(coords) < 3:
        raise ValueError("A detector or mask polygon needs at least three RA/Dec pairs")
    if not np.isfinite(coords).all() or np.any(np.abs(coords[:, 1]) > 90):
        raise ValueError("Invalid ICRS polygon coordinates")
    vectors = SkyCoord(coords[:, 0] * u.deg, coords[:, 1] * u.deg).cartesian.xyz.value.T
    normals = np.cross(vectors, np.roll(vectors, -1, axis=0))
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths <= 1e-12):
        raise ValueError("Polygon has a degenerate edge")
    normals /= lengths[:, None]
    normals *= np.sign(normals @ np.mean(vectors, axis=0))[:, None]
    if np.any(np.linalg.norm(normals, axis=1) == 0) or np.any(normals @ vectors.T < -1e-10):
        raise ValueError("Expected ordered vertices of a convex sky polygon")
    return normals


def covered_circle(center, radius_arcsec, detectors, masks):
    """Require containment in one detector and separation from every mask."""
    direction = center.cartesian.xyz.value
    margin = np.sin(np.deg2rad(radius_arcsec / 3600))
    return (
        any(np.all(detector @ direction > margin) for detector in detectors)
        and all(np.any(mask @ direction < -margin) for mask in masks)
    )


def read_strict_alerts(topic, target=None):
    if Path(topic).name != topic or not topic.startswith("ftransfer_lsst_"):
        raise ValueError(f"Invalid local transfer topic {topic!r}")
    files = sorted((ROOT / "alerts" / topic).rglob("*.avro"))
    if not files:
        raise FileNotFoundError(f"No Avro files for {topic}")
    by_id = {}
    for path in files:
        with path.open("rb") as handle:
            for packet in reader(handle):
                source = packet.get("diaSource") or {}
                if target is not None and source.get("ssObjectId") != target:
                    continue
                row = tuple(source.get(key) for key in (
                    "diaSourceId", "visit", "midpointMjdTai", "ra", "dec", "ssObjectId"
                ))
                if None not in row[:5] and np.isfinite(row[2:5]).all():
                    by_id.setdefault(row[0], row)
    return list(by_id.values())


def strict_control(control, footprints, footprints_source, test_cache):
    target = int(control["ss_object_id"])
    radius = float(control["radius_arcsec"])
    max_rate = float(control["max_rate_arcsec_min"])
    if not (0 < radius < 3600 and 0 < max_rate < float("inf")):
        raise ValueError("Radius must be between 0 and 3600 arcsec and maximum rate positive")

    comparisons = np.asarray(control["comparison_offsets_arcsec"], dtype=float)
    if (comparisons.ndim != 2 or comparisons.shape[1] != 2
            or not len(comparisons) or not np.isfinite(comparisons).all()):
        raise ValueError("Specify comparison offsets as a list of east/north pairs")
    if np.any(np.linalg.norm(comparisons, axis=1) <= 2 * radius):
        raise ValueError("Comparison circles must be separated from the prediction circle")

    training_topics = control["training_topics"]
    test_topic = control["test_topic"]
    if not training_topics or test_topic in training_topics:
        raise ValueError("Training and test topics must be distinct")
    training = {
        row[0]: row for topic in training_topics
        for row in read_strict_alerts(topic, target)
    }
    fit_rows = sorted(training.values(), key=lambda row: row[2])
    lines = [f"{control['label']} | catalog ID {target}",
             f"Configured radius: {radius:g} arcsec | maximum training rate: "
             f"{max_rate:g} arcsec/min | footprint source: {footprints_source}"]
    if len({row[1] for row in fit_rows}) < 3 or fit_rows[-1][2] <= fit_rows[0][2]:
        return lines + ["Pending: at least three known training visits with a time baseline."]

    def sky(rows):
        return SkyCoord([r[3] for r in rows] * u.deg, [r[4] for r in rows] * u.deg)

    origin = sky(fit_rows[:1])[0]
    epoch = fit_rows[0][2]
    offsets = origin.spherical_offsets_to(sky(fit_rows))
    xy = np.column_stack([angle.arcsec for angle in offsets])
    times = (np.asarray([r[2] for r in fit_rows]) - epoch) * 1440
    slope, intercept = np.polyfit(times, xy, 1)
    rate = float(np.linalg.norm(slope))
    lines.append(f"Training: {len(fit_rows)} detections | fitted rate: {rate:.4f} arcsec/min.")
    if rate > max_rate:
        return lines + ["Excluded: training rate exceeds the configured slow-mover limit."]

    if test_topic not in test_cache:
        by_visit = defaultdict(list)
        for row in read_strict_alerts(test_topic):
            by_visit[row[1]].append(row)
        test_cache[test_topic] = by_visit
    visits = test_cache[test_topic]
    if not visits or any(row[2] <= fit_rows[-1][2]
                         for rows in visits.values() for row in rows):
        raise ValueError("The test batch must contain only observations after training")

    missing = outside = scored = recovered_visits = comparison_circles = unrelated = 0
    for visit, rows in sorted(visits.items()):
        geometry = footprints.get(str(visit))
        if geometry is None:
            missing += 1
            continue
        detectors, masks = geometry
        visit_time = np.median([r[2] for r in rows])
        east, north = intercept + (visit_time - epoch) * 1440 * slope
        prediction = origin.spherical_offsets_by(east * u.arcsec, north * u.arcsec)
        if not covered_circle(prediction, radius, detectors, masks):
            outside += 1
            continue

        scored += 1
        positions = sky(rows)
        errors = prediction.separation(positions).arcsec
        candidates = np.flatnonzero(errors <= radius)
        ranked = candidates[np.argsort(errors[candidates], kind="stable")]
        hits = [(rank, i) for rank, i in enumerate(ranked, 1) if rows[i][5] == target]
        recovered_visits += bool(hits)
        for rank, i in hits:
            lines.append(f"Visit {visit}: recovered alert {rows[i][0]} at rank "
                         f"{rank}/{len(ranked)} inside radius | {errors[i]:.2f} arcsec.")

        accepted = [prediction]
        for dx, dy in comparisons:
            center = prediction.spherical_offsets_by(dx * u.arcsec, dy * u.arcsec)
            if (any(center.separation(other).arcsec <= 2 * radius for other in accepted)
                    or not covered_circle(center, radius, detectors, masks)):
                continue
            accepted.append(center)
            comparison_circles += 1
            indices = np.flatnonzero(center.separation(positions).arcsec <= radius)
            unrelated += sum(rows[i][5] != target for i in indices)

    lines.append(f"Test visits: {len(visits)} with alerts | {scored} scored | "
                 f"{missing} missing geometry | {outside} prediction circles outside usable area.")
    lines.append(f"Recovered visits: {recovered_visits}/{scored} scored.")
    if comparison_circles:
        lines.append(f"Covered same-visit comparison circles: {comparison_circles} | "
                     f"unrelated alerts: {unrelated}.")
    else:
        lines.append("No covered comparison circles; false-match count unavailable.")
    return lines


def strict_benchmark():
    config_path = ROOT / "research" / "strict-benchmark.json"
    if not config_path.is_file():
        return ["Pending: add verified slow controls, fixed radii and visit footprints "
                "in strict-benchmark.json. No strict benchmark ran."]
    config = json.loads(config_path.read_text())
    provenance = config["footprints_source"].strip()
    if not provenance or not config["controls"] or not config["footprints"]:
        return ["Pending: configuration needs slow controls and documented usable footprints."]
    footprints = {}
    for visit, geometry in config["footprints"].items():
        detectors = [detector_polygon(polygon) for polygon in geometry["usable_polygons"]]
        masks = [detector_polygon(polygon) for polygon in geometry.get("mask_polygons", [])]
        if not detectors:
            raise ValueError(f"Visit {visit} has no usable polygons")
        footprints[visit] = (detectors, masks)
    lines = ["Settings are read before scoring. Each visit uses its median alert timestamp. "
             "Geometry must come from calibrated images or verified detector coverage."]
    test_cache = {}
    for control in config["controls"]:
        try:
            lines.extend(strict_control(control, footprints, provenance, test_cache))
        except (KeyError, OSError, TypeError, ValueError) as exc:
            lines.append(f"{control.get('label', 'Control')}: could not score: {exc}")
    return lines


def published_nights():
    today = date.today()
    recent = {today - timedelta(days=i) for i in range(7)}
    rows = {}
    for month in sorted({day.strftime("%Y%m") for day in recent}):
        for row in query("statistics", date=month):
            rows[str(row.get("f:night"))] = row.get("f:alerts")
    return [f"{day.isoformat()}: " + (
        f"{rows[day.strftime('%Y%m%d')]} published alerts"
        if day.strftime("%Y%m%d") in rows else "no published statistics entry"
    ) for day in sorted(recent)]


def main():
    sections = {}
    for title, task in (("PGC 766016 · i-band history", pgc_history),
                        ("Fink · recent observing nights", published_nights)):
        try:
            sections[title] = task()
        except Exception as exc:
            sections[title] = [f"Query failed: {type(exc).__name__}: {exc}"]
    scans, counts, controls, test_rows = scan_batches()
    sections["Local Avro inventory"] = scans
    try:
        sections["Known-object recovery"] = benchmark(counts, controls, test_rows)
    except Exception as exc:
        sections["Known-object recovery"] = [f"Benchmark failed: {type(exc).__name__}: {exc}"]
    try:
        sections["Slow-mover benchmark · fixed-radius, footprint-checked"] = strict_benchmark()
    except (KeyError, OSError, TypeError, ValueError) as exc:
        sections["Slow-mover benchmark · fixed-radius, footprint-checked"] = [
            f"Configuration could not be read: {exc}"
        ]
    sections["Deferred analyses"] = [
        "Full-night job submission: manual through Fink Data Transfer.",
        "Size and mass ranges: pending a calibrated benchmark with independent size or mass.",
        "Planet Nine candidate screening: pending validation against slow known objects and "
        "more extensive false-match controls. No candidate search ran in this report.",
    ]
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = "".join(f"<h2>{escape(title)}</h2><pre>{escape(chr(10).join(lines))}</pre>"
                   for title, lines in sections.items())
    html = ("<!doctype html><meta charset=utf-8><title>Rubin Morning Research</title>"
            "<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}"
            "pre{white-space:pre-wrap;background:#eef2f5;padding:1rem}</style>"
            f"<h1>Rubin Morning Research</h1><p>Generated {generated}</p>{body}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=REPORT.parent, delete=False) as tmp:
        tmp.write(html)
    Path(tmp.name).replace(REPORT)
    print(f"REPORT: {REPORT}")


if __name__ == "__main__":
    main()

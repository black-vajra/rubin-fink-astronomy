#!/usr/bin/env python3
"""Add the observation time span to the installed Rubin daily reports."""
import argparse
import ast
from pathlib import Path
import tempfile

POTS = [
    ("    latest=db.execute('SELECT max(mjd) FROM rw_measurements').fetchone()[0]",
     """    earliest, latest = db.execute(
        'SELECT min(mjd), max(mjd) FROM rw_measurements WHERE mjd > 50000 AND mjd < 100000'
    ).fetchone()
    observation_span = None
    if earliest is not None:
        observation_span = dict(
            earliest_utc=core.utc(earliest), latest_utc=core.utc(latest),
            earliest_mjd_tai=earliest, latest_mjd_tai=latest,
            elapsed_seconds=round((latest-earliest)*86400, 3))
    span_text = 'No valid observation timestamps'
    if observation_span:
        span_text = (f"{observation_span['earliest_utc']} through "
                     f"{observation_span['latest_utc']} · "
                     f"{observation_span['elapsed_seconds']:,.3f} s elapsed")"""),
    ("freshness=core.freshness(latest),fields=fields,",
     "freshness=core.freshness(latest),observation_span=observation_span,fields=fields,"),
    ("<p class=\"warn\">{esc(data['freshness'])}</p>",
     "<p><strong>Observation span (UTC, all stored detections)</strong> {esc(span_text)}</p>\n"
     "    <p class=\"warn\">{esc(data['freshness'])}</p>"),
]

PAVILION = [
    ('    newest = utc(next(iter(latest.values()))[0]) if latest else "No valid alerts saved yet"',
     """    observation_span = "No valid observation timestamps"
    valid = [source for _, source, _, _ in ordered if not source.get("timeWithdrawnMjdTai")]
    if valid:
        earliest, newest = valid[-1], valid[0]
        elapsed = (newest["midpointMjdTai"] - earliest["midpointMjdTai"]) * 86400
        observation_span = f"{utc(earliest)} through {utc(newest)} · {elapsed:,.3f} s elapsed" """.rstrip()),
    ("<p>Latest observation (UTC) {newest}</p>",
     "<p><strong>Observation span (UTC, all valid non-withdrawn detections)</strong> "
     "{esc(observation_span)}</p>"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", choices=("pots", "pavilion"))
    host = parser.parse_args().host
    relative, changes = (
        ("rubin-live/search/rubin-distant-watch.py", POTS) if host == "pots"
        else ("rubin-quasar/report.py", PAVILION)
    )
    path = Path.home() / relative
    old = path.read_text()
    if all(new in old for _, new in changes):
        print(f"Already updated: {path}")
        return
    updated = old
    for before, after in changes:
        if updated.count(before) != 1:
            raise SystemExit(f"Unexpected installed version at {path}. File left intact.")
        updated = updated.replace(before, after, 1)
    ast.parse(updated, filename=str(path))
    backup = path.with_suffix(".py.before-observation-span")
    with backup.open("x") as handle:
        handle.write(old)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
        handle.write(updated)
        temporary = Path(handle.name)
    try:
        temporary.chmod(path.stat().st_mode & 0o777)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Updated {path}\nBackup: {backup}")


if __name__ == "__main__":
    main()

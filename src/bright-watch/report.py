"""Generate the Pavilion's bright extragalactic alert report."""
import html
import math
import os
from pathlib import Path
from datetime import datetime, timezone

from astropy.time import Time
from fastavro import reader

ROOT = Path.home() / "rubin-quasar"


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def magnitude(flux):
    flux = number(flux)
    return f"{31.4 - 2.5 * math.log10(flux):.2f}" if flux is not None and flux > 0 else "—"


def catalog_value(value):
    if value is None or str(value).strip().lower() in ("", "none", "unknown", "fail", "nan", "null"):
        return "—"
    return str(value)


def main():
    detections = {}
    errors = []
    for path in sorted((ROOT / "alerts").glob("*/*.avro")):
        try:
            with path.open("rb") as stream:
                for packet in reader(stream):
                    source = packet.get("diaSource") or {}
                    sid = source.get("diaSourceId")
                    mjd = number(source.get("midpointMjdTai"))
                    if type(sid) is not int or sid <= 0 or mjd is None or not 50000 < mjd < 100000:
                        raise ValueError("Missing valid detection ID or observation time")
                    processed = number(source.get("timeProcessedMjdTai")) or 0
                    if sid not in detections or processed > detections[sid][0]:
                        detections[sid] = (processed, source, packet.get("xm") or {},
                                           len(packet.get("prvDiaSources") or []))
        except (ValueError, EOFError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    latest = {}
    ordered = sorted(detections.values(), key=lambda item: item[1]["midpointMjdTai"], reverse=True)
    for _, source, xm, history in ordered:
        if source.get("timeWithdrawnMjdTai"):
            continue
        oid = source.get("diaObjectId")
        key = ("object", oid) if type(oid) is int and oid > 0 else ("source", source["diaSourceId"])
        latest.setdefault(key, (source, xm, history))

    def utc(source):
        return Time(source["midpointMjdTai"], format="mjd", scale="tai").utc.isot + "Z"

    esc = html.escape
    rows = []
    for source, xm, history in list(latest.values())[:200]:
        oid = source.get("diaObjectId")
        sid = source["diaSourceId"]
        link = (f'<a href="https://lsst.fink-portal.org/{oid}">{oid}</a>'
                if type(oid) is int and oid > 0 else "—")
        cells = [str(sid), utc(source), str(source.get("band") or "—"),
                 magnitude(source.get("psfFlux")), magnitude(source.get("scienceFlux")),
                 catalog_value(xm.get("milliquas_type")), catalog_value(xm.get("milliquas_redshift")),
                 catalog_value(xm.get("simbad_otype")), str(history)]
        rows.append(f"<tr><td>{link}</td>" + "".join(f"<td>{esc(cell)}</td>" for cell in cells) + "</tr>")
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    newest = utc(next(iter(latest.values()))[0]) if latest else "No valid alerts saved yet"
    doc = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rubin Bright Extragalactic Watch</title>
<style>body{{background:#08151e;color:#e8f0f4;font:16px system-ui;margin:2rem}}
a{{color:#79e4cf}}td,th{{padding:.55rem;border-bottom:1px solid #36505e;text-align:left}}
div{{overflow:auto}}</style>
<h1>Bright Extragalactic Candidates</h1>
<p>Fink LSST · Pavilion · Generated {generated}</p>
<p>{len(detections)} distinct detections · {len(latest)} objects or ungrouped detections · {len(errors)} file errors</p>
<p>Latest observation (UTC) {newest}</p>
<p>Latest alert per object, up to 200 rows. Milliquas and SIMBAD entries are catalog crossmatches.
Magnitudes are AB values derived from positive difference and science fluxes in nJy.</p>
<div><table><tr><th>Fink object</th><th>Detection ID</th><th>Observation UTC</th><th>Band</th>
<th>Difference mag</th><th>Science mag</th><th>Milliquas type</th><th>Milliquas redshift</th>
<th>SIMBAD type</th><th>Prior detections in packet</th></tr>{''.join(rows)}</table></div>
<p>{esc(' | '.join(errors[:20]))}</p></html>"""
    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    temp = reports / "latest.html.tmp"
    temp.write_text(doc, encoding="utf-8")
    os.replace(temp, reports / "latest.html")
    print(f"REPORT: {reports / 'latest.html'} | {len(detections)} detections | {len(errors)} file errors")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

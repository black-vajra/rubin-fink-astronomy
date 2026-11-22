#!/usr/bin/env python3
"""Build dated reports from retained Fink responses, host evidence and research outputs."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from astropy.time import Time
from report_html import render

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report-date',required=True);a=p.parse_args()
base=ROOT/'reports'/a.report_date.replace('-','/')
fresh=json.loads((base/'freshness-review/freshness.json').read_text())
host=json.loads((base/'pots-overnight-evidence.json').read_text())
ed=json.loads((base/'ed138-public-astrometry/results.json').read_text())
pgc=json.loads((base/'pgc-fit-sensitivity/results.json').read_text())
generated=datetime.now(timezone.utc).isoformat(timespec='seconds')

def write(name,lines):
    md='\n'.join(lines)+'\n';(base/(name+'.md')).write_text(md)
    (base/(name+'.html')).write_text(render(md,lines[0].lstrip('# ')))

local=['Both scheduled reports completed successfully on Pots: bright-object report at **09:00 EST** (60 detections, zero file errors), morning research at **09:10 EST**.',
       'The collector ran from **19:26:23 EST November 20** until **09:00:01 EST November 21**. Its late start reduced the intended window by 2 h 26 min; that is consistent with the stated dual-boot practice. The reported 626.4-minute gap includes the planned daytime stop.',
       'Kafka session/heartbeat/fetch timeouts occurred around 07:21 and 07:32. These are communication interruptions, distinct from the camera status. The collector remained running until its scheduled stop. The user-supplied inbox check found **zero new Avro files** in the assessed window; the newest files remain dated November 15. Missed-message counts are not established.']
review=[f'# Overnight review · {a.report_date}','',f'Generated {generated}. Reporting date is America/New_York.','',
    '## Delivery and automation','']+local+['',
    'Eight small Fink queries succeeded: monthly statistics, four extragalactic histories and three moving-object histories. The ED138 Fink query returned HTTP 400. All seven successful object histories have unchanged source-ID membership and unchanged returned records versus their saved November 20 baselines. None has a returned non-withdrawn observation in the assessed November 20 17:00–November 21 09:00 EST window.', '',
    '**Freshly generated reports do not mean freshly observed sky data.** The latest returned Fink published-night key is **20261115**. Missing statistics entries are not independently asserted to mean zero telescope visits.','',
    'Rubin’s homepage as retrieved for this review still displays a temporary off-sky notice; the latest formal cooling-issue notice found is dated November 17. No newer restart date was established.','',
    '## Work advanced with existing observations','',
    '| Track | Work completed | Result |','|---|---|---|',
    '| Extragalactic | Refreshed four histories; twelve image-fit choices per PGC cutout | No changed history; residual-image amplitudes depend on measurement choice; no confirmed flare |',
    '| Moving objects | Retrieved public ED138 astrometry; fitted earlier Rubin positions and withheld later ones | 74 public records retained; five withheld errors 0.027–0.075 arcsec |',
    '| Methodology | Reviewed discovery/precovery sources | Targeted archival workflow identified; no ADAM login/search or new-object scan |','',
    '## Reports','',f'- [Extragalactic review]({a.report_date}-extragalactic-report.html)',f'- [Moving-object review]({a.report_date}-moving-object-report.html)',
    '- [Freshness data and query accounting](freshness-review/report.html)','- [PGC fit-choice diagnostic](pgc-fit-sensitivity/report.html)',
    '- [ED138 public-astrometry benchmark](ed138-public-astrometry/report.html)','- [Methods and data-source follow-up](methods-and-data-sources.html)','',
    'Official sources: https://rubinobservatory.org/ ; https://www.rubin.community/t/rubin-status-november-17-2026/12959 . Fresh Fink response provenance and user-supplied host evidence are retained in this directory.']
write('overnight-review',review)

lines=[f'# Extragalactic review · {a.report_date}','',f'Generated {generated}.','',
    '**No new observations or changed returned source records in the four queried watchlist histories.** Measurements below remain historical; the assessed interval starts July 16, 2026 and extends through this retrieval, rather than silently stopping the analysis at November 15.','',
    '| Object | Band | Unique points since July 16 | Latest UTC | Latest science / earlier median | Latest difference / earlier median |','|---|---|---:|---|---:|---:|']
labels=[('PGC 766016','171141216913588260'),('Quasar crossmatch','313774266976305153'),('Science-image high','313862200773574662'),('AT 2019hkw','170653056044630027')]
for label,sid in labels:
    raw=json.loads((base/f'freshness-review/data/object-{sid}.json').read_text());unique={str(r['r:diaSourceId']):r for r in raw if r.get('r:timeWithdrawnMjdTai') is None}
    rows=[r for r in unique.values() if r.get('r:midpointMjdTai') is not None and str(Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot)>='2026-07-16']
    for band in sorted({r['r:band'] for r in rows}):
        selected=sorted([r for r in rows if r['r:band']==band],key=lambda r:r['r:midpointMjdTai'])
        ratios=[]
        for key in ['r:scienceFlux','r:psfFlux']:
            earlier=[r[key] for r in selected[:-1] if r.get(key) is not None]
            ratios.append(f'{selected[-1][key]/np.median(earlier):.3f}' if earlier and np.median(earlier)!=0 else '—')
        lines.append(f"| {label} | {band} | {len(selected)} | {Time(selected[-1]['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot} | {ratios[0]} | {ratios[1]} |")
lines += ['', 'Ratios compare alert-selected samples in the same filter. They are descriptive comparisons, not variability significances. One-point bands cannot support a same-band trend.','',
    '## New archived-image sensitivity test','',
    'The retained November 11/13/15 PGC cutouts were refitted over a fixed grid: radii 6/10/14 pixels, constant/planar backgrounds, uniform/inverse-variance weighting. All twelve results per cutout are retained.','',
    '| UTC date | Difference-image amplitude range, nJy | Median across choices, nJy |','|---|---:|---:|']
for r in pgc['measurements']:
    if r['kind']=='Difference':lines.append(f"| {r['UTC_date']} | {r['amplitude_min_nJy']:,.0f}–{r['amplitude_max_nJy']:,.0f} | {r['amplitude_median_nJy']:,.0f} |")
lines += ['', 'The ranges overlap, but that is not a formal statistical test. The spread across methods measures fitting sensitivity, not a calibrated uncertainty. The reported science-image rise is not sufficient to assign a nuclear flare.','',
    'The supplied FITS do not provide an explicit mask-bit dictionary; no generic mask mapping was guessed. Nuclear/host decomposition, independent calibration and inter-pixel covariance remain unresolved. The full diagnostic and file hashes are in [PGC fit sensitivity](pgc-fit-sensitivity/report.html).','',
    'Next: establish product-specific mask semantics and usable photometric calibration before interpreting a cross-epoch nuclear light curve. No additional extragalactic discovery scan ran on the unchanged archive in this review.']
write(a.report_date+'-extragalactic-report',lines)

lines=[f'# Moving-object review · {a.report_date}','',f'Generated {generated}.','',
    'Active scope remains **2001 QY297, 2014 WV203, 2013 CR7 and 2026 ED138**. The three successful Fink histories are unchanged; ED138’s Fink query failed with HTTP 400. The public MPC route succeeded.','',
    '## ED138 public-astrometry gate completed','',
    'Retrieved MPEC 2026-U85 and parsed **74 public observations**: **30 Rubin/X05** positions on **20 dates**, March 4–July 11, 2026; and **44 DECam/W84** positions on **14 dates**, February 25, 2016–April 7, 2023. The latter are retained but not included in this initial fit.','',
    'Before numerical scoring, the training cutoff was fixed at **June 13, 2026 UTC**. We fitted 25 Rubin positions on 17 earlier dates and withheld five later positions. No target catalog orbit, orbital elements printed in the circular, or restricted Rubin image/catalog release entered the fit.','',
    '| Withheld UTC | Miss (arcsec) | Inside fixed 60 arcsec? |','|---|---:|---|']
for r in ed['withheld']:lines.append(f"| {r['UTC']} | {r['error_arcsec']:.3f} | {r['inside_60_arcsec']} |")
lines += ['', 'This is a retrospective known-object benchmark with a Sun-only physical model, observer motion and light travel time. It is not an independent discovery, a globally unique precision orbit, or a size/mass result. Formal errors remain conditional on the assumed 0.15 arcsec coordinate floor and selected branch.','',
    'See [ED138 raw data, geometry, trials and benchmark](ed138-public-astrometry/report.html). Native MPC line numbers/station codes are retained; no Fink source IDs or visit IDs were fabricated.','',
    '## QY297 and comparison controls','',
    'The prior QY297, CR7 and WV203 fits remain their November 20 results, not freshly recomputed orbital solutions. Next numerical gate remains planetary perturbations, global orbit ambiguity/uncertainty and an established-fitter cross-check. The fitted-track full-night ranking remains separate from the already verified external-JPL recovery.','',
    '## Methodology follow-up','',
    'The discovery announcement prompted a targeted review of linking and precovery methods. See [methods and source-access notes](methods-and-data-sources.html). Our next archive searches should remain confined to the named watchlist, preserving candidate provenance and image-level validation. No authenticated ADAM search was submitted and no broad new-object search ran.','',
    'The public astrometry and restricted image/catalog release are distinct products. ED138 is now an active public-astrometry benchmark; its proprietary RSP images were not accessed.']
write(a.report_date+'-moving-object-report',lines)

fresh['local_Pots_overnight_service_and_file_evidence']={'status':'user terminal evidence supplied','file':'../pots-overnight-evidence.json','reports_completed':True,'new_local_Avro_count':host['local_new_Avro_count']}
(base/'freshness-review/freshness.json').write_text(json.dumps(fresh,indent=2)+'\n')
fresh_report=(base/'freshness-review/report.md').read_text().split('## Local overnight evidence',1)[0]
fresh_report += ('## Local overnight evidence\n\n'
    f"User-supplied Pots logs confirm reports completed at 09:00 and 09:10 EST. Collector start 19:26:23; scheduled stop 09:00:01; Kafka timeouts around 07:21 and 07:32. "
    f"The inbox check found **{host['local_new_Avro_count']} new Avro files** in the assessed window; newest files remain dated November 15. "
    'See the retained pots-overnight-evidence.json for the supplied file timestamps.\n\n'
    'Counts in the freshness table cover all returned history epochs; the science report tables apply the July 16 onward interval. '
    'This explains differences between history totals and the science-table counts.\n\n'
    'Raw responses, request parameters, retrieval timestamps, response hashes and source-ID changes are retained. '
    'The ED138 Fink query returned HTTP 400; it was not a successful empty result. Public MPC astrometry was retrieved separately and used for the historical benchmark.\n')
(base/'freshness-review/report.md').write_text(fresh_report);(base/'freshness-review/report.html').write_text(render(fresh_report,'Fink freshness review'))
for folder in ['ed138-public-astrometry','pgc-fit-sensitivity']:
    md=(base/folder/'report.md').read_text();(base/folder/'report.html').write_text(render(md,folder))
print('Built overview, both science reports, and readable HTML diagnostics:',base)

for source,name in [('freshness-review/report.md','freshness-and-query-accounting.html'),('pgc-fit-sensitivity/report.md','pgc-fit-choice-diagnostic.html'),('ed138-public-astrometry/report.md','ed138-public-astrometry-benchmark.html'),('methods-and-data-sources.md','methods-and-data-sources.html')]:
    md=(base/source).read_text()
    (base/name).write_text(render(md,name))

from datetime import datetime, timezone
from html import escape
import importlib.util
import json
from pathlib import Path
import zipfile

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('historical',BASE/'historical.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
h.extragalactic()
now=datetime.now(timezone.utc).isoformat(timespec='seconds')
provenance=json.loads((BASE/'refresh-provenance.json').read_text())
assert len(provenance)==7 and all(r['status']=='fresh' for r in provenance)
assert all(not r['added_source_ids'] and not r['removed_source_ids'] for r in provenance)
common=f'''Generated {now}. Reporting date November 20, 2026 (America/New_York).

Seven fresh Fink API queries succeeded today. No source IDs were added or removed for the four watchlist objects or either named slow control compared with the saved November 19 responses. November statistics still end on November 15. This verifies the returned histories, not every possible source in the archive.

Scope: public histories refreshed today; monthly SSO/physical snapshots retained from November 19. The full 1,043,458-source archive is on Pots and was not rerun here. The historical interval remains July 16–November 15 inclusive.

'''
ex=(BASE/'extragalactic-report.md').read_text()
ex=ex.replace('# Historical extragalactic report\n\n','# Extragalactic search · November 20, 2026\n\n'+common,1)
ex+='''
## Interpretation and immediate work

PGC 766016 still has six i-band detections. Latest science flux is 1.477 times the earlier median; difference flux is 0.981 times it. These are descriptive comparisons of alert detections, not evidence sufficient to identify a nuclear flare. The quasar crossmatch is modestly changed in this sample (science 1.048, difference 0.936). The science-image-high object's i-band ratios are 1.124 and 0.978. AT 2019hkw has only one in-window measurement per returned band, preventing a same-band trend test here.

### PGC science, template and difference measurements

| UTC epoch | Detector | Science nJy | Template nJy | Difference nJy | Template version |
|---|---:|---:|---:|---:|---:|
'''
rows=json.loads((BASE/'data/object-171141216913588260.json').read_text())
rows=sorted({str(r['r:diaSourceId']):r for r in rows if r.get('r:band')=='i' and h.in_window(r['r:midpointMjdTai'])}.values(),key=lambda r:r['r:midpointMjdTai'])
for r in rows:
    ex+='| '+h.Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot+' | '+str(r.get('r:detector'))+' | '+' | '.join(f"{r['r:'+f]:,.0f}" for f in ['scienceFlux','templateFlux','psfFlux'])+' | '+str(r.get('r:templateVersion'))+' |\n'
ex+='''
Template flux rises alongside science flux. Different detectors and measurement/reference effects need examination. Template version numbers alone do not establish identical reference content. No image-cutout or forced-photometry analysis ran today. Next: compare the November 11, 13 and 15 science/reference/difference images, seeing and calibration before attributing the rise to the source.

Source: https://api.lsst.fink-portal.org/api/v1/sources . Exact query parameters, timestamps and response hashes are in refresh-provenance.json.
'''
motion=(BASE/'moving-object-report.md').read_text()
motion=motion.replace('# Historical moving-object report\n\n','# Moving-object search · November 20, 2026\n\n'+common,1)
motion=motion.replace('cataloged objects.','product entries in the cached snapshot; archive populations are excluded from this run.')
motion=motion.replace('The monthly SSO bulk product can omit November measurements. The compact transfer ftransfer_lsst_2026-11-19_639723 is required to supplement it through November 15.','The cached monthly bulk product omits later measurements. The compact transfer was imported successfully on Pots on November 19; that database is absent here. No additional download is required to resume those tests on Pots.')
motion+='''
## Recovery results carried forward from November 19

The following are documented results from the November 19 journal, not fresh full-archive tests today.

| Control | Held-out night | Recovered | JPL prediction error |
|---|---|---:|---|
| 2014 WV203 | November 12 | 2/2 | 0.060 and 0.086 arcsec |
| 2014 WV203 | November 15 | 1/1 | 0.034 arcsec |
| 2013 CR7 | November 12 | 1/1 | 0.013 arcsec |

These recoveries used independent known-orbit predictions from JPL Horizons, a preselected 60 arcsec radius and all alerts on the test nights. They validate tested position/time handling. They do not validate fitting an unknown orbit. The WV203 November 12 search included an unrelated alert inside that radius.

Short-arc linear predictions failed over 13–16 days. For WV203, fitting October 30 plus November 12 reduced the November 15 miss to 610.045 arcsec (linear) or 122.979 arcsec (quadratic), both outside the fixed radius.

Next: fit a physical orbit using only training observations, withhold later detections, and compare against JPL. Obtain usable detector footprints before coverage-normalized comparison-position scoring. Keep search radii fixed before scoring; if a new radius is calibrated, test it on a separate holdout. Apparent slow motion alone does not establish a distant orbit.

2026 ED138 remains a priority control. Its dedicated March 4–July 11 release is outside this archive interval; public MPC astrometry retrieval remains pending. No ED138 recovery, unknown-body search, size/mass estimate or Planet Nine screening ran today.

Sources: fresh Fink /sso responses and cached ssobulk.parquet; November 19b journal for prior recovery results. JPL documentation https://ssd-api.jpl.nasa.gov/doc/horizons.html ; ED138 release https://prompt-products.lsst.io/products/2026-ED138/index.html .
'''
for filename,body in [('2026-11-20-extragalactic-report',ex),('2026-11-20-moving-object-report',motion)]:
    (BASE/(filename+'.md')).write_text(body)
    (BASE/(filename+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>'+filename+'</title><style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem}pre{white-space:pre-wrap}</style><pre>'+escape(body)+'</pre>')
print('Dated reports written; seven successful fresh queries verified.')

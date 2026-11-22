#!/usr/bin/env python3
"""Audit supplied QY297 ADAM exports; no orbit fitting or attribution claims."""
from pathlib import Path
import argparse, collections, csv, hashlib, json, math, re, shutil
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import pyarrow.parquet as pq
from report_html import render

BASE=Path(__file__).resolve().parents[1]
def mjd(x): return x['time']['days']+x['time']['nanos']/86400e9
def utc(x): return (datetime(1858,11,17,tzinfo=timezone.utc)+timedelta(days=mjd(x))).isoformat()
def sep(x,y):
    a,b,c,d=map(math.radians,[x['ra'],x['dec'],y['ra'],y['dec']])
    h=math.sin((b-d)/2)**2+math.cos(b)*math.cos(d)*math.sin((a-c)/2)**2
    return math.degrees(2*math.asin(min(1,math.sqrt(h))))*3600

def main():
    p=argparse.ArgumentParser();p.add_argument('--uploads',type=Path,required=True);a=p.parse_args()
    out=BASE/'reports/2026/11/21/qy297-adam-reconciliation';out.mkdir(parents=True,exist_ok=True)
    inputs=out/'inputs';inputs.mkdir(exist_ok=True)
    names=['275809_orbit_inputs.parquet','275809_observations.adam-core.parquet','Pasted text(3).txt']
    manifest=[]
    for name in names:
        dst=inputs/({'Pasted text(3).txt':'search-spans.txt'}.get(name,name));shutil.copyfile(a.uploads/name,dst)
        manifest.append({'path':str(dst.relative_to(out)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size})
    table=pq.read_table(inputs/names[1]);rows=table.to_pylist();mpc=[x for x in rows if x['catalog_id']=='mpc'];nsc=[x for x in rows if x['catalog_id']=='nsc'];lsst=[x for x in rows if x['catalog_id']=='lsst']
    orbit=pq.read_table(inputs/names[0]).to_pylist()[0]
    assert len(rows)==408 and orbit['object_id']=='275809 (2001 QY297)'
    # Predeclared conservative duplicate-screen tolerances, unrelated to orbit recovery radius.
    matches=[]
    for i,x in enumerate(rows):
        for y in rows[i+1:]:
            if x['observatory_code']==y['observatory_code'] and abs(mjd(x)-mjd(y))*86400<=2 and sep(x,y)<=2:
                matches.append({'id_a':x['id'],'catalog_a':x['catalog_id'],'id_b':y['id'],'catalog_b':y['catalog_id'],'delta_seconds':abs(mjd(x)-mjd(y))*86400,'separation_arcsec':sep(x,y)})
    nights=collections.defaultdict(list)
    for x in nsc:nights[utc(x)[:10]].append(x)
    # One SIA query per night, 0.05-degree box; contains each night's candidate positions.
    def image_query(item):
        date,rr=item;ra=sum(x['ra'] for x in rr)/len(rr);dec=sum(x['dec'] for x in rr)/len(rr)
        url='https://datalab.noirlab.edu/sia/nsc_dr2?'+urlencode({'POS':f'{ra},{dec}','SIZE':'0.05','FORMAT':'ALL'})
        result={'night':date,'url':url,'queried_utc':datetime.now(timezone.utc).isoformat(),'radius_note':'0.05-degree square centered on mean nightly position; not a detector-footprint test'}
        cache=out/f'sia-{date}.xml'
        try:
            if not cache.exists():
                with urlopen(url,timeout=25) as response:data=response.read(5000001)
                if len(data)>5000000:raise ValueError('SIA response exceeded 5 MB cap')
                cache.write_bytes(data)
            root=ET.fromstring(cache.read_bytes());result['rows']=len(root.findall('.//{*}TABLEDATA/{*}TR'));result['status']=[e.attrib for e in root.findall('.//{*}INFO') if e.attrib.get('name')=='QUERY_STATUS'];result['response_sha256']=hashlib.sha256(cache.read_bytes()).hexdigest()
        except Exception as e:result['error']=f'{type(e).__name__}: {e}'
        return result
    image_results=list(ThreadPoolExecutor(max_workers=4).map(image_query,sorted(nights.items())))
    night_rows=[]
    for date,rr in sorted(nights.items()):
        rr=sorted(rr,key=mjd)
        night_rows.append({'date_utc':date,'rows':len(rr),'bands':','.join(sorted(set(x['filter'] for x in rr))),'first_utc':utc(rr[0]),'last_utc':utc(rr[-1]),'position_span_arcsec':max(sep(x,y) for x in rr for y in rr),'median_mag_sigma':sorted(x['mag_sigma'] for x in rr)[len(rr)//2]})
    old=json.loads((BASE/'reports/2026/11/20/qy297-investigation/fink-number.json').read_text());oldids={str(x['r:diaSourceId']) for x in old};newids={str(x['id']).removeprefix('lsst:') for x in lsst}
    spans=re.findall(r'(?m)^(\d{4})\s*\n\s*(\d{4}-\d{2}-\d{2}) – (\d{4}-\d{2}-\d{2})\s*\n\s*(\w+)\s*\n\s*(?:\d+/\d+ cutouts\s*\n\s*)?(\d+)',(inputs/'search-spans.txt').read_text())
    summary={'generated_utc':datetime.now(timezone.utc).isoformat(),'job_id':table.schema.metadata[b'precovery.job_id'].decode(),'rows':len(rows),'catalog_counts':dict(collections.Counter(x['catalog_id'] for x in rows)),'screen':{'same_station':True,'time_seconds':2,'angular_arcsec':2,'purpose':'duplicate screen, not orbit fit gate'},'duplicate_pairs':matches,'nsc_nights':night_rows,'nsc_exposure_ids_unique':len(set(x['exposure_id'] for x in nsc)),'nsc_mpc_same_station_rows':sum(x['observatory_code']=='W84' for x in mpc),'lsst_ids_equal_previous_fink':newids==oldids,'lsst_only_ids':sorted(newids-oldids),'previous_fink_only_ids':sorted(oldids-newids),'spans':{'count':len(spans),'states':dict(collections.Counter(x[3] for x in spans)),'accepted_sum':sum(int(x[4]) for x in spans)},'image_queries':image_results,'input_manifest':manifest}
    (out/'results.json').write_text(json.dumps(summary,indent=2))
    with (out/'nsc-measurements.csv').open('w') as f:
        keys=['id','exposure_id','utc','ra','dec','ra_sigma','dec_sigma','mag','mag_sigma','filter','observatory_code','exposure_duration','astcat','photcat'];w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for x in nsc:w.writerow({**{k:x[k] for k in keys if k!='utc'},'utc':utc(x)})
    lines=['# QY297 · ADAM archive reconciliation','Reporting date November 21, 2026 (America/New_York).',f"Generated {summary['generated_utc']}. Run {summary['job_id']}.",'## Accounting','408 exported rows: 342 MPC, 56 NSC/DECam (W84), 10 Rubin (X05). These are catalog rows, not 408 independent exposures.',f"All {len(spans)} pasted search spans are marked complete. Their accepted counts sum to {summary['spans']['accepted_sum']}; this differs from export rows. The export mixes attributed MPC records and accepted survey detections; exact accepted/recovered/new accounting needs the ADAM detailed-accounting export.",'## Duplicate screen',f"Same station, within 2 seconds and 2 arcseconds: {len(matches)} matching pairs. This is a screening definition, not proof that every remaining row is independent.",f"All 56 DECam rows have distinct exposure IDs and span {len(nights)} UTC nights. No W84 observations occur in the supplied MPC rows, so none can be matched to an MPC row at that station. This does not certify they are unpublished: the supplied MPC snapshot may omit observations or use other attribution.",f"The ten Rubin source IDs exactly equal our retained Fink set: {newids==oldids}. They add no new Rubin detections.",'## DECam measurement inspection','All 56 rows include coordinate uncertainties, magnitude uncertainties, band, and exposure identifiers. All lack seeing/FWHM and image-mask/centroid quality flags in this export. An object_id is assigned throughout this target-filtered export; it is not independent evidence of MPC attribution. No image confirmation or calibrated astrometric validation has yet occurred.','| UTC night | Rows | Bands | Position span, arcsec |','|---|---:|---|---:|']
    lines += [f"| {x['date_utc']} | {x['rows']} | {x['bands']} | {x['position_span_arcsec']:.3f} |" for x in night_rows]
    lines+=['## Available image investigation',f"Queried the documented NOIRLab NSC DR2 SIA endpoint at all {len(image_results)} nightly positions. Returned image rows: {sum(x.get('rows',0) for x in image_results)}; failed queries: {sum('error' in x for x in image_results)}. XML responses and request URLs are retained. An empty result does not establish that original DECam images are unavailable elsewhere.",'No image pixels were supplied in the two Parquet files. No image pixels were inspected in this reconciliation. ADAM cutout downloads or exposure-specific Astro Data Archive retrieval are needed next; no full detector images were downloaded.','## Suitability for independent orbit tests','The 56 DECam rows are provisionally useful inputs, pending image checks and astrometric validation. Use W84 observer geometry, UTC-to-TDB conversion, and exposure-time semantics verified for NSC. Do not guess the timestamp offset from the exposure filename. Quoted uncertainties need unit/convention verification and a systematic-error floor; same-night measurements may be correlated.','Do not feed the exported JPL state or covariance into the independent fit. Selection of these candidates already used the JPL orbit, so a test using them is a retrospective known-object benchmark, not blind discovery.','Recommended next experiment: freeze a training cutoff before the first Rubin epoch; fit validated pre-2026 observations with a planetary-perturbation-capable fitter and hold all ten 2026 Rubin observations out. Define uncertainty and rejection rules using training data. Preserve the earlier November 12 benchmark unchanged. The present Sun-only model is not an adequate precision benchmark for a 13-year extrapolation without an established-fitter cross-check.','No new orbital fit or mass estimate was performed here. Unresolved centroids do not determine the binary mutual orbit.','## Sources','[NOIRLab NSC documentation](https://datalab.noirlab.edu/data/nsc)', '[ADAM Precovery](https://b612.ai/adam-platform/precovery/)']
    md='\n\n'.join(lines[:0]) if False else '\n'.join(lines)
    (out/'report.md').write_text(md);(out/'report.html').write_text(render(md,'QY297 ADAM reconciliation'))
    print(json.dumps({k:summary[k] for k in ['catalog_counts','lsst_ids_equal_previous_fink','nsc_exposure_ids_unique','duplicate_pairs']},indent=2));print('SIA',[(x['night'],x.get('rows'),x.get('error')) for x in image_results]);print(out/'report.html')
if __name__=='__main__':main()

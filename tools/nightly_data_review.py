#!/usr/bin/env python3
"""Small, explicit-watchlist Fink freshness review; no bulk download or discovery scan."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone
import hashlib
from html import escape
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import urllib.request
import urllib.error
from astropy.time import Time

ROOT=Path(__file__).resolve().parents[1]
TARGETS=[('PGC 766016','171141216913588260'),('Quasar crossmatch','313774266976305153'),
         ('Science-image high','313862200773574662'),('AT 2019hkw','170653056044630027')]
MOVERS=['2001 QY297','2014 WV203','2013 CR7','2026 ED138']
API='https://api.lsst.fink-portal.org/api/v1/'


def keyed(rows):
    by={}
    for r in rows:
        sid=str(r.get('r:diaSourceId',''))
        if sid:by.setdefault(sid,set()).add(json.dumps(r,sort_keys=True,separators=(',',':')))
    return by


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report-date',required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    day=datetime.strptime(args.report_date,'%Y-%m-%d').date();z=ZoneInfo('America/New_York')
    start=datetime.combine(day-timedelta(days=1),time(17),z).astimezone(timezone.utc)
    stop=datetime.combine(day,time(9),z).astimezone(timezone.utc)
    out=args.output;out.mkdir(parents=True,exist_ok=False);data=out/'data';data.mkdir()
    jobs=[('November statistics','statistics-202611.json','statistics',{'date':'202611'},ROOT/'data/snapshots/2026-11-20/statistics-202611.json')]
    jobs += [(label,f'object-{sid}.json','sources',{'diaObjectId':sid},ROOT/f'data/snapshots/2026-11-20/object-{sid}.json') for label,sid in TARGETS]
    for name in MOVERS:
        old=ROOT/'reports/2026/11/20/qy297-investigation/fink-name.json' if name=='2001 QY297' else ROOT/f'data/snapshots/2026-11-20/sso-{name.replace(" ","_")}.json'
        jobs.append((name,f'sso-{name.replace(" ","_")}.json','sso',{'n_or_d':name},old))
    def fetch(job):
        label,filename,endpoint,params,old=job
        query={'output-format':'json',**params};record={'label':label,'endpoint':API+endpoint,'parameters':query,'file':filename,'requested_UTC':datetime.now(timezone.utc).isoformat()}
        try:
            req=urllib.request.Request(API+endpoint,data=json.dumps(query).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=45) as response:raw=response.read();record['HTTP_status']=response.status
            rows=json.loads(raw)
            if not isinstance(rows,list):raise ValueError('Expected a JSON row list')
            (data/filename).write_bytes(raw);record.update(status='fresh',rows=len(rows),sha256=hashlib.sha256(raw).hexdigest())
            if endpoint=='statistics':
                record['published_nights']=[{'night':r.get('f:night'),'alerts':r.get('f:alerts'),'visits':r.get('f:visits')} for r in rows]
                record['latest_published_night']=max([str(r.get('f:night','')) for r in rows],default=None)
            else:
                previous=json.loads(old.read_text()) if old.is_file() else []
                before,after=keyed(previous),keyed(rows)
                record.update(baseline_file=str(old.relative_to(ROOT)) if old.is_file() else None,
                    unique_source_ids=len(after),added_source_ids=sorted(after.keys()-before.keys()),removed_source_ids=sorted(before.keys()-after.keys()),
                    revised_source_ids=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]))
                valid=[r for r in rows if r.get('r:midpointMjdTai') is not None and r.get('r:timeWithdrawnMjdTai') is None]
                epochs=Time([r['r:midpointMjdTai'] for r in valid],format='mjd',scale='tai').utc if valid else []
                record['latest_observation_UTC']=str(max(epochs).isot) if valid else None
                record['last_night_nonwithdrawn_source_ids']=sorted({str(r['r:diaSourceId']) for r,t in zip(valid,epochs) if start<=t.to_datetime(timezone.utc)<stop})
        except Exception as exc:
            record.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        print(label,record['status'],record.get('unique_source_ids',record.get('rows','')),record.get('latest_observation_UTC',record.get('latest_published_night','')),flush=True)
        return record
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,jobs))
    payload={'report_date_America_New_York':args.report_date,'generated_UTC':datetime.now(timezone.utc).isoformat(),
      'overnight_window_UTC':[start.isoformat(),stop.isoformat()],'queries':results,
      'local_Pots_overnight_service_and_file_evidence':'pending user-provided logs; no direct host access',
      'scope':'Four extragalactic watchlist histories and four named moving targets. No bulk archive download or new-object scan.'}
    (out/'freshness.json').write_text(json.dumps(payload,indent=2)+'\n')
    lines=[f'# Overnight data review · {args.report_date}', '',f"Generated {payload['generated_UTC']}.",'',
      f'Collection window assessed: {start.isoformat()} through {stop.isoformat()} (17:00–09:00 America/New_York).','',
      'Fresh API retrieval time and observation time are reported separately. Returned histories are sparse; absence of a row does not establish non-observation. No local host collection success is inferred from these queries.','',
      '| Target | Unique returned source IDs | Latest observation UTC | Added / removed / revised IDs | In assessed overnight window |','|---|---:|---|---|---:|']
    for r in results[1:]:
        if r['status']=='fresh':
            lines.append(f"| {r['label']} | {r['unique_source_ids']} | {r['latest_observation_UTC'] or 'no returned observation'} | {len(r['added_source_ids'])} / {len(r['removed_source_ids'])} / {len(r['revised_source_ids'])} | {len(r['last_night_nonwithdrawn_source_ids'])} |")
        else:lines.append(f"| {r['label']} | query failed | unknown | unknown | unknown |")
    stat=results[0]
    lines+=['','## Broker statistics','']
    if stat['status']=='fresh':
        lines += [f"Latest returned published-night key: **{stat['latest_published_night']}**.",'',
          '| Published-night key | Alerts | Visits |','|---|---:|---:|']
        for r in stat['published_nights'][-8:]:lines.append(f"| {r['night']} | {r['alerts']} | {r['visits']} |")
    else:lines+=[stat['error']]
    lines+=['','## Local overnight evidence','',payload['local_Pots_overnight_service_and_file_evidence'],
      '', 'Raw responses, request parameters, retrieval timestamps, response hashes and source-ID changes are retained in this directory. Empty ED138 results mean no history returned by this endpoint; other public astrometry sources remain to investigate.','']
    md='\n'.join(lines);(out/'report.md').write_text(md)
    (out/'report.html').write_text('<!doctype html><meta charset=utf-8><title>Overnight data review</title><pre style="white-space:pre-wrap;font:16px/1.5 system-ui">'+escape(md)+'</pre>')

if __name__=='__main__':main()

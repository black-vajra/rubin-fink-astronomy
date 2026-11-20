#!/usr/bin/env python3
"""Offline first-pass variability triage across the complete historical sources index.

No catalog identification, image-quality validation or discovery claim is made.
The existing archive is opened read-only. Every eligible object/filter is scored.
"""
import argparse,csv,hashlib,itertools,json,math,sqlite3,statistics
from collections import Counter,defaultdict
from datetime import datetime,timezone
from html import escape
from pathlib import Path

WATCH={'171141216913588260','313774266976305153','313862200773574662','170653056044630027'}
EMPTY={'','0','None','null','-1'}

def finite(x):
    try:return math.isfinite(float(x))
    except (TypeError,ValueError):return False

def position(rows):
    xyz=[(math.cos(math.radians(r['dec']))*math.cos(math.radians(r['ra'])),
          math.cos(math.radians(r['dec']))*math.sin(math.radians(r['ra'])),math.sin(math.radians(r['dec']))) for r in rows]
    center=[statistics.mean(v[i] for v in xyz) for i in range(3)]
    norm=math.sqrt(sum(v*v for v in center));center=[v/norm for v in center]
    ra=math.degrees(math.atan2(center[1],center[0]))%360;dec=math.degrees(math.asin(center[2]))
    # atan2 of cross/dot is accurate at subarcsecond separations and crosses RA=0 safely.
    distances=[]
    for v in xyz:
        cross=(v[1]*center[2]-v[2]*center[1],v[2]*center[0]-v[0]*center[2],v[0]*center[1]-v[1]*center[0])
        distances.append(math.degrees(math.atan2(math.sqrt(sum(x*x for x in cross)),sum(v[i]*center[i] for i in range(3))))*3600)
    b=math.degrees(math.asin(math.sin(math.radians(dec))*math.sin(math.radians(27.12825))+math.cos(math.radians(dec))*math.cos(math.radians(27.12825))*math.cos(math.radians(ra-192.85948))))
    return ra,dec,b,max(distances)

def assess(rows,args):
    rows=[r for r in rows if all(finite(r[k]) for k in ('mjd','ra','dec','science','difference')) and 0<=r['ra']<360 and -90<=r['dec']<=90]
    visits=defaultdict(list)
    for r in rows:
        if str(r['visit']) in EMPTY or not r['utc_night']:continue
        visits[(r['utc_night'],str(r['visit']))].append(r)
    if len(visits)<args.min_visits:return None,'too_few_visits'
    night_visits=defaultdict(list)
    for (night,visit),selected in visits.items():
        night_visits[night].append({k:statistics.median(float(r[k]) for r in selected) for k in ('science','difference')})
    if len(night_visits)<args.min_nights:return None,'too_few_nights'
    ra,dec,b,scatter=position(rows)
    if abs(b)<args.min_abs_b:return None,'low_galactic_latitude'
    if scatter>args.max_scatter:return None,'position_scatter'
    nightly=[]
    for day,values in sorted(night_visits.items()):
        nightly.append({'utc_date':day,'visits':len(values),**{k:statistics.median(v[k] for v in values) for k in ('science','difference')}})
    difference=[v['difference'] for v in nightly];science=[v['science'] for v in nightly]
    amplitude=max(difference)-min(difference)
    scale=statistics.median(abs(v) for v in difference)
    fraction=amplitude/max(scale,1.0)
    # This is a ranking heuristic, not significance; the index lacks errors/flags.
    candidate=(fraction>=args.min_fraction and amplitude>=args.min_amplitude)
    return {'object_id':str(rows[0]['object_id']),'band':rows[0]['band'],
            'ra':ra,'dec':dec,'galactic_b_deg':b,'max_offset_arcsec':scatter,
            'sources':len(rows),'visits':len(visits),'nights':len(nightly),
            'difference_amplitude_njy':amplitude,'difference_fraction':fraction,
            'science_amplitude_njy':max(science)-min(science),
            'score':fraction*math.sqrt(len(nightly)), 'passes_variability_cut':candidate,
            'watchlist':str(rows[0]['object_id']) in WATCH,'nightly':nightly,
            'source_ids':[str(r['sid']) for r in rows]},'scored'

def run(args):
    database=args.database.expanduser().resolve()
    if not database.is_file():raise SystemExit(f'Missing archive database: {database}')
    out=args.output.expanduser().resolve()
    if out.exists() and any(out.iterdir()):raise SystemExit('Output directory is not empty; choose a new run directory to preserve prior results.')
    out.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    counts=Counter();scored=[];row_hash=hashlib.sha256()
    try:
        total=con.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
        span=con.execute('SELECT MIN(utc_night),MAX(utc_night) FROM sources').fetchone()
        rows=con.execute('SELECT sid,object_id,band,visit,mjd,utc_night,ra,dec,sso,science,difference FROM sources ORDER BY object_id,band,mjd,sid')
        for oid,group in itertools.groupby(rows,key=lambda r:str(r['object_id'])):
            object_rows=list(group);counts['all_source_rows_read']+=len(object_rows);counts['object_groups_seen']+=1
            for row in object_rows:row_hash.update((json.dumps(list(row),separators=(',',':'))+'\n').encode())
            if counts['object_groups_seen']%10000==0:print(f"Read {counts['all_source_rows_read']:,}/{total:,} rows; grouped {counts['object_groups_seen']:,} objects",flush=True)
            if oid in EMPTY:counts['missing_object_id_rows']+=len(object_rows);continue
            if any(str(r['sso']) not in EMPTY for r in object_rows):counts['known_sso_object_groups']+=1;continue
            for band,by_band in itertools.groupby(object_rows,key=lambda r:r['band']):
                if band not in ('u','g','r','i','z','y'):counts['invalid_filter_groups']+=1;continue
                result,status=assess(list(by_band),args);counts[status]+=1
                if result:scored.append(result)
    finally:con.rollback();con.close()
    assert counts['all_source_rows_read']==total
    candidates=sorted([r for r in scored if r['passes_variability_cut']],key=lambda r:(-r['score'],r['object_id'],r['band']))
    counts['scored_object_filter_groups']=len(scored);counts['candidate_object_filter_groups']=len(candidates)
    counts['candidate_unique_objects']=len({r['object_id'] for r in candidates})
    fields=['object_id','band','sources','visits','nights','ra','dec','galactic_b_deg','max_offset_arcsec','difference_amplitude_njy','difference_fraction','science_amplitude_njy','score','passes_variability_cut','watchlist']
    with (out/'all-scored.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(sorted(scored,key=lambda r:-r['score']))
    with (out/'shortlist.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(candidates)
    summary={'generated_utc':datetime.now(timezone.utc).isoformat(),'database':str(database),'database_bytes':database.stat().st_size,
             'source_index_schema':1,'utc_span':list(span),'ordered_source_rows_sha256':row_hash.hexdigest(),
             'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'parameters':{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
             'counts':dict(counts),'shortlist':candidates[:args.top],'watchlist_scored':[r for r in scored if r['watchlist']],
             'limitations':['Index lacks flux errors, quality flags, template flux, host matches and stellar crossmatches.',
                 'Galactic latitude and positional consistency do not establish an extragalactic identity.',
                 'Score and relative amplitude are heuristic; no statistical significance or false-discovery rate is claimed.',
                 'Alert-only sampling is biased; nondetections and forced photometry are absent. Single-night transients are outside this initial multi-night screen.',
                 'Known SSO labels are excluded, but unlabeled moving objects can remain.']}
    (out/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    lines=['# Archive-wide extragalactic discovery triage','',f"Generated {summary['generated_utc']}",'',
           f"Read {total:,} indexed alerts, spanning {span[0]} through {span[1]}. Every eligible object/filter was scored.",
           f"{len(scored):,} object/filter groups scored; {len(candidates):,} passed the heuristic variability cut, representing {counts['candidate_unique_objects']:,} objects.",'',
           'This is an unclassified review list. No extragalactic discovery is confirmed.','',
           '## Selection fixed for this first pass','',json.dumps(summary['parameters'],indent=2),'',
           'Known SSO-associated object groups excluded. Median measurements per visit, then median visit measurements per UTC night, reduce repeated-row weighting. No error bars or formal significance can be recovered from this index.','',
           '## Ranked review list','', '| Object | Band | Nights | Visits | Difference range nJy | Fraction | Watchlist |', '|---|---|---:|---:|---:|---:|---|']
    for r in candidates[:args.top]:lines.append(f"| {r['object_id']} | {r['band']} | {r['nights']} | {r['visits']} | {r['difference_amplitude_njy']:.1f} | {r['difference_fraction']:.3f} | {r['watchlist']} |")
    lines+=['','## Limitations','']+['- '+s for s in summary['limitations']]+['','## Next pass','',
        'Retrieve original source measurements and flags for shortlisted objects, reject problematic photometry, inspect science/template/difference cutouts, and crossmatch stellar, galaxy and AGN catalogs. Keep known watchlist objects visibly marked. A large science-only rise with stable difference flux is a measurement/reference review flag.','',
        'Full scoring is in all-scored.csv. All passing groups are in shortlist.csv; only the detailed JSON and displayed list are capped by --top.','', '## Selection accounting','',json.dumps(dict(counts),indent=2)]
    text='\n'.join(lines)+'\n';(out/'report.md').write_text(text)
    (out/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>Archive extragalactic triage</title><style>body{font:16px system-ui;margin:2rem}pre{white-space:pre-wrap}</style><pre>'+escape(text)+'</pre>')
    print(f'REPORT: {out / "report.html"}',flush=True)

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',type=Path,default=Path.home()/'rubin-historical-2026/alerts.sqlite3')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--min-visits',type=int,default=3);p.add_argument('--min-nights',type=int,default=3)
    p.add_argument('--min-abs-b',type=float,default=20);p.add_argument('--max-scatter',type=float,default=2)
    p.add_argument('--min-fraction',type=float,default=.2);p.add_argument('--min-amplitude',type=float,default=1000)
    p.add_argument('--top',type=int,default=100)
    return p

if __name__=='__main__':
    p=parser();a=p.parse_args()
    if not all(math.isfinite(v) for v in [a.min_abs_b,a.max_scatter,a.min_fraction,a.min_amplitude]) or a.min_visits<1 or a.min_nights<2 or not 0<=a.min_abs_b<=90 or a.max_scatter<=0 or a.min_fraction<0 or a.min_amplitude<0 or a.top<1:p.error('Invalid selection parameter')
    run(a)

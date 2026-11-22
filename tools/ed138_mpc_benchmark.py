#!/usr/bin/env python3
"""Parse public MPEC 2026-U85 observations and test a training-only ED138 orbit.

Uses native MPC records, not invented Fink source/visit IDs. No catalog orbit
or restricted RSP images enter the fit. Geometric Sun/observer states only.
"""
import argparse,csv,hashlib,io,json,re
from datetime import datetime,timedelta,timezone
from html import unescape,escape
from pathlib import Path
import urllib.parse,urllib.request
import numpy as np
from astropy.time import Time
import physical_orbit_review as model

URL='https://www.minorplanetcenter.net/mpec/K26/K26U85.html'
CUTOFF='2026-06-13'


def parse(raw):
    text=unescape(re.sub('<[^>]+>','',raw.decode()))
    result=[]
    for line_no,line in enumerate(text.splitlines(),1):
        if len(line)!=80 or line[5:12]!='K26ED8D' or line[14]!='C':continue
        year,month,day=line[15:32].split()
        utc=datetime(int(year),int(month),1,tzinfo=timezone.utc)+timedelta(days=float(day)-1)
        h,m,s=map(float,line[32:44].split());ra=15*(h+m/60+s/3600)
        d,m,s=line[44:56].split();dec=(abs(float(d))+float(m)/60+float(s)/3600)*(-1 if d.startswith('-') else 1)
        result.append({'record':line,'text_line':line_no,'station':line[77:80],
            'UTC':utc.isoformat(timespec='milliseconds'),'mjd_tai':float(Time(utc).tai.mjd),
            'ra_deg':ra,'dec_deg':dec,'mag':float(line[65:70]) if line[65:70].strip() else None,'band':line[70]})
    return sorted(result,key=lambda r:r['mjd_tai'])


def geometry(out,epochs,center,tag):
    p={'format':'json','COMMAND':"'10'",'CENTER':repr(center),'EPHEM_TYPE':"'VECTORS'",
       'TLIST':"'"+'\n'.join(f'{x:.12f}' for x in epochs)+"'",'TIME_TYPE':"'TDB'",
       'REF_PLANE':"'FRAME'",'REF_SYSTEM':"'ICRF'",'OUT_UNITS':"'AU-D'",'VEC_TABLE':"'2'",
       'VEC_CORR':"'NONE'",'CSV_FORMAT':"'YES'",'OBJ_DATA':"'NO'"}
    path=out/(tag+'.json')
    if not path.exists():
        with urllib.request.urlopen('https://ssd.jpl.nasa.gov/api/horizons.api?'+urllib.parse.urlencode(p),timeout=45) as response:body=json.load(response)
        if 'error' in body:raise ValueError(body['error'])
        path.write_text(json.dumps({'requested_UTC':datetime.now(timezone.utc).isoformat(),'parameters':p,'response':body},indent=2)+'\n')
    return model.vectors(path,epochs,center)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mpec-html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    raw=a.mpec_html.read_bytes();(out/'MPEC-2026-U85.html').write_bytes(raw)
    records=parse(raw)
    if len(records)!=74 or sum(r['station']=='X05' for r in records)!=30:
        raise ValueError('Unexpected circular content: review parser before fitting')
    (out/'observations.json').write_text(json.dumps(records,indent=2)+'\n')
    with (out/'observations.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=[k for k in records[0] if k!='record']);writer.writeheader();writer.writerows([{k:v for k,v in r.items() if k!='record'} for r in records])
    selected=[r for r in records if r['station']=='X05']
    train=np.array([i for i,r in enumerate(selected) if r['UTC'][:10]<CUTOFF]);test=np.array([i for i,r in enumerate(selected) if r['UTC'][:10]>=CUTOFF])
    plan={'declared_before_scoring_UTC':datetime.now(timezone.utc).isoformat(),'target':'2026 ED138','source':URL,
          'source_sha256':hashlib.sha256(raw).hexdigest(),'training_UTC_before':CUTOFF,
          'test_text_lines':[selected[i]['text_line'] for i in test],'fixed_radius_arcsec':60,
          'assumed_coordinate_sigma_arcsec':model.SIGMA,'initial_distance_grid_AU':model.SEEDS,
          'excluded_from_fitting':'All post-cutoff positions; all W84 precoveries; published orbital elements in circular; restricted RSP images/catalogs.'}
    (out/'test-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    tai=Time([r['mjd_tai'] for r in selected],format='mjd',scale='tai');epochs=tai.tdb.jd;dt=epochs-epochs[0]
    observer=-geometry(out,epochs,'X05@399','sun-from-observer')[:,:3]
    sv=geometry(out,epochs,'500@0','sun-barycentric')[:,3:]
    ra=np.radians([r['ra_deg'] for r in selected]);dc=np.radians([r['dec_deg'] for r in selected])
    n=np.c_[np.cos(ra)*np.cos(dc),np.sin(ra)*np.cos(dc),np.sin(dc)]
    east=np.c_[-np.sin(ra),np.cos(ra),np.zeros(len(ra))];north=np.cross(n,east)
    print('ED138 public records:',len(records),'Rubin:',len(selected),'training:',len(train),'withheld:',len(test),flush=True)
    state,trials=model.fit_training(dt[train],observer[train],sv[train],n[train],east[train],north[train])
    payload={'generated_UTC':datetime.now(timezone.utc).isoformat(),'source':URL,'all_records':len(records),
             'Rubin_records':len(selected),'Rubin_dates':len({r['UTC'][:10] for r in selected}),
             'training_points':len(train),'training_dates':len({selected[i]['UTC'][:10] for i in train}),
             'test_plan':plan,'trials':trials,'withheld':[]}
    if state is None:
        payload['status']='No converged bound fit; retained all trial outcomes'
        (out/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
        raise SystemExit('No converged bound fit; see retained results.json')
    pr=model.predict(state,dt,observer,sv);err=np.arctan2(np.linalg.norm(np.cross(pr,n),axis=1),np.sum(pr*n,axis=1))*model.ARC
    j=model.tangent_jacobian(state,dt,observer,sv,n,east,north);J=j[train].reshape(-1,6)/model.SIGMA
    _,singular,vt=np.linalg.svd(J,full_matrices=False);cov=vt.T@np.diag(singular**-2)@vt
    payload.update(state=state.tolist(),reference_TDB_JD=float(epochs[0]),elements=model.elements(state),
        training_max_error_arcsec=float(err[train].max()),training_RMS_position_error_arcsec=float(np.sqrt(np.mean(err[train]**2))),
        covariance_state=cov.tolist())
    for i in test:
        pc=j[i]@cov@j[i].T;axes=np.sqrt(np.maximum(np.linalg.eigvalsh(pc),0)[::-1]*5.991464547)
        payload['withheld'].append({'text_line':selected[i]['text_line'],'UTC':selected[i]['UTC'],
            'station':'X05','band':selected[i]['band'],'error_arcsec':float(err[i]),
            'inside_60_arcsec':bool(err[i]<=60),'formal_95pct_prediction_semiaxes_arcsec':axes.tolist()})
    (out/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
    lines=['# 2026 ED138 · public astrometry benchmark','',payload['generated_UTC'],'',
        '**Historical benchmark, not new overnight observations.** Native public MPC observations were retrieved successfully; the Fink query failure is not an absence-of-astrometry result.','',
        f"Parsed **74** MPC observations: **44 W84** DECam precoveries and **30 X05** Rubin positions on **{payload['Rubin_dates']}** dates. "
        'Only the Rubin subset is fitted here; the precoveries are retained for later work. No Fink alert IDs or visit IDs are invented.','',
        f"Training cutoff fixed before numerical scoring: **UTC < {CUTOFF}**. "
        f"Training: **{len(train)} positions on {payload['training_dates']} dates**; withheld: **{len(test)} positions**. "
        'All trial outcomes are retained. Published target orbital elements and all withheld positions are excluded from initialization and optimization.','',
        'Model: existing six-state heliocentric Sun-only fitter; Rubin observer motion and iterated light travel time. '
        'Uniform assumed 0.15 arcsec per-coordinate errors; existing fixed 60 arcsec search gate. '
        'Retrospective known-object test, not a blind discovery or a replacement catalog orbit.','',
        '| Withheld UTC | Band | Miss (arcsec) | Inside 60 arcsec? | Formal 95% prediction semiaxes (arcsec) |','|---|---|---:|---|---|']
    for r in payload['withheld']:lines.append(f"| {r['UTC']} | {r['band']} | {r['error_arcsec']:.3f} | {r['inside_60_arcsec']} | {r['formal_95pct_prediction_semiaxes_arcsec'][0]:.3f} × {r['formal_95pct_prediction_semiaxes_arcsec'][1]:.3f} |")
    el=payload['elements']
    lines+=['',f"Training position RMS: **{payload['training_RMS_position_error_arcsec']:.4f} arcsec**; maximum **{payload['training_max_error_arcsec']:.4f} arcsec**.",
        '',f"Exploratory heliocentric elements at JD {epochs[0]:.9f} TDB: a={el['a_AU']:.4f} AU, e={el['e']:.4f}. "
        'These are not directly comparable to quoted barycentric elements without transforming definitions and epochs.','',
        '## Limits and next steps','',
        'This initial model omits planetary perturbations, mutual/body-specific motion, correlated astrometric errors and image-level biases. '
        'The MPC rounded positions lack per-observation uncertainties here. Formal ellipses are conditional on an assumed error model and one local branch, '
        'not calibrated coverage. This report neither identifies all orbit solutions nor measures size/mass or a resonant classification.','',
        'Next: compare with an established orbit fitter and a planetary force model, then consider independent W84 precoveries with station-specific geometry. '
        'The restricted Rubin RSP image/catalog release is not used. Public MPC astrometry is a distinct data product.','',
        'Source: '+URL,'Rubin data-product access distinction: https://prompt-products.lsst.io/products/2026-ED138/index.html','']
    md='\n'.join(lines);(out/'report.md').write_text(md);(out/'report.html').write_text('<!doctype html><meta charset=utf-8><title>ED138 public astrometry benchmark</title><pre style="white-space:pre-wrap;font:16px/1.5 system-ui">'+escape(md)+'</pre>')
    print('ED138 withheld errors:',[round(x['error_arcsec'],4) for x in payload['withheld']],flush=True)

if __name__=='__main__':main()

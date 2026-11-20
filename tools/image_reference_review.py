#!/usr/bin/env python3
"""Review existing watchlist metadata and optionally retrieve nine PGC FITS cutouts."""
import argparse,hashlib,io,json,math,statistics,urllib.request
from datetime import datetime,timezone
from html import escape
from pathlib import Path
from astropy.time import Time

API='https://api.lsst.fink-portal.org/api/v1/cutouts'
TARGETS=['171141216913588260','313862200773574662']

def execute(a):
    out=a.output.resolve()
    if out.exists() and any(out.iterdir()):raise SystemExit('Choose a fresh output directory to preserve earlier investigations.')
    out.mkdir(parents=True,exist_ok=True)
    lines=['# Science/reference investigation','',f'Generated {datetime.now(timezone.utc).isoformat()}','',
           'Existing alert measurements only. New observing data are not required for this review.','']
    results={'histories':{},'cutouts':[]};pgc=[]
    for oid in TARGETS:
        path=a.data/f'object-{oid}.json'
        raw=json.loads(path.read_text())
        rows=sorted({str(r['r:diaSourceId']):r for r in raw if r.get('r:band')=='i' and r.get('r:midpointMjdTai') is not None and '2026-10-30'<=Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot[:10]<='2026-11-15'}.values(),key=lambda r:r['r:midpointMjdTai'])
        if oid==TARGETS[0]:pgc=rows
        lines += [f'## {oid} · i band','', '| UTC | Detector | Science nJy | Template nJy | Difference nJy | PSF trace (native units) | True flags |', '|---|---:|---:|---:|---:|---:|---|']
        retained=[]
        for r in rows:
            utc=Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot
            flags=[k[2:] for k,v in r.items() if v is True and ('flag' in k.lower() or k=='r:isDipole')]
            trace=None if r.get('r:ixxPSF') is None or r.get('r:iyyPSF') is None else r['r:ixxPSF']+r['r:iyyPSF']
            def flux(k):return 'unavailable' if r.get('r:'+k) is None else f"{r['r:'+k]:,.0f}"
            lines.append(f"| {utc} | {r.get('r:detector')} | {flux('scienceFlux')} | {flux('templateFlux')} | {flux('psfFlux')} | {trace if trace is not None else 'unavailable'} | {', '.join(flags) or 'none returned true'} |")
            retained.append({'utc':utc,'diaSourceId':str(r['r:diaSourceId']),'detector':r.get('r:detector'),
                'scienceFlux':r.get('r:scienceFlux'),'scienceFluxErr':r.get('r:scienceFluxErr'),
                'templateFlux':r.get('r:templateFlux'),'templateFluxErr':r.get('r:templateFluxErr'),
                'psfFlux':r.get('r:psfFlux'),'psfFluxErr':r.get('r:psfFluxErr'),
                'psf_trace_native':trace,'true_flags':flags,
                **{k[2:]:v for k,v in r.items() if k.startswith('r:template')}})
        results['histories'][oid]={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':retained}
        lines+=['','PSF trace is a descriptive shape proxy in returned native units, not a calibrated seeing measurement. Missing or false flags do not certify photometric validity.','']
    earlier=next(r for r in pgc if Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot.startswith('2026-11-11'))
    latest=pgc[-1]
    changes={f:latest['r:'+f]-earlier['r:'+f] for f in ['scienceFlux','templateFlux','psfFlux']}
    results['pgc_nov11_to_nov15']=changes
    lines+=['## PGC November 11 → November 15','',f"Science change {changes['scienceFlux']:+,.0f} nJy; template change {changes['templateFlux']:+,.0f} nJy; difference change {changes['psfFlux']:+,.0f} nJy.",'',
        'The template measurement changes almost as much as the science measurement. This motivates reference/measurement/calibration review. It does not establish which effect caused the change. Measurements on science and template share fitting context and are not independent flare confirmations.','']
    selected=[r for r in pgc if Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot[:10] in {'2026-11-11','2026-11-13','2026-11-15'}]
    plotted={}
    if a.fetch_cutouts:
        from astropy.io import fits
        for r in selected:
            sid=str(r['r:diaSourceId']);day=Time(r['r:midpointMjdTai'],format='mjd',scale='tai').utc.isot[:10]
            for kind in ['Science','Template','Difference']:
                params={'diaSourceId':sid,'kind':kind,'output-format':'FITS'}
                item={'diaSourceId':sid,'utc_date':day,'kind':kind,'request':params}
                try:
                    filename=f'{day}-{sid}-{kind}.fits'
                    cached=a.cutout_cache/filename if a.cutout_cache else None
                    if cached and cached.is_file():
                        blob=cached.read_bytes();item['retrieval_source']='Previously downloaded FITS cache'
                    else:
                        req=urllib.request.Request(API,data=json.dumps(params).encode(),headers={'Content-Type':'application/json'})
                        with urllib.request.urlopen(req,timeout=25) as response:blob=response.read()
                        item['retrieval_source']='Fink API'
                    with fits.open(io.BytesIO(blob),ignore_missing_simple=True) as hdus:
                        images=[(i,h) for i,h in enumerate(hdus) if h.data is not None and getattr(h.data,'ndim',0)==2 and h.name.upper() not in {'MASK','VARIANCE'}]
                        if not images:raise ValueError('No science image plane in response')
                        index,plane=images[0];array=plane.data.copy();header=dict(plane.header)
                        item.update(image_hdu=index,hdu_names=[h.name for h in hdus],shape=list(array.shape),
                                    headers={k:str(v) for k,v in header.items() if k not in {'COMMENT','HISTORY',''}},
                                    has_variance=any(h.name.upper()=='VARIANCE' or h.header.get('UTYPE')=='VarianceUncertainty' for h in hdus),
                                    has_mask=any(h.name.upper() in {'MASK','MASKPLANE'} for h in hdus),
                                    wcs_ctype_present=('CTYPE1' in plane.header and 'CTYPE2' in plane.header),
                                    uncertainty_types={h.name:str(h.header.get('UTYPE','unspecified')) for h in hdus if h.name.upper() in {'UNCERT','VARIANCE'}})
                    (out/filename).write_bytes(blob)
                    item.update(status='downloaded and FITS parsed',file=filename,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
                    plotted[day,kind]=array
                except Exception as e:item.update(status='unavailable',error=f'{type(e).__name__}: {e}')
                results['cutouts'].append(item);print(f"{day} {kind}: {item['status']}",flush=True)
        if plotted:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            fig,axes=plt.subplots(3,3,figsize=(10,10))
            for i,day in enumerate(['2026-11-11','2026-11-13','2026-11-15']):
                for j,kind in enumerate(['Science','Template','Difference']):
                    ax=axes[i,j];array=plotted.get((day,kind));ax.set_title(day+' '+kind,fontsize=9)
                    if array is not None:
                        finite=array[np.isfinite(array)]
                        if finite.size:ax.imshow(array,origin='lower',cmap='gray',vmin=np.percentile(finite,1),vmax=np.percentile(finite,99))
                    else:ax.text(.5,.5,'Unavailable',ha='center',transform=ax.transAxes)
                    ax.set_xticks([]);ax.set_yticks([])
            fig.suptitle('Native cutouts · separate percentile scales · not aligned for photometry',fontsize=11)
            fig.tight_layout();fig.savefig(out/'cutout-contact-sheet.png',dpi=160);plt.close(fig)
    # Compare shape proxies without assigning a seeing FWHM or relying on disputed schema units.
    lines+=['## PSF and reference metadata comparison','',
            '| Object | PSF trace Nov 11 | Nov 13 | Nov 15 | Nov 15 / Nov 11 | Same reported template date summary? |',
            '|---|---:|---:|---:|---:|---|']
    for oid,entry in results['histories'].items():
        picked=[next((r for r in entry['rows'] if r['utc'].startswith(day)),None) for day in ['2026-11-11','2026-11-13','2026-11-15']]
        if all(picked):
            traces=[r['psf_trace_native'] for r in picked]
            same=len({tuple(r.get(k) for k in ['templateMjdMin','templateMjdMax','templateMjdMean','templateVersion']) for r in picked})==1
            lines.append(f"| {oid} | {traces[0]:.6f} | {traces[1]:.6f} | {traces[2]:.6f} | {traces[2]/traces[0]:.3f} | {same} |")
    lines+=['','The reported PSF trace increases alongside science/template flux in both objects. This supports investigating image quality and forced-PSF measurement effects. The three matching template date summaries do not prove identical coadd pixels, weights, detector projection or photometric fitting. A detector ID alone does not establish a cause.','',
            '## Image retrieval','',f"{sum(r['status'].startswith('downloaded') for r in results['cutouts'])} of {len(results['cutouts'])} requested FITS cutouts retrieved and parsed.",
            'Contact sheet, when present, uses native pixel orientation and independent percentile stretches. It cannot establish a brightness trend, and images have not been aligned, PSF-matched or photometrically recalibrated.','',
            'FITS extension names, uncertainty types and WCS CTYPE presence are recorded per cutout. Missing CTYPE keywords require resolving the documented WCS/orientation issue before cross-visit sky alignment. Mask bits require their actual definitions; a nonzero mask value is not automatically a bad pixel.','',
            '## Remaining interpretation gates','',
            'Check FITS WCS/units, variance and masks, confirm usable template provenance, align sky coordinates and compare with PSF-matched or aperture-consistent measurements. Inspect neighboring objects and extended host light. Do not treat detector changes alone as a demonstrated cause.','',
            'Photometry documentation: https://doc.lsst.fink-broker.org/data/photometry/',
            'Cutout documentation: https://doc.lsst.fink-broker.org/services/api/imagesearch/']
    text='\n'.join(lines)+'\n';(out/'report.md').write_text(text)
    (out/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>Image reference investigation</title><style>body{font:16px system-ui;margin:2rem}pre{white-space:pre-wrap}img{max-width:100%}</style><pre>'+escape(text)+'</pre>'+('<img src="cutout-contact-sheet.png">' if plotted else ''))
    (out/'measurements.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    print('REPORT:',out/'report.html')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fetch-cutouts',action='store_true');p.add_argument('--cutout-cache',type=Path);execute(p.parse_args())

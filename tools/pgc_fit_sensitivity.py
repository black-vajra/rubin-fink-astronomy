#!/usr/bin/env python3
"""Diagnostic fit-choice sensitivity on retained PGC cutouts; not calibrated photometry."""
import argparse,hashlib,json
from datetime import datetime,timezone
from html import escape
from pathlib import Path
import numpy as np
from astropy.io import fits
from psf_reference_diagnostic import load,kernel_image

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cutouts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
results=[]
for path in sorted(a.cutouts.glob('*.fits')):
    image,head,psf,variance,mask=load(path)
    center=(head['CRPIX1']-1,head['CRPIX2']-1);y,x=np.indices(image.shape);dx=x-center[0];dy=y-center[1]
    kernel=kernel_image(psf,image.shape,center)
    with fits.open(path) as hdus:
        schema_cards=[k for h in hdus for k in h.header if k.startswith('MP_') or k.startswith('MSKN')]
    trials=[]
    for radius in [6,10,14]:
        keep=(dx*dx+dy*dy<=radius*radius)&np.isfinite(image)&np.isfinite(variance)&(variance>0)&np.isfinite(kernel)
        for background in ['constant','plane']:
            cols=[kernel[keep],np.ones(keep.sum())]
            if background=='plane':cols += [dx[keep]/radius,dy[keep]/radius]
            design=np.column_stack(cols)
            for weighting in ['uniform','variance']:
                weight=np.ones(keep.sum()) if weighting=='uniform' else 1/np.sqrt(variance[keep])
                coef,_,rank,_=np.linalg.lstsq(design*weight[:,None],image[keep]*weight,rcond=None)
                if rank!=design.shape[1]:raise ValueError('Rank-deficient fit')
                trials.append({'radius_pixels':radius,'background':background,'weighting':weighting,
                    'amplitude_nJy':float(coef[0]),'fit_pixels':int(keep.sum()),
                    'nonzero_mask_pixels':int(np.count_nonzero(mask[keep]))})
    values=np.array([t['amplitude_nJy'] for t in trials])
    results.append({'file':path.name,'kind':path.stem.split('-')[-1],'UTC_date':path.name[:10],
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mask_schema_cards_found':schema_cards,
        'amplitude_min_nJy':float(values.min()),'amplitude_median_nJy':float(np.median(values)),
        'amplitude_max_nJy':float(values.max()),'trials':trials})
payload={'generated_UTC':datetime.now(timezone.utc).isoformat(),'status':'unmasked image-model sensitivity diagnostic',
    'grid':{'radii_pixels':[6,10,14],'backgrounds':['constant','plane'],'weights':['uniform','inverse_variance']},
    'measurements':results,'limitations':['Nonzero mask bits are counted, not interpreted or rejected: the supplied FITS omit a mask-bit dictionary.',
        'No nuclear/host decomposition, reference matching, inter-pixel covariance or independent photometric calibration.',
        'The spread across choices is model sensitivity, not a statistical uncertainty or a confidence interval.',
        'Same archived November 11/13/15 images; no new observations or flare confirmation.']}
(a.output/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
lines=['# PGC 766016 · image-fit sensitivity','',payload['generated_UTC'],'',
    '**Archived-image diagnostic only.** Twelve fixed choices per cutout: fit radius 6/10/14 pixels, constant/planar background, uniform/inverse-variance weighting. Supplied PSFs retain total-flux normalization. Finite image and positive variance pixels are used; masks are not semantically decoded.','',
    '| UTC date | Image | Minimum amplitude nJy | Median nJy | Maximum nJy |','|---|---|---:|---:|---:|']
for r in results:lines.append(f"| {r['UTC_date']} | {r['kind']} | {r['amplitude_min_nJy']:,.0f} | {r['amplitude_median_nJy']:,.0f} | {r['amplitude_max_nJy']:,.0f} |")
lines += ['','These amplitudes measure a chosen PSF-plus-background model, not total galaxy luminosity. Cross-date ranges may reflect source structure, PSF/background choices, subtraction residuals or calibration. No significant-change claim follows from this grid.','',
    '## Remaining measurement gate','',
    'All nine retained FITS products were checked for MP_ or MSKN mask-schema cards. Their absence leaves a mask-interpretation dependency; generic defaults are not assigned to these particular packets without provenance. Image-level photometric validation remains incomplete.','',
    '## Limitations','']+['- '+x for x in payload['limitations']]
md='\n'.join(lines)+'\n';(a.output/'report.md').write_text(md);(a.output/'report.html').write_text('<!doctype html><meta charset=utf-8><title>PGC fit sensitivity</title><pre style="white-space:pre-wrap;font:16px/1.5 system-ui">'+escape(md)+'</pre>')
for r in results:
    if r['kind']=='Difference':print(r['UTC_date'],r['amplitude_min_nJy'],r['amplitude_median_nJy'],r['amplitude_max_nJy'])

#!/usr/bin/env python3
"""Diagnostic of PSF-dependent photometry; not validated nuclear-flux measurement.

Mask definitions are not in the retrieved products. No pixel bits are decoded.
No cross-epoch subtraction, astrometric alignment, or significance claim is made.
"""
import argparse,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone
from html import escape
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter,map_coordinates

def load(path):
    with fits.open(path) as h:
        image=np.asarray(h[0].data,dtype=float).copy();head=h[0].header.copy()
        psf=np.asarray(h['PSFIMAGE'].data,dtype=float).copy()
        variance=np.asarray(h['UNCERT'].data,dtype=float).copy()
        mask=np.asarray(h['MASKPLANE'].data).copy()
        if h['UNCERT'].header.get('UTYPE')!='VarianceUncertainty':raise ValueError('Expected variance, not standard deviation')
        if head.get('BUNIT','').strip()!='nJy':raise ValueError('Unexpected flux units')
    return image,head,psf,variance,mask

def kernel_image(psf,shape,center):
    # Normalize the entire PSF before interpolation/cropping, preserving total-flux convention.
    psf=psf/psf.sum();y,x=np.indices(shape,dtype=float)
    coords=[y-center[1]+(psf.shape[0]-1)/2,x-center[0]+(psf.shape[1]-1)/2]
    return map_coordinates(psf,coords,order=3,mode='constant',cval=0.)

def fit(image,psf,center,radius=10):
    y,x=np.indices(image.shape);select=(x-center[0])**2+(y-center[1])**2<=radius**2
    model=kernel_image(psf,image.shape,center)
    select &= np.isfinite(image)&np.isfinite(model)
    design=np.column_stack([model[select],np.ones(select.sum())])
    coef,_,_,_=np.linalg.lstsq(design,image[select],rcond=None)
    residual=image[select]-design@coef
    return {'fitted_amplitude_njy':float(coef[0]),'constant_background_njy_pixel':float(coef[1]),'rms_residual_njy_pixel':float(np.sqrt(np.mean(residual**2))),'pixels':int(select.sum())}

def rms(psf):
    p=psf/psf.sum();y,x=np.indices(p.shape);cx=(x*p).sum();cy=(y*p).sum()
    return float(np.sqrt((((x-cx)**2+(y-cy)**2)*p).sum()/2))

def broadening(image,psf,center):
    p=np.pad(psf,25);p/=p.sum();rows=[]
    for sigma in [0.,1.,2.,3.,4.,5.]:
        smooth=image.copy() if sigma==0 else gaussian_filter(image,sigma,mode='reflect',truncate=4)
        model=p.copy() if sigma==0 else gaussian_filter(p,sigma,mode='constant',truncate=4)
        rows.append({'added_gaussian_sigma_pixels':sigma,**fit(smooth,model,center)})
    return rows

def main(a):
    out=a.output;out.mkdir(parents=True,exist_ok=False)
    measurements=[]
    for path in sorted(a.cutouts.glob('*.fits')):
        image,head,psf,var,mask=load(path)
        center=(float(head['CRPIX1'])-1,float(head['CRPIX2'])-1)
        y,x=np.indices(image.shape);dx=x-center[0];dy=y-center[1]
        matrix=np.array([[head['PC1_1']*head['CDELT1'],head['PC1_2']*head['CDELT1']],[head['PC2_1']*head['CDELT2'],head['PC2_2']*head['CDELT2']]])
        east,north=np.einsum('ij,jkl->ikl',matrix,np.array([dx,dy]))*3600
        radius=np.hypot(east,north)
        ann=(radius>=2.3)&(radius<=2.7)&np.isfinite(image)
        sky=float(np.median(image[ann]))
        apertures={}
        for rad in [.8,1.2,1.6,2.]:
            select=(radius<=rad)&np.isfinite(image)&np.isfinite(var)&(var>0)
            apertures[str(rad)]={'sum_minus_local_median_njy':float(np.sum(image[select]-sky)),'pixels':int(select.sum()),'mask_nonzero_pixels':int(np.count_nonzero(mask[select]))}
        measurements.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'kind':path.stem.split('-')[-1],'date':path.name[:10],'shape':list(image.shape),'psf_sum':float(psf.sum()),'psf_rms_pixels':rms(psf),
            'fit_with_own_psf':fit(image,psf,center),'apertures_arcsec':apertures,'mask_values':[int(x) for x in np.unique(mask)],'plate_singular_values_arcsec':(np.linalg.svd(matrix,compute_uv=False)*3600).tolist()})
    reference=next(a.cutouts.glob('2026-11-15-*-Template.fits'))
    image,head,psf,_,_=load(reference);center=(head['CRPIX1']-1,head['CRPIX2']-1)
    experiment=broadening(image,psf,center)
    # A flux-conserving point source provides a control for interpolation, smoothing and fitting.
    point=kernel_image(np.pad(psf,25),image.shape,center)*1e6+100
    control=broadening(point,psf,center)
    control_error=max(abs(x['fitted_amplitude_njy']/1e6-1) for x in control)
    if control_error>.02:raise RuntimeError(f'Point-source control failed: {control_error}')
    payload={'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'diagnostic; not independently validated photometry',
        'measurements':measurements,'fixed_reference_experiment':experiment,'point_source_control':control,'point_control_max_fractional_error':control_error,
        'method':'Same November 15 template image, flux-conserving Gaussian blur and matching blurred PSF, unweighted PSF-plus-constant fit within 10 pixels at fixed supplied CRPIX position.',
        'limitations':['Mask-to-bit mapping is absent; masks are inventoried but not decoded or applied. Apertures and fits are diagnostic only.',
            'Fixed annulus and fitted constants can absorb host light; changing fitted PSF amplitude is not changing total galaxy light.',
            'Gaussian blur is a controlled mechanism demonstration, not a reproduction of the Rubin pipeline or the actual inter-epoch PSFs.',
            'No independent zeropoint check, background validation, covariance model, PSF matching across epochs, or nuclear/host decomposition.',
            'Aperture metric uses the local header linear matrix only; no global WCS repair is asserted. No aperture error bars or cross-epoch significance claimed.']}
    (out/'diagnostic.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    lines=['# PGC image/reference diagnostic — work in progress','',payload['generated_utc'],'',
        '**Diagnostic only: mask semantics and independent photometric validation remain unresolved.**','',
        '## Supplied PSF kernels','', '| UTC date | Science PSF RMS, pixels | Template PSF RMS, pixels | Difference PSF RMS, pixels |','|---|---:|---:|---:|']
    for day in ['2026-11-11','2026-11-13','2026-11-15']:
        d={r['kind']:r['psf_rms_pixels'] for r in measurements if r['date']==day}
        lines.append(f"| {day} | {d['Science']:.3f} | {d['Template']:.3f} | {d['Difference']:.3f} |")
    lines+=['','The actual supplied science PSF kernels broaden across visits, while template PSF kernels remain comparatively similar. These are kernel second moments, not calibrated seeing FWHM.','',
        '## Controlled experiment on one unchanged template','',payload['method'],'',
        '| Added Gaussian sigma, pixels | Fitted amplitude, nJy | Relative to no added blur |','|---:|---:|---:|']
    for r in experiment:lines.append(f"| {r['added_gaussian_sigma_pixels']:.1f} | {r['fitted_amplitude_njy']:,.0f} | {r['fitted_amplitude_njy']/experiment[0]['fitted_amplitude_njy']:.3f} |")
    lines+=['',f'Point-source control maximum fractional amplitude error: {control_error:.6f}.','',
        'Any amplitude response in the unchanged real template demonstrates model/measurement sensitivity in this experiment. It does not establish that the Rubin pipeline made the same measurement or that this explains the complete observed trend.','',
        '## Limits','']+['- '+s for s in payload['limitations']]
    text='\n'.join(lines)+'\n';(out/'report.md').write_text(text);(out/'report.html').write_text('<!doctype html><meta charset="utf-8"><pre>'+escape(text)+'</pre>')
    print(text)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cutouts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())

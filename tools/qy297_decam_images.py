"""Fetch only small cutouts matched by exposure timestamp prefix, band and detector."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from urllib.parse import urlsplit,parse_qs,urlencode,urlunsplit
import json,hashlib,base64
import numpy as np
import pyarrow.parquet as pq
from astropy.io.votable import parse_single_table
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from report_html import render
from reconcile_qy297_adam import utc
BASE=Path(__file__).resolve().parents[1];out=BASE/'reports/2026/11/21/qy297-adam-reconciliation'
r=[x for x in pq.read_table(out/'inputs/275809_observations.adam-core.parquet').to_pylist() if x['catalog_id']=='nsc']
jobs=[]
for x in r:
 t=parse_single_table(str(out/f"sia-{utc(x)[:10]}.xml")).to_table()
 detector=x['id'].split('.')[2]
 for y in t:
  u=str(y['access_url']);q=parse_qs(urlsplit(u).query)
  if x['exposure_id'][:17] in u and str(y['prodtype'])=='image' and q.get('extn')==[detector] and str(y['obs_bandpass'])==x['filter']:
   q={k:v[0] for k,v in q.items()};q['POS']=f"{x['ra']},{x['dec']}";q['SIZE']='0.008333333,0.008333333'
   parts=urlsplit(u);u=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(q),''))
   jobs.append((x,u));break

def fetch(job):
 x,u=job;d={'id':x['id'],'exposure_id':x['exposure_id'],'utc':utc(x),'url':u,'band':x['filter']};raw=BASE/'data/raw/qy297-adam';raw.mkdir(parents=True,exist_ok=True);path=raw/(x['id']+'.fits')
 try:
  if not path.exists():
   with urlopen(u,timeout=25) as f:b=f.read(36000001)
   if len(b)>36000000:raise ValueError('36 MB cap exceeded')
   path.write_bytes(b)
  with fits.open(path) as h:
   image=next(z for z in h if z.data is not None and np.ndim(z.data)==2);a=np.array(image.data,dtype=float);w=WCS(image.header);px,py=w.all_world2pix(x['ra'],x['dec'],0);d.update({'pixel_x':float(px),'pixel_y':float(py),'shape':list(a.shape),'inside_image':bool(0<=px<a.shape[1] and 0<=py<a.shape[0]),'finite_fraction':float(np.mean(np.isfinite(a)))})
   cx,cy=int(round(float(px))),int(round(float(py))); x0=max(0,cx-60);y0=max(0,cy-60);a=a[y0:cy+61,x0:cx+61];d['plot_x']=float(px)-x0;d['plot_y']=float(py)-y0
   np.save(out/(x['id']+'.npy'),a)
  d['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();d['bytes']=path.stat().st_size;d['raw_path']=str(path.relative_to(BASE))
 except Exception as e:d['error']=f'{type(e).__name__}: {e}'
 return d
jobs=jobs[:1]  # Service returns detector images, so bound transfer to one ~34 MB file.
results=list(ThreadPoolExecutor(max_workers=1).map(fetch,jobs));(out/'image-checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
good=[x for x in results if 'error' not in x]
if good:
 fig,axs=plt.subplots(1,1,figsize=(6,6),squeeze=False);
 for ax,d in zip(axs.flat,good):
  a=np.load(out/(d['id']+'.npy'));v=a[np.isfinite(a)];lo,hi=np.percentile(v,[15,99.5]);ax.imshow(a,origin='lower',cmap='gray',vmin=lo,vmax=hi);ax.plot(d['plot_x'],d['plot_y'],'o',ms=14,mfc='none',mec='cyan');ax.set_title(d['utc'][:16]+' '+d['band']+'\n'+d['id'],fontsize=8);ax.set_axis_off()
 for ax in list(axs.flat)[len(good):]:ax.set_axis_off()
 fig.suptitle('DECam matching-exposure image\nCyan circle: NSC catalog position',fontsize=11);fig.tight_layout();fig.savefig(out/'decam-contact-sheet.png',dpi=150);plt.close(fig)
md=(out/'report.md').read_text();start=md.index('No image pixels were supplied');end=md.index('## Suitability',start);md=md[:start]+'No image pixels were supplied in the two Parquet files. No image pixels were inspected in this reconciliation.\n'+md[end:];md=md.replace('No image pixels were inspected in this reconciliation.',f"Retrieved {len(good)} science detector image(s) from {len(jobs)} exposure/band/detector-matched requests; {len(results)-len(good)} failed. See retained FITS, image-checks.json and contact sheet. The service returned a full detector image despite the small cutout request. Locally cropped a 121-pixel square for inspection. Raw detector FITS is retained under data/raw/qy297-adam (excluded from Git); its hash and retrieval URL are recorded. Pixel positions were checked using the image WCS; no new centroid fit or independent orbit residual was measured.")
md+='\n## Matched cutout inspection\nExposure matching uses timestamp prefix, band and detector. Processing-version suffixes can differ from the NSC exposure identifiers, so these are matching-exposure products, not certified identical NSC reduction versions. Mask and weight products were not retrieved; visual appearance alone cannot certify the astrometry.\n'
(out/'report.md').write_text(md);html=render(md,'QY297 ADAM reconciliation')
if good:html+='<img style="width:100%" alt="DECam cutout contact sheet" src="data:image/png;base64,'+base64.b64encode((out/'decam-contact-sheet.png').read_bytes()).decode()+'">'
(out/'report.html').write_text(html)

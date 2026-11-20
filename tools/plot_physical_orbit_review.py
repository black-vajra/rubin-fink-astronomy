#!/usr/bin/env python3
"""Plot the retained physical-orbit scores and conditional QY297 ellipse."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('report_dir',type=Path)
a=p.parse_args()
rows=json.loads((a.report_dir/'results.json').read_text())['results']
q=next(x for x in rows if x['name']=='2001 QY297')['withheld'][0]
cov=np.array(q['formal_position_covariance_arcsec2'])
eig,vec=np.linalg.eigh(cov);order=np.argsort(eig)[::-1];eig=eig[order];vec=vec[:,order]
axes=np.sqrt(eig*5.991464547);angle=np.degrees(np.arctan2(vec[1,0],vec[0,0]))
fig,(left,right)=plt.subplots(1,2,figsize=(12,5),layout='constrained')
left.add_patch(Ellipse((0,0),2*axes[0],2*axes[1],angle=angle,facecolor='#dbeafe',edgecolor='#2563eb',lw=1.5,label='Formal 95% prediction ellipse'))
left.scatter([0],[0],marker='+',s=110,color='#2563eb',label='Fitted prediction',zorder=3)
left.scatter([-q['east_error_arcsec']],[-q['north_error_arcsec']],s=45,color='#047857',label=f"Withheld detection: {q['error_arcsec']:.3f} arcsec miss",zorder=4)
left.set(xlabel='East offset (arcsec)',ylabel='North offset (arcsec)',title='QY297 · withheld November 12 position')
left.set_aspect('equal');left.autoscale_view();left.grid(alpha=.2);left.legend(fontsize=8,loc='upper left')
labels=[];values=[]
for x in rows:
 if x['name']=='2001 QY297':label='QY297\nNov 12';w=x['withheld'][0]
 elif x['name']=='2013 CR7':label='CR7\nNov 12';w=x['withheld'][0]
 elif x['test_cutoff_UTC']=='2026-11-12':label='WV203: 2 dates\nNov 15';w=x['withheld'][-1]
 else:label='WV203: 3 dates\nNov 15';w=x['withheld'][0]
 labels.append(label);values.append(w['error_arcsec'])
colors=['#047857' if v<=60 else '#b91c1c' for v in values]
bars=right.bar(labels,values,color=colors,width=.62)
right.set_yscale('log');right.set_ylim(.02,6000)
right.axhline(60,color='#a16207',ls='--',label='Fixed 60 arcsec gate')
for bar,v in zip(bars,values):right.text(bar.get_x()+bar.get_width()/2,v*1.25,f'{v:,.3f}',ha='center',fontsize=9)
right.set(ylabel='Withheld position error (arcsec; logarithmic)',title='Independent fits · successes and failed two-date arc')
right.legend(fontsize=8);right.grid(axis='y',alpha=.2)
fig.suptitle('Exploratory Sun-only orbit model · training observations only',fontsize=14)
fig.savefig(a.report_dir/'benchmark.png',dpi=170)
plt.close(fig)
caption='Formal ellipse assumes independent 0.15-arcsecond errors per coordinate and one local orbit branch; systematic errors and alternative branches are excluded. These are known-object retrospective tests.'
md=a.report_dir/'report.md';content=md.read_text()
if '![Physical orbit benchmark]' not in content:
 md.write_text(content+'\n## Benchmark figure\n\n![Physical orbit benchmark](benchmark.png)\n\n'+caption+'\n')
html=a.report_dir/'report.html';content=html.read_text()
if 'src="benchmark.png"' not in content:html.write_text(content+'<p><img src="benchmark.png" style="max-width:100%" alt="Physical orbit benchmark"></p><p>'+caption+'</p>')
print(a.report_dir/'benchmark.png')

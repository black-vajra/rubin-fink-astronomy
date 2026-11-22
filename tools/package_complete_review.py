#!/usr/bin/env python3
"""Embed the dated review and its appendices/provenance in a single offline HTML."""
import argparse,base64,csv,io,json,re
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from report_html import render

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report-dir',type=Path,required=True);a=p.parse_args()
base=a.report_dir.resolve();day=base.name;date='-'.join(base.parts[-3:])
parts=[('overview','Overnight overview','overnight-review.md'),
 ('extragalactic','Extragalactic review',date+'-extragalactic-report.md'),
 ('moving','Moving-object review',date+'-moving-object-report.md'),
 ('freshness','Freshness data and query accounting','freshness-review/report.md'),
 ('pgc-diagnostic','PGC fit-choice diagnostic','pgc-fit-sensitivity/report.md'),
 ('ed138-benchmark','ED138 public-astrometry benchmark','ed138-public-astrometry/report.md'),
 ('methods','Methods and data-source follow-up','methods-and-data-sources.md')]
map_links={}
for ident,title,file in parts:
    path=base/file
    map_links[path.resolve()]=ident
    map_links[path.with_suffix('.html').resolve()]=ident
for file,ident in [('freshness-and-query-accounting.html','freshness'),('pgc-fit-choice-diagnostic.html','pgc-diagnostic'),('ed138-public-astrometry-benchmark.html','ed138-benchmark')]:map_links[(base/file).resolve()]=ident
output=[render('',f'Complete Rubin review · {date}'),'<main><h1>Complete Rubin review · '+escape(date)+'</h1>',
 '<p>All seven report sections are embedded in this one file. No companion folders are needed to read them. '
 'Reporting date is America/New_York; UTC generation dates after midnight November 22 still fall on November 21 EST. '
 'Full source histories and FITS remain in the research archive; selected supporting data are embedded below.</p><nav><h2>Contents</h2><ul>']
output += [f'<li><a href="#{ident}">{escape(title)}</a></li>' for ident,title,_ in parts]
output += ['<li><a href="#supporting-data">Supporting data and provenance</a></li></ul></nav>']
for ident,title,file in parts:
    path=base/file;md=path.read_text()
    def internal(m):
        url=m.group(2)
        if '://' in url or url.startswith('#'):return m.group(0)
        target=map_links.get((path.parent/url).resolve())
        if target is None:raise ValueError(f'Unresolved report link: {file}: {url}')
        return m.group(1)+'#'+target+m.group(3)
    md=re.sub(r'(\[[^\]]+\]\()([^)]+)(\))',internal,md)
    # Make source-only URL lines clickable, without guessing inside existing links.
    md=re.sub(r'(?m)^(- )?(https?://\S+)$',lambda m:(m.group(1) or '')+'['+m.group(2)+']('+m.group(2)+')',md)
    html=render(md,title).split('</style>',1)[1]
    output += [f'<section id="{ident}">',html,'<p><a href="#top">Back to top</a></p></section><hr>']
output.insert(1,'<div id="top"></div>')
output.append('<section id="supporting-data"><h2>Supporting data and provenance</h2>')
for file,title in [('freshness-review/freshness.json','Fink requests, source-ID changes and response hashes'),
 ('pots-overnight-evidence.json','User-supplied Pots overnight evidence, including zero new files'),
 ('ed138-public-astrometry/test-plan.json','ED138 training and withheld-test declaration'),
 ('ed138-public-astrometry/results.json','ED138 initialization trials, fitted state and held-out predictions'),
 ('ed138-public-astrometry/sun-from-observer.json','Retained Rubin observer geometry request/response'),
 ('ed138-public-astrometry/sun-barycentric.json','Retained Sun barycentric geometry request/response'),
 ('pgc-fit-sensitivity/results.json','PGC: all 108 diagnostic fits and input file hashes'),
 ('review-sources.json','Source-access notes'),('runtime-and-code.json','Runtime versions and analysis code hashes')]:
    path=base/file;raw=path.read_bytes();payload=json.loads(raw)
    data='data:application/json;base64,'+base64.b64encode(raw).decode()
    output += ['<details><summary>'+escape(title)+'</summary>',
       '<p><a download="'+escape(path.name)+'" href="'+data+'">Download JSON</a></p>',
       '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(json.dumps(payload,indent=2))+'</pre></details>']
raw=(base/'ed138-public-astrometry/observations.csv').read_bytes()
rows=list(csv.reader(io.StringIO(raw.decode())))
output += ['<details><summary>All 74 public MPC observations: native station codes, positions and source lines</summary>',
 '<p><a download="ed138-public-observations.csv" href="data:text/csv;base64,'+base64.b64encode(raw).decode()+'">Download CSV</a></p><table>']
for i,row in enumerate(rows):
    tag='th' if i==0 else 'td';output.append('<tr>'+''.join('<'+tag+'>'+escape(cell)+'</'+tag+'>' for cell in row)+'</tr>')
output+=['</table></details></section></main>']
html='\n'.join(output)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if 'href' in d:self.links.append(d['href'])
        if 'src' in d:raise AssertionError('Offline review must not depend on external resources')
x=Links();x.feed(html)
for link in x.links:
    if link.startswith('#'):assert link[1:] in x.ids,link
    else:assert link.startswith(('https://','http://','data:')),link
path=base/'complete-review.html';path.write_text(html)
print(f'Validated self-contained review: {path}; {len(html.encode()):,} bytes; {len(x.links)} links.')

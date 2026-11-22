"""Small escaped renderer for the headings, lists, links and tables in our reports."""
from html import escape
import re

def inline(text):
    text=escape(text)
    text=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',text)
    def link(m):
        url=m.group(2)
        return f'<a href="{url}">{m.group(1)}</a>' if ':' not in url or url.startswith(('https://','http://')) else m.group(1)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,text)

def render(md,title):
    out=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+escape(title)+'</title>',
         '<style>body{font:16px/1.55 system-ui;max-width:1120px;margin:2em auto;padding:0 1em;color:#172033}table{border-collapse:collapse;width:100%;font-size:.94em}th,td{border:1px solid #cbd5e1;padding:.45em;text-align:left}th{background:#edf2f7}h1,h2{line-height:1.2}a{color:#174fb0}code{background:#eef2f6}</style>']
    table=listing=False
    for line in md.splitlines():
        if not line.startswith('|') and table:out.append('</table>');table=False
        if not line.startswith('- ') and listing:out.append('</ul>');listing=False
        if not line.strip():continue
        if line.startswith('|'):
            cells=[c.strip() for c in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?',c) for c in cells):continue
            tag='td' if table else 'th'
            if not table:out.append('<table>');table=True
            out.append('<tr>'+''.join('<'+tag+'>'+inline(c)+'</'+tag+'>' for c in cells)+'</tr>')
        elif line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));n=min(n,6);out.append(f'<h{n}>'+inline(line.lstrip('#').strip())+f'</h{n}>')
        elif line.startswith('- '):
            if not listing:out.append('<ul>');listing=True
            out.append('<li>'+inline(line[2:])+'</li>')
        else:out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</table>')
    if listing:out.append('</ul>')
    return '\n'.join(out)

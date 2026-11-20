#!/usr/bin/env python3
"""Add colored terminal sections to installed Rubin collectors (presentation only).
Stop both collectors first. Run with system Python 3; no extra packages required.
"""
import argparse
import ast
from datetime import datetime
import os
from pathlib import Path
import shutil
import stat
import tempfile

MARKER = '_RUBIN_TERMINAL_UI_VERSION = 1'
RENDERER = r'''
_RUBIN_TERMINAL_UI_VERSION = 1


def _rubin_paint(text, code):
    import os
    mode = os.environ.get('RUBIN_COLOR', 'auto').lower()
    enabled = (mode == 'always' or
               (mode != 'never' and sys.stdout.isatty()
                and os.environ.get('TERM') != 'dumb'))
    if 'NO_COLOR' in os.environ:
        enabled = False
    return f'\033[{code}m{text}\033[0m' if enabled else text


def log(message):
    clean = ''.join(c for c in str(message) if c.isprintable() or c == '\n')
    upper = clean.upper()
    if 'ERROR' in upper or 'FAILED' in upper:
        color = '91'
    elif any(word in upper for word in ('WARNING', 'HISTORICAL', 'GAP:', 'UNVERIFIED', 'FUTURE TIME')):
        color = '93'
    elif 'REPORT:' in upper or 'EVIDENCE UPDATE' in upper or 'WATCHLIST:' in upper or 'DISTANT WATCH:' in upper:
        color = '95'
    elif any(word in upper for word in ('NEXT CYCLE', 'RUBIN PUBLIC WATCH', 'RUBIN DISTANT WATCH', 'STOPPED')):
        color = '96'
    else:
        color = '92'
    print(_rubin_paint(f'[{now()}] {clean}', color), flush=True)


def heading(title, detail=''):
    import shutil
    clean = lambda x: ''.join(c for c in str(x) if c.isprintable())
    width = max(30, min(shutil.get_terminal_size(fallback=(100,24)).columns-1, 100))
    print('\n' + _rubin_paint('═'*width, '96'), flush=True)
    print(_rubin_paint('  '+clean(title), '93'), flush=True)
    if detail:
        print(_rubin_paint('  '+clean(detail), '96'), flush=True)
    print(_rubin_paint('─'*width, '96'), flush=True)
'''


def function_node(text, name):
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        raise ValueError(f'Expected exactly one {name}() function; unsupported version')
    return nodes[0]


def replace_logger(text):
    node = function_node(text, 'log')
    lines = text.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1]) + RENDERER.strip() + '\n' + ''.join(lines[node.end_lineno:])


def enter(text, name, statement):
    node = function_node(text, name)
    lines = text.splitlines(keepends=True)
    first = node.body[0]
    # Keep a real function docstring as its first statement.
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        index = first.end_lineno
    else:
        index = first.lineno-1
    lines.insert(index, '    ' + statement + '\n')
    return ''.join(lines)


def swap(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected source anchor was not found exactly once; unsupported version')
    return text.replace(old, new, 1)


def public_style(text):
    text = replace_logger(text)
    text = enter(text, 'cycle', "heading('RUBIN PUBLIC WATCH — COLLECTION CYCLE', 'Public API samples · ' + now())")
    text = swap(text, '    for tag in args.tags:\n        collector.fetch', '''    for tag in args.tags:
        titles = {'hostless_candidate': 'HOSTLESS TRANSIENT CANDIDATES',
                  'extragalactic_new_candidate': 'NEW EXTRAGALACTIC CANDIDATES',
                  'extragalactic_lt20mag_candidate': 'BRIGHT EXTRAGALACTIC CANDIDATES'}
        heading(titles.get(tag, tag.upper()), f'Selection: {tag} · requested sample: {args.sample}')
        collector.fetch''')
    text = swap(text, "    todo = db.execute('''SELECT DISTINCT", "    heading('OBJECT HISTORIES', f'Up to {args.histories} due objects this cycle')\n    todo = db.execute('''SELECT DISTINCT")
    text = enter(text, 'analyze', "heading('CANDIDATE SCREENING & EVIDENCE REVIEW', 'Same-filter brightness changes · repeated detections · positional review')")
    text = enter(text, 'report', "heading('GENERATING RESEARCH REPORT', 'HTML light curves · JSON evidence · CSV watchlist')")
    return text


def distant_style(text):
    text = enter(text, 'collect', "core.heading('DISTANT SOLAR SYSTEM — COLLECTION CYCLE', 'Public sky patches and measurement histories')")
    text = swap(text, "        selection='field:'+f['label']", "        core.heading('SKY PATCH — ' + f['label'], f\"RA {f['ra']:.5f}° · Dec {f['dec']:.5f}° · radius {f['radius']} arcsec\")\n        selection='field:'+f['label']")
    text = swap(text, "    todo=db.execute('''SELECT DISTINCT", "    core.heading('OBJECT HISTORIES', f'Up to {args.histories} due objects this cycle')\n    todo=db.execute('''SELECT DISTINCT")
    text = enter(text, 'analyze', "core.heading('DISTANT-BODY MOTION LINKING', 'Cross-ID links · Earth parallax · trial distances · quality and consistency checks')")
    text = enter(text, 'skybot', "core.heading('KNOWN-OBJECT CATALOG CHECK', 'SkyBoT queries at three observation epochs')")
    text = enter(text, 'report', "core.heading('GENERATING DISTANT-BODY REPORT', 'Motion plots · evidence · coverage · conditional size scenarios')")
    return text + '\n' + MARKER + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='Account home containing the installed Rubin folders')
    args = parser.parse_args()
    targets = [
        (args.home/'rubin-watch/rubin-public-watch.py', public_style),
        (args.home/'rubin-distant-watch/rw_core.py', replace_logger),
        (args.home/'rubin-distant-watch/rubin-distant-watch.py', distant_style),
    ]
    plans = []
    for path, transform in targets:
        if not path.is_file():
            print('Not installed; skipped:', path)
            continue
        source = path.read_text()
        if MARKER in source:
            print('Color headings already installed:', path)
            continue
        updated = transform(source)
        compile(updated, str(path), 'exec')
        plans.append((path, updated))
    if not plans:
        print('Nothing to update.')
        return
    # All files must parse before any installed source is changed.
    backup = args.home/'rubin-terminal-backups'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    staged = []
    changed = []
    try:
        for path, updated in plans:
            backup_file = backup/path.parent.name/path.name
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_file)
            fd, name = tempfile.mkstemp(prefix='.rubin-ui-', suffix='.py', dir=path.parent)
            with os.fdopen(fd, 'w') as f:
                f.write(updated)
            os.chmod(name, stat.S_IMODE(path.stat().st_mode))
            staged.append((path, Path(name), backup_file))
        for path, temp, backup_file in staged:
            os.replace(temp, path)
            changed.append((path, backup_file))
            print('Updated:', path)
    except Exception:
        for path, backup_file in changed:
            shutil.copy2(backup_file, path)
        raise
    finally:
        for _, temp, _ in staged:
            temp.unlink(missing_ok=True)
    print('Backups:', backup)
    print('Finished. Restart the collectors to see the colored headings.')


if __name__ == '__main__':
    main()

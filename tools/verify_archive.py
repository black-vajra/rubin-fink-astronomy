#!/usr/bin/env python3
"""Verify preserved-source checksums and catch unsuitable files before committing."""
import hashlib,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[]
    imported=json.loads((ROOT/'data/manifests/2026-11-20-import.json').read_text())
    for row in imported:
        p=ROOT/row['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            errors.append('Missing or altered preserved source: '+row['path'])
    result=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT,capture_output=True,check=True)
    names=sorted(set(n for n in result.stdout.decode().split('\0') if n))
    for row in imported:
        if row['path'] not in names:
            errors.append('Imported evidence excluded from Git: '+row['path'])
    sensitive=re.compile(rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}')
    for name in names:
        p=ROOT/name
        if not p.is_file(): continue
        if p.stat().st_size>95*1024*1024: errors.append('Use a release asset for large file: '+name)
        if any(part in {'.finkclient','.ssh','.venv','venv'} for part in p.parts): errors.append('Private/runtime path: '+name)
        if sensitive.search(p.read_bytes()): errors.append('Possible secret material: '+name)
        if p.suffix=='.json':
            try:json.loads(p.read_text())
            except (ValueError,UnicodeDecodeError) as e:errors.append(f'Invalid JSON: {name}: {e}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'OK: {len(imported)} preserved-source hashes; {len(names)} files checked. Secret-pattern checks are limited and do not certify arbitrary uploads.')

if __name__=='__main__': main()

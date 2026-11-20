#!/usr/bin/env python3
"""Capture allowlisted research files; optionally preserve large data as split release assets.

Never scans arbitrary home files, credential directories or SSH/VPN configuration.
No Git commits, uploads, service changes or downloads are performed.
"""
import argparse,hashlib,json,shutil,sqlite3,tarfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

class Parts:
    def __init__(self,folder):
        self.folder=folder;self.f=None;self.n=0;self.size=0;self.limit=95*1024*1024
    def writable(self):return True
    def write(self,blob):
        total=len(blob)
        while blob:
            if self.f is None:
                self.f=(self.folder/f'part-{self.n:04d}.bin').open('wb');self.n+=1;self.size=0
            n=min(len(blob),self.limit-self.size)
            self.f.write(blob[:n]);self.size+=n;blob=blob[n:]
            if self.size==self.limit:self.close()
        return total
    def flush(self):
        if self.f:self.f.flush()
    def close(self):
        if self.f:self.f.close();self.f=None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-home',type=Path,default=Path.home())
    p.add_argument('--include-large-data',action='store_true')
    args=p.parse_args();home=args.source_home.resolve()
    stamp=datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d-%H%M%S')
    small=ROOT/'archive/hosts/pots'/stamp
    if small.exists():raise SystemExit('Capture directory already exists')
    small.mkdir(parents=True)
    roots=['rubin-historical-2026','rubin-live','rubin-quasar','rubin-watch']
    found=[];large=[];missing=[]
    for name in roots:
        base=home/name
        if not base.is_dir():missing.append(name);continue
        for path in sorted(base.rglob('*')):
            rel=path.relative_to(home)
            if path.is_symlink() or any(x in {'venv','.venv','.git','__pycache__','ephemeris-cache'} for x in rel.parts):continue
            if not path.is_file() or 'credentials' in path.name.lower():continue
            if path.suffix not in {'.py','.sh','.md','.html','.json','.csv','.toml','.parquet','.sqlite3','.avro','.service','.timer'}:continue
            if path.suffix=='.avro' or path.stat().st_size>=45*1024*1024 or path.suffix=='.sqlite3':
                large.append((path,rel));continue
            dest=small/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
            found.append({'source':str(rel),'path':str(dest.relative_to(ROOT)),'bytes':dest.stat().st_size,'sha256':digest(dest)})
    units=home/'.config/systemd/user'
    if units.exists():
        for path in sorted(units.glob('rubin-*')):
            if path.is_symlink() or not path.is_file() or path.suffix not in {'.service','.timer'}:continue
            dest=small/'systemd/user'/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
            found.append({'source':str(path.relative_to(home)),'path':str(dest.relative_to(ROOT)),'bytes':dest.stat().st_size,'sha256':digest(dest)})
    manifest={'captured_local':stamp,'source_home':str(home),'small_files':found,'missing_roots':missing,
              'large_data_archived':False,'large_files':[],'release_parts':[]}
    if args.include_large_data and large:
        folder=ROOT/'.release-assets'/stamp;folder.mkdir(parents=True)
        writer=Parts(folder)
        try:
            with tarfile.open(mode='w|gz',fileobj=writer) as archive:
                for path,rel in large:
                    source=path;temporary=None
                    if path.suffix=='.sqlite3':
                        temporary=folder/'sqlite-backup.tmp'
                        src=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);out=sqlite3.connect(temporary)
                        try:src.backup(out)
                        finally:out.close();src.close()
                        source=temporary
                    stat=source.stat();before=digest(source)
                    archive.add(source,arcname=str(rel),recursive=False)
                    if source.stat().st_mtime_ns!=stat.st_mtime_ns or source.stat().st_size!=stat.st_size:
                        raise RuntimeError(f'Source changed during capture: {rel}; retry in a quiet collection window')
                    manifest['large_files'].append({'source':str(rel),'bytes':stat.st_size,'sha256':before,'sqlite_backup':temporary is not None})
                    if temporary:temporary.unlink()
        finally:writer.close()
        manifest['release_parts']=[{'path':str(x.relative_to(ROOT)),'name':x.name,'bytes':x.stat().st_size,'sha256':digest(x)} for x in sorted(folder.glob('part-*.bin'))]
        manifest['large_data_archived']=True
    else:
        manifest['large_files']=[{'source':str(rel),'bytes':path.stat().st_size,'status':'not captured'} for path,rel in large]
    target=ROOT/'data/manifests'/f'pots-capture-{stamp}.json'
    target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Captured {len(found)} small files; found {len(large)} large/raw files. Manifest: {target}')
    if large and not args.include_large_data:print('Large data remain unarchived. Add --include-large-data to create split release assets.')
    if args.include_large_data:print('Large archives are local only. Upload and verify release assets before calling them a remote backup.')

if __name__=='__main__':main()

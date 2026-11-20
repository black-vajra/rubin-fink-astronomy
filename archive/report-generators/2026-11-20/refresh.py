"""Refresh small public histories, retain provenance, regenerate cached-snapshot reports."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('historical', BASE / 'historical.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
jobs = [('statistics-202611.json', 'statistics', {'date':'202611'})]
jobs += [(f'object-{oid}.json','sources',{'diaObjectId':oid}) for oid in h.TARGETS]
jobs += [(f'sso-{name.replace(" ","_")}.json','sso',{'n_or_d':name}) for name in ['2014 WV203','2013 CR7']]

def refresh(job):
    filename, endpoint, params = job
    dest = BASE / 'data' / filename
    previous = json.loads(dest.read_text()) if dest.exists() else []
    result = {'file':filename, 'endpoint':endpoint, 'parameters':params,
              'requested_utc':datetime.now(timezone.utc).isoformat(), 'previous_rows':len(previous)}
    try:
        req = urllib.request.Request(h.API+endpoint,
            data=json.dumps({'output-format':'json',**params}).encode(),
            headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as response:
            raw = response.read()
        rows = json.loads(raw)
        if not isinstance(rows,list) or not rows:
            raise ValueError('Response was not a nonempty row list; retained prior data')
        dest.write_bytes(raw)
        key = 'r:diaSourceId'
        old_ids = {str(r[key]) for r in previous if key in r}
        new_ids = {str(r[key]) for r in rows if key in r}
        result.update(status='fresh',rows=len(rows),added_source_ids=sorted(new_ids-old_ids),
                      removed_source_ids=sorted(old_ids-new_ids),sha256=hashlib.sha256(raw).hexdigest())
    except Exception as e:
        result.update(status='failed; cached data retained',error=f'{type(e).__name__}: {e}')
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(refresh,jobs))
(BASE/'refresh-provenance.json').write_text(json.dumps(results,indent=2)+'\n')
h.inventory()
h.extragalactic()
h.motion()
for r in results:
    print(json.dumps(r))

#!/usr/bin/env bash
set -euo pipefail
package=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo="$HOME/rubin-fink-astronomy"
python_bin="$HOME/rubin-live/venv/bin/python"
bundle="$package/rubin-research-finalize-2026-11-20.bundle"
[[ -d "$repo/.git" && -x "$python_bin" && -f "$bundle" ]]
[[ "$(git -C "$repo" branch --show-current)" == main ]]
git -C "$repo" bundle verify "$bundle"
git -C "$repo" fetch --no-tags "$bundle" refs/heads/final-closeout-20261120
prepared=$(git -C "$repo" rev-parse FETCH_HEAD)
if ! git -C "$repo" merge-base --is-ancestor HEAD "$prepared"; then
    printf 'The checkout has additional local commits; a normal merge is needed before this finalizer. No reset was performed.\n' >&2
    exit 1
fi
# Preserve any manually renamed/edited e/f/g entry before applying the finalized journals.
"$python_bin" - "$repo" <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import shutil,subprocess,sys
repo=Path(sys.argv[1]);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=repo/'archive/hosts/pots/pre-finalization-journals'/stamp
for letter in ('e','f','g'):
    rel=f'journal/2026/11/2026-11-20{letter}-rubin-journal.md';path=repo/rel
    dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain','--',rel],text=True).strip()
    if not dirty:continue
    if path.is_file():
        backup.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup/path.name)
    head=subprocess.run(['git','-C',str(repo),'show','HEAD:'+rel],capture_output=True)
    if head.returncode==0:
        subprocess.run(['git','-C',str(repo),'restore','--staged','--',rel],check=True)
        path.write_bytes(head.stdout)
    elif path.exists():
        # A verified backup exists above; move the untracked colliding name out of the merge path.
        path.unlink()
PY
git -C "$repo" merge --ff-only "$prepared"
"$python_bin" "$repo/tools/finalize-pots.py" --prepared-commit "$prepared"

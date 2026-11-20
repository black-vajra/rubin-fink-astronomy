#!/usr/bin/env bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${RUBIN_PYTHON:-$HOME/rubin-watch/venv/bin/python}"
if [[ ! -x "$python_bin" ]]; then
    printf 'Python environment missing: %s\nSet up ~/rubin-watch/venv with numpy astropy matplotlib first.\n' "$python_bin" >&2
    exit 1
fi
exec "$python_bin" "$script_dir/rubin-distant-watch.py" "$@"

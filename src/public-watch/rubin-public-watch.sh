#!/usr/bin/env bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${RUBIN_PYTHON:-$HOME/rubin-watch/venv/bin/python}"
if [[ ! -x "$python_bin" ]]; then
    printf 'Python environment not found: %s\n' "$python_bin" >&2
    exit 1
fi
exec "$python_bin" "$script_dir/rubin-public-watch.py" "$@"

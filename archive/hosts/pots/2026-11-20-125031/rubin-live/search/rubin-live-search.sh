#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${RUBIN_PYTHON:-$HOME/rubin-live/venv/bin/python}" "$script_dir/rubin-distant-watch.py" --data-dir "$HOME/rubin-live/distant-search" "$@"

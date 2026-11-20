#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python_bin="$HOME/rubin-live/venv/bin/python"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$repo/reports/$(TZ=America/New_York date +%Y/%m/%d)/physical-orbit-$stamp"
"$python_bin" "$repo/tools/physical_orbit_review.py" \
    --data-dir "$repo/reports/2026/11/20/physical-orbit-watchlist" --output "$out"
"$python_bin" "$repo/tools/plot_physical_orbit_review.py" "$out"
printf '\nReport: %s\n' "$out/report.md"
if command -v xdg-open >/dev/null; then
    xdg-open "$out/report.html" >/dev/null 2>&1 || true
fi

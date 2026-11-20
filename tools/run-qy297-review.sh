#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python_bin="$HOME/rubin-live/venv/bin/python"
database="$HOME/rubin-historical-2026/alerts.sqlite3"
if [[ ! -x "$python_bin" || ! -f "$database" ]]; then
    printf 'Requires the Rubin Python environment and local archive:\n%s\n%s\n' "$python_bin" "$database" >&2
    exit 1
fi
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$repo/reports/$(TZ=America/New_York date +%Y/%m/%d)/qy297-local-$stamp"
"$python_bin" "$repo/tools/qy297_review.py" \
    --data-dir "$repo/reports/2026/11/20/qy297-investigation" \
    --output "$out" --db "$database"
printf '\nReview together: %s\n' "$out/report.md"
printf 'This run reads the local database and requests small JPL ephemerides; it downloads no alert archive.\n'
if command -v xdg-open >/dev/null; then
    xdg-open "$out/report.html" >/dev/null 2>&1 || true
fi

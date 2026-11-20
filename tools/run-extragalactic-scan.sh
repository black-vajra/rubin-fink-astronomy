#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
run_day="$(TZ=America/New_York date +%Y/%m/%d)"
run_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="reports/$run_day/archive-scan-$run_stamp"
python3 tools/extragalactic_scan.py \
  --database "$HOME/rubin-historical-2026/alerts.sqlite3" \
  --output "$output"
printf '\nScan finished. Report: %s/%s/report.html\n' "$repo_dir" "$output"
printf 'Review the report and JSON accounting before interpreting candidates.\n'
printf 'To archive the generated results after review: git add %q && git commit -m %q && git push\n' "$output" "Record $run_stamp archive-wide extragalactic triage"

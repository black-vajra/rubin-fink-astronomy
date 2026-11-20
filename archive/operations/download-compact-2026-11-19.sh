#!/bin/bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
topic=ftransfer_lsst_2026-11-19_639723
python="$HOME/rubin-live/venv/bin/python"
mkdir -p "$project_dir/alerts/$topic"
df -h "$project_dir"
"$python" "$HOME/rubin-live/venv/bin/finkctl" transfer -survey lsst   -topic "$topic" -outdir "$project_dir/alerts/$topic" -outformat avro   --dump_schemas --verbose
"$python" "$project_dir/historical.py" --avro "$project_dir/alerts/$topic"

#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
command -v gh >/dev/null || { echo 'Install GitHub CLI (gh) first.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Run gh auth login, then run this script again.' >&2; exit 1; }
account="$(gh api user --jq .login)"
[[ "$account" == black-vajra ]] || { echo "GitHub is signed in as $account; switch to black-vajra before publishing." >&2; exit 1; }
python3 tools/verify_archive.py
if ! gh repo view black-vajra/rubin-fink-astronomy --json nameWithOwner >/dev/null 2>&1; then
  gh repo create black-vajra/rubin-fink-astronomy --private --description 'Rubin/Fink astronomy research: data provenance, daily reports, journals and validated analyses'
fi
if git remote get-url origin >/dev/null 2>&1; then
  remote="$(git remote get-url origin)"
  case "$remote" in
    https://github.com/black-vajra/rubin-fink-astronomy|https://github.com/black-vajra/rubin-fink-astronomy.git|git@github.com:black-vajra/rubin-fink-astronomy.git) ;;
    *) echo "Unexpected origin $remote; review it before publishing." >&2; exit 1 ;;
  esac
else
  git remote add origin https://github.com/black-vajra/rubin-fink-astronomy.git
fi
gh auth setup-git
git push --set-upstream origin main
test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/main | cut -f1)"
echo 'Published and verified black-vajra/rubin-fink-astronomy main.'
assets=(.release-assets/*/part-*.bin)
if [[ -f "${assets[0]}" ]]; then
  echo 'Large local assets are ready. Follow docs/ARCHIVING.md to upload and verify them.'
fi

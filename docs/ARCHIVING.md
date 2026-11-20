# GitHub publication and large-data preservation

The prepared checkout contains a local `main` commit, scientific snapshots and checksums. GitHub creation/push requires the user's existing authentication. Default visibility is **private**. Nothing is made public implicitly.

After extracting the prepared checkout on Pots:

```bash
cd "$HOME/rubin-fink-astronomy"
gh auth status
# If needed, sign in interactively using: gh auth login
bash tools/publish-github.sh
```

That script verifies the account is `black-vajra`, creates the repository if absent, checks the remote destination and pushes without force. Existing conflicting remote history will cause the push to fail rather than being overwritten.

## Capture remaining Pots work

Run during the daytime quiet window, while collections and reports are not writing files:

```bash
python3 tools/capture-pots.py --source-home "$HOME" --include-large-data
python3 tools/verify_archive.py
git status --short
git add archive/hosts data/manifests
git commit -m "Archive Pots research outputs, installed units and raw-data inventory"
git push
```

The capture reads only the named Rubin directories and Rubin systemd units. It excludes credential/runtime directories. It copies small code/reports/JSON/Parquet, takes consistent SQLite backups, and writes raw Avro and large products into a gzip tar stream split into 95 MiB release parts. Each part and member receives a checksum. It does not change installed scripts or services, commit automatically or upload anything. Keep collections quiet to prevent an inconsistent raw-file snapshot. Review newly captured scripts/reports for embedded credentials before committing.

Large data go into GitHub **release assets**, with their inventories committed to Git. This retains complete scientific bytes without repeatedly embedding multi-gigabyte raw archives in repository history. The initial 42 MB and 10 MB public Parquet products are already in Git. No Git LFS subscription or storage purchase is configured.

For a completed capture, choose its exact timestamp from `data/manifests/pots-capture-*.json`, then publish that capture's parts:

```bash
capture=REPLACE_WITH_EXACT_CAPTURE_TIMESTAMP
tag="data-$capture"
gh release create "$tag" --repo black-vajra/rubin-fink-astronomy \
  --target main --title "Pots data archive $capture" \
  --notes "Raw research data and consistent SQLite snapshots. Committed capture manifest records per-file and per-part SHA-256 hashes. Concatenate numbered parts to restore the gzip tar archive."
gh release upload "$tag" ".release-assets/$capture"/part-*.bin \
  --repo black-vajra/rubin-fink-astronomy
```

Download release assets to a separate directory, compare their SHA-256 hashes with the committed capture manifest, then concatenate `part-*.bin` in lexical order and extract with `tar -xz` into an empty directory. Verify member hashes too. Do not remove original data merely because upload commands succeeded.

The initial `external-data.json` deliberately keeps unmeasured checksums null. A later capture manifest and verified release supply the missing evidence. Do not relabel the initial inventory as complete before then.

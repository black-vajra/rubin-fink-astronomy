# Daily research record

1. Verify job completion and observation freshness separately. Record observing epochs, API query time, generation time, host, source selection and errors.
2. Save new reports under `reports/YYYY/MM/DD/`. Preserve supplied originals and identify fresh computations versus carried-forward results.
3. Save query responses in a dated `data/snapshots/YYYY-MM-DD/` directory. Keep large raw packets outside Git history, with a committed inventory and a verified durable archive.
4. Write only new journal material to `journal/YYYY/MM/YYYY-MM-DD-rubin-journal.md`. The second entry is `YYYY-MM-DDb-rubin-journal.md`, then `c`, and so on. Use America/New_York for the journal day and UTC for observation epochs. Never put a new day's entry into an older date's file.
5. Describe accomplishments, failed tests, interpretation, remaining uncertainty and next objectives. Link evidence. Update the status/objective pages when evidence changes them.
6. Run `python3 tools/verify_archive.py`, inspect `git diff --stat` and `git diff`, then commit and push explicitly.

Suggested commit title: `Record YYYY-MM-DD reports, findings and research objectives`.

No automatic GitHub pushes or new scheduled tasks are installed by this archive. The nightly scientific jobs and explicit version-control publication are separate operations.

Original reports retain original relative data paths. Their corresponding snapshots now live in `data/snapshots/`; use the import manifest to resolve moved evidence. Older reports may contain superseded conclusions or stale instructions. Current status pages and later journal entries explain the updates.

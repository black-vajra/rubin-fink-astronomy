# Rubin Public Watch 1.0

Public Fink/Rubin alert collection, SQLite evidence tracking, and daily review reports.
Built for piper@sable-hp, Python 3.13, using the existing Fink virtual environment.
No registration, API token, or streaming credentials are used.

## Install on sable-hp

Download `rubin-public-watch.zip` into `~/Downloads`, then:

```bash
python3 -m zipfile -e ~/Downloads/rubin-public-watch.zip ~/rubin-watch
bash ~/rubin-watch/rubin-public-watch.sh --once --report
```

This uses `~/rubin-watch/venv/bin/python`. NumPy, Astropy, and Matplotlib were already
installed with fink-client. It does not change system Python or install anything.
The ZIP does not contain a database and cannot replace your pilot database.

After the first run, collect continuously:

```bash
bash ~/rubin-watch/rubin-public-watch.sh
```

Ctrl+C stops it safely. Keep the terminal/session running for continuous work.
This is a local program, not a ChatGPT scheduled task. No systemd unit is installed.
Stop the old display monitor if you no longer want its duplicate API requests.

## What it does

- Polls three selected public tags every 10 minutes: hostless_candidate,
  extragalactic_new_candidate, extragalactic_lt20mag_candidate.
- Retrieves at most 100 recent detections per tag per cycle. All returned columns
  are saved; responses are capped at 20 MB each. A capped response fails without
  importing a partial batch. Requests are separated by at least two seconds.
- Rotates through up to six object histories per cycle. Each object has a six-hour
  history-fetch cooldown, including failed attempts. History requests use `/sources`.
- Uses the existing `~/rubin-watch/rubin.sqlite3`. Retains the pilot's four tables,
  detections, raw JSON versions, fetch URLs, and provenance. Adds `rw_*` tables for
  normalization, history rotation, coverage, review candidates, and audit entries.
  Existing pilot records are imported into analysis without altering their originals.
  Before the first migration of an existing pilot database, a consistent SQLite
  backup is written under `~/rubin-watch/backups/` automatically.
- Deduplicates exact detection identifiers. JSON integer IDs remain integers/strings;
  floating-point identifiers are rejected rather than rounded. Changed payloads are
  retained as separate versions. One process per data directory is allowed.
- Records request errors, sample-size warnings, overlaps, and collection gaps.
  These diagnostics never claim complete survey coverage.
- Prints the observation date in UTC converted from the source's MJD TAI using
  Astropy. Measurements older than two days are explicitly historical, even when
  downloaded for the first time today.

## Review heuristics

These choices are conservative starting points for triage, not scientific classifiers.

1. **Difference-flux changes:** within the same filter, at least four independent
   visits spanning three TAI calendar-day bins. Inverse-variance daily means are
   compared, with errors inflated for within-day scatter. Flag an extreme-bin
   difference at seven times the combined stated/inflated uncertainty.
   This selection is not corrected for multiple comparisons, calibration errors,
   or correlated measurements. It does not establish a discovery probability.
2. **Repeated hostless-selection detections:** at least three independent visits
   in one filter across two TAI calendar-day bins, each at absolute difference-flux
   S/N >=5. This is evidence of repetition in a broker selection, not confirmed
   hostlessness, astrophysical reality, novelty, or scientific importance.
3. **Positional review:** within one broker-associated object AND filter, at least
   five usable visits across three day bins and a 1–30-day span, using the most
   recent 30 days of available positions. A weighted local
   tangent-plane linear fit includes a 0.10-arcsecond per-axis systematic floor,
   inflates slope errors for residual scatter, requires heuristic motion S/N >=5,
   reduced chi-square <=5 per axis, and displacement >=0.5 arcsecond. Objects with
   a populated ssObjectId are excluded. These are centroid drift alerts, NOT
   unknown moving-body detections. No cross-ID linking, orbit, distance, mass,
   or Planet Nine inference is attempted. RA wrap is handled; high-declination
   and wide-angle cases are excluded. RA–Dec error covariance is not modeled.

All review heuristics require absolute difference-flux S/N >=5 and no observed bad
flags. Core photometry/centroid/pixel quality flags must explicitly be populated.
Missing quality is saved but excluded from screening. All available original
measurements remain archived, including rejected measurements.
Reliability scores are recorded but not used as proof of reality.
Negative difference flux is valid. Science flux is retained separately and is
not substituted for difference flux. Days here are TAI calendar bins, not an
observatory-certified grouping into observing nights.

Broker cross-match metadata (including supplied TNS and Gaia fields) is shown.
A `Fail` or missing match is not evidence of an undiscovered object. Independent
catalog checks, inspection of image cutouts, association checks, calibration
review, and follow-up are still required. Portal links support manual review.
No cutouts or external catalog queries are downloaded automatically in this version.

## Reports and audit

A report is generated on the first cycle, then when 24 hours have elapsed since
the last report and a collection cycle completes. This persists across restarts.
It is not tied to midnight; a stopped computer cannot produce an unattended report.
Each timestamped folder under `~/rubin-watch/reports/` contains:

- `index.html`: self-contained plots for up to 12 flagged objects, evidence,
  freshness, source errors, coverage warnings, and links to Fink for image review.
- `report.json`: machine-readable evidence, fetch diagnostics, and limitations.
- `watchlist.csv`: all retained candidates, including those no longer flagged.

Open `~/rubin-watch/reports/latest.html` in your browser and follow its report link.
All candidate evidence is included even when only the first 12 objects have plots.
Raw data and the full history of changing evidence are preserved in SQLite.
No change in retrieved measurements means no new evidence, no artificial promotion,
and no repeated audit entries. A flag that stops meeting its criteria is retained
as `not_currently_flagged`; this does not prove the object is uninteresting.

Force an immediate new report after a collection:

```bash
bash ~/rubin-watch/rubin-public-watch.sh --once --report
```

Analyze stored data and report without network requests:

```bash
bash ~/rubin-watch/rubin-public-watch.sh --report-only
```

For help or a larger bounded pilot:

```bash
bash ~/rubin-watch/rubin-public-watch.sh --help
bash ~/rubin-watch/rubin-public-watch.sh --sample 200 --histories 10
```

Sample sizes may be 1–1000; histories 0–20; poll interval at least 300 seconds.
HTTP 429 responses honor a bounded Retry-After cooldown, with no immediate retries.
Cycles with errors wait longer. A one-shot run exits 2 if any retrieval failed,
even when some records were successfully saved and a report was produced.

The `faint_trails` tag is optionally available through `--tags`; it selects trails
over two arcseconds. It is not a selection for distant planets, and this script
does not treat a trail tag alone as a reason to flag an object.

Do not run the original pilot write commands simultaneously with this program.
Back up a live SQLite database with SQLite's backup function, not by copying only
the main database file while its WAL is active. Existing public API samples can
miss alerts between polls, including after downtime; this collector does not
silently claim to backfill missing detections.

## Verification

`test_rubin_public_watch.py` contains synthetic offline tests for exact IDs,
quality gating, signed flux, filter separation, repeated visits, constant sources,
RA wrap and position fits, SQLite deduplication/revisions, audit transitions,
invalid-batch rollback, gap reporting, and TAI/UTC conversion. Test measurements
are created only in temporary test databases, never in your observing database.

```bash
~/rubin-watch/venv/bin/python ~/rubin-watch/test_rubin_public_watch.py
```

## Primary sources

- https://doc.lsst.fink-broker.org/services/api/tagsearch/
- https://api.lsst.fink-portal.org/swagger.json
- https://doc.lsst.fink-broker.org/data/photometry/
- https://doc.lsst.fink-broker.org/data/quality/
- https://doc.lsst.fink-broker.org/data/issues/

This is an independent research aid, not an official Rubin/Fink application.

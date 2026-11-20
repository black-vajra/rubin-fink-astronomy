# Archive-wide extragalactic discovery triage

Generated 2026-11-20T15:26:36.439345+00:00

Read 45 indexed alerts, spanning 2026-10-30 through 2026-11-15. Every eligible object/filter was scored.
6 object/filter groups scored; 1 passed the heuristic variability cut, representing 1 objects.

This is an unclassified review list. No extragalactic discovery is confirmed.

## Selection fixed for this first pass

{
  "database": "scan-watchlist-validation/watchlist.sqlite3",
  "output": "scan-watchlist-validation/verified-final",
  "min_visits": 3,
  "min_nights": 3,
  "min_abs_b": 20,
  "max_scatter": 2,
  "min_fraction": 0.2,
  "min_amplitude": 1000,
  "top": 100
}

Known SSO-associated object groups excluded. Median measurements per visit, then median visit measurements per UTC night, reduce repeated-row weighting. No error bars or formal significance can be recovered from this index.

## Ranked review list

| Object | Band | Nights | Visits | Difference range nJy | Fraction | Watchlist |
|---|---|---:|---:|---:|---:|---|
| 171141216913588260 | i | 5 | 6 | 28935.3 | 0.285 | True |

## Limitations

- Index lacks flux errors, quality flags, template flux, host matches and stellar crossmatches.
- Galactic latitude and positional consistency do not establish an extragalactic identity.
- Score and relative amplitude are heuristic; no statistical significance or false-discovery rate is claimed.
- Alert-only sampling is biased; nondetections and forced photometry are absent. Single-night transients are outside this initial multi-night screen.
- Known SSO labels are excluded, but unlabeled moving objects can remain.

## Next pass

Retrieve original source measurements and flags for shortlisted objects, reject problematic photometry, inspect science/template/difference cutouts, and crossmatch stellar, galaxy and AGN catalogs. Keep known watchlist objects visibly marked. A large science-only rise with stable difference flux is a measurement/reference review flag.

Full scoring is in all-scored.csv. All passing groups are in shortlist.csv; only the detailed JSON and displayed list are capped by --top.

## Selection accounting

{
  "all_source_rows_read": 45,
  "object_groups_seen": 4,
  "too_few_visits": 4,
  "scored": 6,
  "scored_object_filter_groups": 6,
  "candidate_object_filter_groups": 1,
  "candidate_unique_objects": 1
}

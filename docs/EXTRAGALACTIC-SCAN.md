# Broader extragalactic discovery triage

Implemented November 20, 2026. The million-alert run is pending execution on Pots, where the full historical SQLite index lives. This is the first screening stage, not a confirmed extragalactic-candidate catalog.

## Run on Pots

From the repository:

```bash
run_stamp=$(date +%Y%m%dT%H%M%S)
python3 tools/extragalactic_scan.py \
  --database "$HOME/rubin-historical-2026/alerts.sqlite3" \
  --output "reports/2026/11/20/archive-scan-$run_stamp"
```

The scanner uses Python's standard library and reads the existing index without altering it. No alerts are downloaded. It reads every row, excludes catalog-labeled Solar System object groups, and scores every eligible object/filter group. Missing or zero object IDs are not pooled into a fictitious source. IDs stay strings. Filters remain separate. Repeated rows in one visit are reduced before nightly medians, so they do not count as independent visits.

## Initial selection

| Parameter | Default | Interpretation |
|---|---:|---|
| Minimum visits | 3 | Independent indexed visits, after grouping duplicates |
| Minimum UTC nights | 3 | Same-filter multi-night sample |
| Minimum absolute Galactic latitude | 20° | Initial foreground/crowding reduction; not a galaxy classifier |
| Maximum angular offset from group mean position | 2 arcsec | Preliminary positional-consistency gate; not a proper-motion fit |
| Minimum range of nightly median difference flux | 1,000 nJy | Bright-residual screening floor |
| Minimum range / median absolute nightly difference flux | 0.20 | Heuristic variability threshold; denominator floored at 1 nJy |
| Detailed/displayed list | 100 | All eligible and passing groups are still written to CSV |

The ranking is fractional difference-flux range times the square root of the number of nights. It is **not** a statistical significance. The index lacks flux uncertainties, template flux and quality flags. The range is sensitive to outliers. The next pass must retrieve original packet measurements or bounded public histories for shortlisted sources and recheck flags, uncertainties, bright-star artifacts, variability, motion and catalogs. A galaxy/AGN match is not inferred from Galactic latitude.

This initial pass deliberately misses single-night or poorly sampled transients, low-latitude sources and variability below the declared cuts. It does not deduplicate distinct diaObjectIds assigned to the same sky source. The output is conditional on alert selection, association quality and the existing index. It is not a complete census of extragalactic phenomena.

## Outputs

- `report.md` and `report.html`: selection, counts and review list.
- `all-scored.csv`: every scored object/filter group, including non-passing groups.
- `shortlist.csv`: all groups passing the declared variability cuts.
- `results.json`: parameters, counts, detailed top list, original source IDs, nightly medians and hashes of the scanner and ordered input rows.

Watchlist membership is explicitly marked. The algorithm is not restricted to those four objects, but their known changes are useful diagnostic checks.

## Verification so far

Synthetic checks cover a variable source, a constant source, a science-only rise with constant difference flux, a known SSO, negative residual flux, RA wrapping, large exact identifiers and repeated visits. A 45-source real watchlist subset was also exercised; PGC's historical i-band difference range passed the heuristic cut. That is a validation sample, not an archive-wide result or new discovery. Its longer-range residual variability can pass even though its latest difference flux is nearly unchanged.

Original index schema comes from `src/historical/historical-original-2026-11-19.py`. The full index on Pots must be used to obtain full-archive counts and a review shortlist beyond the known targets.

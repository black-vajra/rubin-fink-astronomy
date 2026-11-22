# Extragalactic review · 2026-11-21

Generated 2026-11-22T01:27:20+00:00.

**No new observations or changed returned source records in the four queried watchlist histories.** Measurements below remain historical; the assessed interval starts July 16, 2026 and extends through this retrieval, rather than silently stopping the analysis at November 15.

| Object | Band | Unique points since July 16 | Latest UTC | Latest science / earlier median | Latest difference / earlier median |
|---|---|---:|---|---:|---:|
| PGC 766016 | i | 6 | 2026-11-15T05:31:12.579 | 1.477 | 0.981 |
| PGC 766016 | r | 2 | 2026-11-13T06:17:26.671 | 0.899 | 0.867 |
| Quasar crossmatch | i | 8 | 2026-11-15T05:30:32.245 | 1.048 | 0.936 |
| Science-image high | g | 8 | 2026-11-13T05:26:59.208 | 0.979 | 0.975 |
| Science-image high | i | 7 | 2026-11-15T05:33:18.561 | 1.124 | 0.978 |
| Science-image high | r | 8 | 2026-11-14T04:55:23.383 | 0.925 | 0.960 |
| Science-image high | z | 3 | 2026-11-08T07:58:55.786 | 1.020 | 1.012 |
| AT 2019hkw | i | 1 | 2026-11-12T01:19:40.773 | — | — |
| AT 2019hkw | r | 1 | 2026-11-15T00:35:36.762 | — | — |
| AT 2019hkw | z | 1 | 2026-11-12T01:56:57.870 | — | — |

Ratios compare alert-selected samples in the same filter. They are descriptive comparisons, not variability significances. One-point bands cannot support a same-band trend.

## New archived-image sensitivity test

The retained November 11/13/15 PGC cutouts were refitted over a fixed grid: radii 6/10/14 pixels, constant/planar backgrounds, uniform/inverse-variance weighting. All twelve results per cutout are retained.

| UTC date | Difference-image amplitude range, nJy | Median across choices, nJy |
|---|---:|---:|
| 2026-11-11 | 93,187–101,489 | 100,011 |
| 2026-11-13 | 88,670–107,804 | 100,119 |
| 2026-11-15 | 94,477–106,633 | 105,142 |

The ranges overlap, but that is not a formal statistical test. The spread across methods measures fitting sensitivity, not a calibrated uncertainty. The reported science-image rise is not sufficient to assign a nuclear flare.

The supplied FITS do not provide an explicit mask-bit dictionary; no generic mask mapping was guessed. Nuclear/host decomposition, independent calibration and inter-pixel covariance remain unresolved. The full diagnostic and file hashes are in [PGC fit sensitivity](pgc-fit-sensitivity/report.html).

Next: establish product-specific mask semantics and usable photometric calibration before interpreting a cross-epoch nuclear light curve. No additional extragalactic discovery scan ran on the unchanged archive in this review.

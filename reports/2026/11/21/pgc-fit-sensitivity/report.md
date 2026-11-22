# PGC 766016 · image-fit sensitivity

2026-11-22T00:58:46.597779+00:00

**Archived-image diagnostic only.** Twelve fixed choices per cutout: fit radius 6/10/14 pixels, constant/planar background, uniform/inverse-variance weighting. Supplied PSFs retain total-flux normalization. Finite image and positive variance pixels are used; masks are not semantically decoded.

| UTC date | Image | Minimum amplitude nJy | Median nJy | Maximum nJy |
|---|---|---:|---:|---:|
| 2026-11-11 | Difference | 93,187 | 100,011 | 101,489 |
| 2026-11-11 | Science | 664,038 | 725,235 | 813,767 |
| 2026-11-11 | Template | 524,340 | 577,785 | 630,659 |
| 2026-11-13 | Difference | 88,670 | 100,119 | 107,804 |
| 2026-11-13 | Science | 706,713 | 796,326 | 875,511 |
| 2026-11-13 | Template | 505,104 | 564,484 | 615,777 |
| 2026-11-15 | Difference | 94,477 | 105,142 | 106,633 |
| 2026-11-15 | Science | 840,383 | 904,388 | 947,058 |
| 2026-11-15 | Template | 539,385 | 589,642 | 641,062 |

These amplitudes measure a chosen PSF-plus-background model, not total galaxy luminosity. Cross-date ranges may reflect source structure, PSF/background choices, subtraction residuals or calibration. No significant-change claim follows from this grid.

## Remaining measurement gate

All nine retained FITS products were checked for MP_ or MSKN mask-schema cards. Their absence leaves a mask-interpretation dependency; generic defaults are not assigned to these particular packets without provenance. Image-level photometric validation remains incomplete.

## Limitations

- Nonzero mask bits are counted, not interpreted or rejected: the supplied FITS omit a mask-bit dictionary.
- No nuclear/host decomposition, reference matching, inter-pixel covariance or independent photometric calibration.
- The spread across choices is model sensitivity, not a statistical uncertainty or a confidence interval.
- Same archived November 11/13/15 images; no new observations or flare confirmation.

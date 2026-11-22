# 2026 ED138 · public astrometry benchmark

2026-11-22T00:58:04.195329+00:00

**Historical benchmark, not new overnight observations.** Native public MPC observations were retrieved successfully; the Fink query failure is not an absence-of-astrometry result.

Parsed **74** MPC observations: **44 W84** DECam precoveries and **30 X05** Rubin positions on **20** dates. Only the Rubin subset is fitted here; the precoveries are retained for later work. No Fink alert IDs or visit IDs are invented.

Training cutoff fixed before numerical scoring: **UTC < 2026-06-13**. Training: **25 positions on 17 dates**; withheld: **5 positions**. All trial outcomes are retained. Published target orbital elements and all withheld positions are excluded from initialization and optimization.

Model: existing six-state heliocentric Sun-only fitter; Rubin observer motion and iterated light travel time. Uniform assumed 0.15 arcsec per-coordinate errors; existing fixed 60 arcsec search gate. Retrospective known-object test, not a blind discovery or a replacement catalog orbit.

| Withheld UTC | Band | Miss (arcsec) | Inside 60 arcsec? | Formal 95% prediction semiaxes (arcsec) |
|---|---|---:|---|---|
| 2026-06-27T05:23:48.336+00:00 | i | 0.027 | True | 0.501 × 0.224 |
| 2026-07-09T04:04:54.307+00:00 | i | 0.043 | True | 0.794 × 0.289 |
| 2026-07-09T04:49:07.046+00:00 | r | 0.038 | True | 0.795 × 0.289 |
| 2026-07-11T06:43:24.182+00:00 | r | 0.039 | True | 0.852 × 0.300 |
| 2026-07-11T07:21:14.515+00:00 | g | 0.075 | True | 0.853 × 0.300 |

Training position RMS: **0.0284 arcsec**; maximum **0.0907 arcsec**.

Exploratory heliocentric elements at JD 2461103.898887757 TDB: a=42.9578 AU, e=0.1431. These are not directly comparable to quoted barycentric elements without transforming definitions and epochs.

## Limits and next steps

This initial model omits planetary perturbations, mutual/body-specific motion, correlated astrometric errors and image-level biases. The MPC rounded positions lack per-observation uncertainties here. Formal ellipses are conditional on an assumed error model and one local branch, not calibrated coverage. This report neither identifies all orbit solutions nor measures size/mass or a resonant classification.

Next: compare with an established orbit fitter and a planetary force model, then consider independent W84 precoveries with station-specific geometry. The restricted Rubin RSP image/catalog release is not used. Public MPC astrometry is a distinct data product.

Source: https://www.minorplanetcenter.net/mpec/K26/K26U85.html
Rubin data-product access distinction: https://prompt-products.lsst.io/products/2026-ED138/index.html

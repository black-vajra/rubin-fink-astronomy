# QY297 · ADAM archive reconciliation
Reporting date November 21, 2026 (America/New_York).
Generated 2026-11-22T02:02:52.052082+00:00. Run 632d9656-be94-468f-a230-1d726201b600.
## Accounting
408 exported rows: 342 MPC, 56 NSC/DECam (W84), 10 Rubin (X05). These are catalog rows, not 408 independent exposures.
All 347 pasted search spans are marked complete. Their accepted counts sum to 295; this differs from export rows. The export mixes attributed MPC records and accepted survey detections; exact accepted/recovered/new accounting needs the ADAM detailed-accounting export.
## Duplicate screen
Same station, within 2 seconds and 2 arcseconds: 0 matching pairs. This is a screening definition, not proof that every remaining row is independent.
All 56 DECam rows have distinct exposure IDs and span 13 UTC nights. No W84 observations occur in the supplied MPC rows, so none can be matched to an MPC row at that station. This does not certify they are unpublished: the supplied MPC snapshot may omit observations or use other attribution.
The ten Rubin source IDs exactly equal our retained Fink set: True. They add no new Rubin detections.
## DECam measurement inspection
All 56 rows include coordinate uncertainties, magnitude uncertainties, band, and exposure identifiers. All lack seeing/FWHM and image-mask/centroid quality flags in this export. An object_id is assigned throughout this target-filtered export; it is not independent evidence of MPC attribution. No image confirmation or calibrated astrometric validation has yet occurred.
| UTC night | Rows | Bands | Position span, arcsec |
|---|---:|---|---:|
| 2013-08-02 | 4 | z | 0.307 |
| 2017-08-22 | 1 | g | 0.000 |
| 2017-09-22 | 1 | r | 0.000 |
| 2018-08-09 | 1 | r | 0.000 |
| 2018-08-30 | 1 | g | 0.000 |
| 2018-09-11 | 1 | r | 0.000 |
| 2018-09-14 | 1 | z | 0.000 |
| 2018-09-15 | 1 | z | 0.000 |
| 2018-09-17 | 1 | z | 0.000 |
| 2019-08-10 | 1 | i | 0.000 |
| 2019-08-26 | 12 | g,i,z | 14.329 |
| 2019-10-24 | 2 | i | 0.053 |
| 2019-10-25 | 29 | i,r | 2.243 |
## Available image investigation
Queried the documented NOIRLab NSC DR2 SIA endpoint at all 13 nightly positions. Returned image rows: 357; failed queries: 0. XML responses and request URLs are retained. An empty result does not establish that original DECam images are unavailable elsewhere.
No image pixels were supplied in the two Parquet files. Retrieved 1 science detector image(s) from 1 exposure/band/detector-matched requests; 0 failed. See retained FITS, image-checks.json and contact sheet. The service returned a full detector image despite the small cutout request. Locally cropped a 121-pixel square for inspection. Raw detector FITS is retained under data/raw/qy297-adam (excluded from Git); its hash and retrieval URL are recorded. Pixel positions were checked using the image WCS; no new centroid fit or independent orbit residual was measured.
## Suitability for independent orbit tests
The 56 DECam rows are provisionally useful inputs, pending image checks and astrometric validation. Use W84 observer geometry, UTC-to-TDB conversion, and exposure-time semantics verified for NSC. Do not guess the timestamp offset from the exposure filename. Quoted uncertainties need unit/convention verification and a systematic-error floor; same-night measurements may be correlated.
Do not feed the exported JPL state or covariance into the independent fit. Selection of these candidates already used the JPL orbit, so a test using them is a retrospective known-object benchmark, not blind discovery.
Recommended next experiment: freeze a training cutoff before the first Rubin epoch; fit validated pre-2026 observations with a planetary-perturbation-capable fitter and hold all ten 2026 Rubin observations out. Define uncertainty and rejection rules using training data. Preserve the earlier November 12 benchmark unchanged. The present Sun-only model is not an adequate precision benchmark for a 13-year extrapolation without an established-fitter cross-check.
No new orbital fit or mass estimate was performed here. Unresolved centroids do not determine the binary mutual orbit.
## Sources
[NOIRLab NSC documentation](https://datalab.noirlab.edu/data/nsc)
[ADAM Precovery](https://b612.ai/adam-platform/precovery/)
## Matched cutout inspection
Exposure matching uses timestamp prefix, band and detector. Processing-version suffixes can differ, so matching exposure does not certify the identical NSC reduction.
The August 9, 2018 r-band image shows a compact source at the NSC position, without an obvious blend at the displayed scale. A single epoch cannot establish motion or identity, or resolve the binary. No new centroid or signal-to-noise measurement was fitted. Mask and weight products were not inspected.
DATE-OBS is 2018-08-09T04:10:48.122410 and EXPTIME is 40 seconds. The catalog timestamp 04:11:08.122442 agrees with mid-exposure within 0.000032 seconds. This check applies only to this exposure.
## Proposed frozen experiment
The proposed plan in test-plan.json uses the 56 NSC rows before January 1, 2020 as training candidates after image validation; all ten 2026 Rubin observations remain withheld. The 60-arcsecond project gate is retained. No new fit ran in this task.

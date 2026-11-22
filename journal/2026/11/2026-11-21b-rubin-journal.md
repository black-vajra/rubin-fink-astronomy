# Rubin journal · November 21, 2026 · b

## QY297 ADAM precovery follow-up

User signed in and submitted ADAM run 632d9656-be94-468f-a230-1d726201b600 for 275809 (2001 QY297), September 1, 2012–November 22, 2026 UTC using JPL SBDB. All 347 supplied span records are complete; accepted counts sum to 295. The filtered export has 408 rows; these accounting measures are not interchangeable.

Audited 342 MPC rows, 56 NSC/DECam W84 rows on 13 nights in 56 distinct exposures, and ten Rubin X05 rows. Normalizing the ADAM lsst: ID prefix proves all ten Rubin IDs match the retained Fink history. No new Rubin detections. A same-station, within-two-seconds/two-arcseconds duplicate screen finds zero pairs. No W84 rows occur in this MPC export; the 56 NSC rows are additions to our working data, not established unpublished observations.

Queried NSC DR2 SIA at 13 nightly positions; 357 image-product rows across overlapping positions (not deduplicated), zero request errors. Eight candidate exposures match available science-product exposure prefixes, band and detector. Initial eight cutout attempts hit a 2 MB cap because the endpoint returned full detector images. Retried one with a 36 MB cap, obtaining a 33,531,840-byte detector image; the original is under data/raw/qy297-adam and excluded from Git. Hash and URL are retained. A local 121-pixel crop shows a compact source at the August 9, 2018 NSC catalog position without an obvious blend at the display scale. This is not independent orbit or motion confirmation. Its FITS header verifies the catalog timestamp is the 40-second exposure midpoint. Other epochs remain unvalidated.

## Next objectives and limits

Validate remaining images, masks, catalog uncertainty conventions and time semantics. Reconcile ADAM accepted/recovered/new counts using detailed accounting. Proposed experiment: approved pre-2020 NSC measurements as training, all ten 2026 Rubin detections withheld, existing 60-arcsecond gate. Use planetary perturbations, observer geometry, light time, alternative orbit branches and an established-fitter cross-check. Do not initialize the independent fit from the supplied JPL target state/covariance. Candidate selection used that external orbit and remains a retrospective known-object benchmark.

No new orbit fit, binary mutual-orbit solution, mass measurement, or additional-object search ran. Research scope remains the four named controls. No GitHub push was performed in this task.

Report: reports/2026/11/21/qy297-adam-reconciliation/report.html (self-contained image included).

# Rubin daily journal · November 19, 2026 · second entry

## Historical archive acquired and imported on Pots

The compact historical transfer completed on Pots, the Z890 running Kubuntu as pepper. All **1,043,458 unique valid detections** were indexed in the selected July 16–November 15 UTC interval. Each of the 13 nightly counts matched Fink's published statistics. Actual detections cover October 30–31 and November 5–15. This is the available coverage in the export; the requested four-month interval does not imply four months of continuous data.

The selected Avro fields occupy approximately **2.6 GB** on disk, exceeding the portal's 1.39 GB estimate. The project is at `~/rubin-historical-2026`, its packets at `alerts/ftransfer_lsst_2026-11-19_639723/`, and its SQLite index at `alerts.sqlite3`. Import and report generation finished successfully.

The expanded moving-object report combines **236,428 archive measurements of 75,018 cataloged object IDs** with **46,050 measurements in 29,038 named snapshot entries**. The displayed combined total of 104,056 includes overlap between these sources. Likewise, the slow shortlist includes **557 archive entries plus 208 snapshot entries** with overlap. These combined counts need clearer labels or deduplication. The report's statement that the compact transfer is still required is stale now that import has finished.

## Extragalactic work

The complete archive added no new unique detections for the four watchlist objects beyond the retrieved Fink histories. PGC 766016 still has six i-band and two r-band detections. Its latest i-band science flux is about **48% above the earlier median**, while its difference flux is essentially unchanged.

Inspection of the retained PGC packet metadata provided a concrete follow-up lead.

| UTC date | Science flux, nJy | Template flux, nJy | Difference flux, nJy | Detector |
|---|---:|---:|---:|---:|
| November 11 | 787,642 | 682,856 | 101,592 | 178 |
| November 13 | 892,683 | 787,698 | 101,571 | 160 |
| November 15 | 1,168,054 | 1,058,652 | 99,608 | 121 |

The measured template flux increases alongside the science flux, with different detectors in these visits. This strengthens the need to inspect measurement, reference and calibration effects before describing the science-image rise as a nuclear flare. It does not yet identify the cause. Science and template fluxes should not be treated as independent confirmation of an intrinsic rise. Image cutouts and the detailed reference/measurement comparison remain pending. The similar science/difference discrepancy in 313862200773574662 is also worth checking.

## Slow-control tests and model failures

Two cataloged controls were tested against every alert on later nights using a **60 arcsecond search radius fixed before scoring**.

The October 30 straight-line predictions failed over 13–16 days. For **2014 WV203**, the error was **2,628.97–2,629.48 arcseconds** on November 12 and **3,833.02 arcseconds** on November 15. For **2013 CR7**, it was **2,497.75 arcseconds** on November 12. Both November 12 prediction searches admitted one unrelated alert inside 60 arcseconds. A position-only acceptance rule would have made a false association.

The initial benchmark extrapolated a short one-night motion fit too far. WV203's measured rate increased from **0.00429 arcsec/min on October 30** to **0.25396 arcsec/min on November 12**. The November rate uses only two detections over 2.05 minutes and is sensitive to positional errors. CR7 had only one November 12 detection, so its rate that night cannot be measured from this batch.

Using October 30 plus November 12 training observations for WV203 improved the November 15 prediction. The linear fit missed by **610.045 arcseconds** and ranked the control 28th among 138,867 alerts. The quadratic fit missed by **122.979 arcseconds** and ranked it third. Both failed the fixed 60 arcsecond radius. The quadratic fit is an empirical extrapolation; a physical orbit fit remains to be implemented.

## Independent JPL recovery succeeded

The new `slow-control-recovery.py` requests independent JPL Horizons astrometric ICRF predictions from Rubin's observing location, converts alert TAI timestamps to UTC, and searches all visits on the test nights. It recovered all four later labeled detections.

| Control | Test night | Recovery | Rank among all nightly alerts | Position error |
|---|---|---|---|---|
| 2014 WV203 | November 12 | 2/2 | 1 and 2 of 235,039 | 0.060″ and 0.086″ |
| 2014 WV203 | November 15 | 1/1 | 1 of 138,867 | 0.034″ |
| 2013 CR7 | November 12 | 1/1 | 1 of 235,039 | 0.013″ |

The WV203 November 12 search admitted three alerts inside 60 arcseconds, including one unrelated detection. Detector footprints are still needed for a coverage-normalized false-match test.

These checks validate the time conversion, observing location and positional matching for the tested controls when an external known orbit supplies predictions. Predicting an unknown object's orbit from our own earlier detections remains a separate development task.

The user ran the script successfully on Pots. It saves `~/rubin-historical-2026/slow-control-recovery.md` and an HTML copy, with cached Horizons responses in `ephemeris-cache/`. [JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html)

## Add 2026 ED138 as a distant-body control

The initial Fink-derived shortlist omitted ED138. It belongs in the named distant-object control list, and its dedicated observations justify extending the date window for this target.

Rubin's dedicated release covers **March 4–July 11, 2026**, preceding our July 16 start. The images and catalogs require Rubin data rights. The astrometry submitted to the MPC is public. Fink's name resolver rejected “2026 ED138” during our check, which does not establish absence from every Fink dataset. Public astrometry retrieval and ingestion into our control workflow remain pending. No ED138 recovery test has run. [Rubin ED138 release and coverage](https://prompt-products.lsst.io/products/2026-ED138/index.html)

## Development objectives on resumption

1. **Fit physical orbits from earlier detections and withhold later observations.** Start with the known controls, include observer motion and light-time handling, quantify uncertainty and compare predictions against the established JPL recovery results. Retain the failed linear and quadratic results as baselines.
2. **Obtain verified usable detector footprints.** Score fixed-radius prediction and comparison circles inside actual observed detector area, accounting for masks and reporting excluded visits. Positions of alerts alone do not define coverage.
3. **Extend validated linking to unassociated detections.** Establish false-association controls and sensitivity to different motion rates and time gaps before interpreting distant-body candidates.
4. **Integrate ED138.** Retrieve permitted public astrometry, record source and epochs, extend the target-specific interval, and determine what image/catalog access is available.
5. **Inspect PGC 766016 images and reference measurements.** Compare November 11, 13 and 15, with emphasis on November 13–15. Review seeing, detector, calibration, template measurement and available flags. Check 313862200773574662 for related effects.
6. **Correct historical report bookkeeping.** Deduplicate or clearly separate snapshot/archive populations, label API-plus-archive counts accurately, and replace stale acquisition text with verified import status.
7. **Calibrate conditional size and mass ranges.** Use independently known objects and suitable distances and calibrated photometry. Record albedo, density and band-conversion assumptions. No mass estimate or Planet Nine identification has been produced.

## Operating state at pause

The user is switching to Sable development. Overnight Fink collection remains scheduled on Pots/Kubuntu from **17:00 to 09:00 America/New_York**, with reports at **09:00 and 09:10**. The first updated research script was initially missed because numbered downloads contained the newer file; installation was subsequently verified by the strict-benchmark section appearing in the report.

Rubin's November 17 notice attributed the camera shutdown to loss of cooling capacity on November 15. The camera was reported safe, with troubleshooting continuing. No confirmed restart time was established in this session. Historical analysis can continue using saved data during the outage. [Camera status notice](https://www.rubin.community/t/rubin-status-november-17-2026/12959)

This file contains only the second November 19 session entry. Earlier journal files remain the record of prior sessions.

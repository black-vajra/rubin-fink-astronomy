# Rubin research journal · November 21, 2026

## Overnight review

Reporting date is November 21 in America/New_York; the preparation timestamps fall after midnight November 22 UTC. The assessed collection window is November 20 17:00 through November 21 09:00 EST.

User-supplied Pots logs confirm that the collector started at 19:26:23 EST and stopped at 09:00:01. The 2 h 26 min late start is consistent with the established dual-boot routine. Its reported 626.4-minute gap includes the scheduled daytime shutdown and is not a measured number of missed messages. Kafka group/heartbeat/fetch timeouts occurred around 07:21 and 07:32; they are communication interruptions, distinct from the telescope status.

The bright-object report ran successfully at 09:00, reporting 60 detections and zero file errors. Morning research ran successfully at 09:10 and finished at 09:10:12. Both latest.html modification times agree. A follow-up user-supplied inbox check confirmed **zero new Avro files** in the assessed window; the newest five files remain dated November 15 at about 22:47 local filesystem time. Successful report generation therefore summarized existing inputs, not a new overnight catch.

Fresh public checks made nine small Fink queries. Eight succeeded: November statistics, four extragalactic histories, and QY297/WV203/CR7 histories. All seven successful histories have unchanged source IDs and unchanged returned records against saved November 20 responses. None returns a non-withdrawn observation in the assessed overnight window. November statistics still end at key 20261115. The ED138 Fink query returned HTTP 400; it was not labeled a successful empty history.

The retrieved Rubin homepage displays a temporary off-sky notice. The latest formal cooling notice found in the reviewed News category remains dated November 17; no new return-to-sky date was established in this check. Absence of a statistics entry is not independently treated as proof that a field had no visit.

## Extragalactic work

The four watchlist histories were refreshed. PGC 766016 retains the same six i-band alerts: latest science flux is 1.477 times the earlier median and difference flux 0.981 times it. These descriptive comparisons do not establish a nuclear flare.

A new archived-image diagnostic fits each retained November 11/13/15 PGC cutout with twelve preselected combinations: fit radii 6/10/14 pixels; constant or planar background; uniform or inverse-variance weighting. Difference-image amplitudes span 93,187–101,489 nJy on November 11; 88,670–107,804 on November 13; and 94,477–106,633 on November 15. The overlap is not a significance test, and the spread is model-choice sensitivity rather than calibrated uncertainty.

All nine supplied FITS were checked for explicit mask-schema cards; none was found. No generic bit mapping was guessed. Mask semantics, independent photometric calibration, nuclear/host separation and correlated-pixel noise remain gates for certified photometry. No new broad discovery scan ran on the unchanged archive.

## ED138 public astrometry and physical prediction

The public Minor Planet Center circular MPEC 2026-U85 was retrieved successfully. Its native 80-column records contain 74 observations: 30 Rubin/X05 positions on 20 dates (March 4–July 11, 2026), and 44 DECam/W84 precoveries on 14 dates (February 25, 2016–April 7, 2023). All are retained as native records and CSV/JSON with observatory codes and source line numbers; no Fink source/visit identifiers were invented.

A June 13 UTC training cutoff was fixed before numerical scoring. The existing Sun-only physical fitter used 25 earlier Rubin positions on 17 dates and withheld five later positions on June 27, July 9 and July 11. No target catalog orbit, published orbital elements, W84 precoveries or restricted Rubin images entered this fit. Held-out errors were 0.027, 0.043, 0.038, 0.039 and 0.075 arcsecond, all within the unchanged 60-arcsecond gate. Training position RMS was 0.0284 arcsecond.

This is a retrospective known-object benchmark. It uses observer motion and light travel time but omits planetary perturbations; assumed 0.15-arcsecond coordinate errors and local covariance do not supply globally calibrated confidence. No precision replacement orbit, new discovery, resonant classification, size or mass is claimed. The old ED138 public-astrometry acquisition gate is now completed. The W84 precoveries remain available for a separately declared multi-site validation exercise.

QY297 remains the primary moving-object research target. Its existing Sun-only benchmark was not rerun and is not presented as a new orbital solution. The next numerical gate remains planetary dynamics and an established-fitter/global-uncertainty comparison.

## Methodology and data-source follow-up

The user's discovery-announcement excerpt prompted review of the linking/precovery workflow and its source-access boundaries. The practical follow-up is a targeted archive plan for the same four objects, with image validation and explicit distinction between external-orbit recovery and independently fitted predictions. Details and primary-source links are in reports/2026/11/21/methods-and-data-sources.md. No authenticated ADAM search was submitted.

Moving-object scope remains QY297, WV203, CR7 and ED138. No additional objects or whole-survey downloads were introduced. The restricted RSP image/catalog release was not accessed. New data retrieval was confined to small public responses, public MPC records and observer geometry.

## Reports, validation and remaining work

The dated overnight overview, both science reports, raw Fink responses and hashes, user-supplied host-event summary, PGC fit grid, native ED138 observations, geometry queries, trial logs and held-out predictions are retained under reports/2026/11/21/.

Four new tests cover native record counts/calendar/stations, independent sexagesimal coordinate conversion, exclusion of non-observation orbital text, and exact large source IDs/revision detection. The existing four physical-model numerical/information-isolation tests were also run. The new reports distinguish freshness from observation dates and archived-data analysis from new detections.

Local packet-count evidence is now completed. Next: investigate Kafka connectivity if it persists; validate product-specific masks/calibration for PGC; add planetary dynamics and independent orbit-fitting checks for the named movers; examine targeted archive access and precovery image validation. Further work on QY297 binary physics remains a separate discussion. No push or release publication is asserted for this new session.

## Report-delivery correction before publication

The user could read the two primary science reports but could not open four linked appendices. The first three used companion-folder relative links, and the methods note was Markdown only. Standalone HTML copies and a single self-contained complete-review.html now embed all seven report sections, the 74-row public-observation table and selected JSON provenance/trial data. Internal link targets and absence of companion-resource dependencies were checked.

One stale sentence in the freshness appendix still said the local file count was pending. It is corrected to the supplied zero, and the ED138 HTTP 400 is explicitly identified as a failed query rather than a successful empty result. The renderer was tested through two rebuilds to confirm those corrections persist. Source observations and numerical results are unchanged by this delivery correction.

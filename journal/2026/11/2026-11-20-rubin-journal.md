# Rubin daily journal · November 20, 2026

This file contains only today's entry. Earlier dated journal files remain unchanged.

## Observatory status

The official sources checked earlier today still reported Rubin temporarily off sky. The latest repair-specific notice found was November 17. It described loss of pumped-coolant cooling capacity on November 15, a camera shutdown, a safe camera and continued troubleshooting. No confirmed completion or observing-resumption date was found. This does not establish the precise component that failed or a repair duration.

Sources: https://www.rubin.community/t/rubin-status-november-17-2026/12959 and https://rubinobservatory.org/ .

## Reports generated and freshness checked

Fresh public Fink queries succeeded for November statistics, all four extragalactic watchlist objects, and both named slow controls, 2014 WV203 and 2013 CR7. None of these six source histories added or removed a diaSourceId compared with the saved November 19 responses. November statistics still end on November 15. Exact parameters, UTC query times, response hashes and source-ID comparisons are retained in refresh-provenance.json.

Generated two dated reports, each in Markdown and HTML, with new provenance and a PGC science/template/difference table. Corrected misleading acquisition wording and separated the cached SSO snapshot population from the full archive. The public snapshot scan contains 46,050 measurements in 29,038 entries, spanning October 30–31, with 208 training shortlist entries. These are not the combined archive population and are not newly discovered objects.

The 1,043,458-source SQLite archive and 2.6 GB of compact Avro remain on Pots. This reporting workspace has the saved small histories and monthly SSO products, but not that database. Today's work therefore did not repeat all-alert held-out scoring or inspect the latest local overnight collector files. The successful API checks do not certify the state of Pots' services or every possible Fink dataset. No bulk alert download was performed.

## Extragalactic findings

PGC 766016 still has six in-window i-band detections and two r-band detections. Its latest i-band science flux is 1.477 times the earlier median, while its difference flux is 0.981 times the earlier median. Template flux rises alongside science flux in the retained measurements, across different detectors. This remains a measurement/reference/calibration question before claiming intrinsic nuclear brightening. Today's table reproduces those packet values; no image-cutout or forced-photometry analysis ran.

The quasar crossmatch remains modestly changed in its sparse i-band sample. Object 313862200773574662 shows a related science/difference discrepancy worth reviewing. AT 2019hkw still has only one in-window measurement per returned band, limiting trend inference.

## Moving-object findings

Neither slow control acquired new returned source IDs. The report carries forward the November 19 JPL-based all-alert recovery of four out of four labeled later detections, with errors 0.013–0.086 arcseconds. Those are earlier verified results, not new tests today.

Known-orbit positional matching succeeded. Independent orbit prediction from our own short training arcs remains unvalidated. Linear extrapolation failed over long gaps; the WV203 quadratic fit also failed the preselected 60 arcsecond radius. One JPL search admitted an unrelated alert inside that radius, so a nearby positional match alone is insufficient.

## Objectives and assessment

The objectives remain reasonable in the following order.

1. Extragalactic: inspect PGC's November 11, 13 and 15 science/reference/difference images and associated seeing/calibration metadata; compare the second object's discrepancy. Obtain permitted image access before interpreting missing cutouts.
2. Moving objects: fit a physical orbit using training detections only and score withheld later observations against the JPL baseline. Include observer motion and uncertainty. Do not enlarge the acceptance radius after seeing a miss.
3. Obtain verified usable detector footprints and place comparison circles inside comparable observed area, accounting for masks. Alert positions alone do not establish that coverage.
4. Add 2026 ED138 through permitted public MPC astrometry. Its dedicated March 4–July 11 observations precede the general archive's July 16 start, so use a target-specific interval.
5. After the controls and false-match tests pass, extend linking to unassociated detections and report sensitivity and selection limits.
6. Keep size/mass estimates conditional on suitable distance, calibrated photometry, albedo and density assumptions. No size/mass estimate or Planet Nine search ran today.

The useful change in priority is to work on interpretation and validation with existing data while Rubin is offline. Repeatedly regenerating unchanged histories provides freshness monitoring, but does not itself advance those analyses.

## Configuration and operating schedule

The previously configured Pots/Kubuntu collection window is 17:00–09:00 America/New_York, with report jobs at 09:00 and 09:10. These are the recorded settings; systemd units and boot behavior were not inspected today. No timer or installed script was changed on Pots in this session. No extra bulk download or schedule change is required solely because today's returned histories are unchanged.

The dated reports and provenance are separate deliverables. Changes made to reporting copies here have not been installed into the nightly services on Pots.

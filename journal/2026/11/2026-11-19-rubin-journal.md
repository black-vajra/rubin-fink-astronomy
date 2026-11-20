# Rubin daily journal · November 19, 2026

## Camera outage explains the data cutoff

Rubin's November 17 operational notice reports that the pumped coolant system lost cooling capacity on Sunday, November 15. The system cools camera electronics inside the cryostat. The camera was shut down safely and remained shut down while the issue was investigated. The public observatory page checked November 19 also reported that Rubin was temporarily off sky for a technical issue. We have no confirmed repair or restart time. [Rubin status notice](https://www.rubin.community/t/rubin-status-november-17-2026/12959) · [Observatory status](https://rubinobservatory.org/)

This aligns with Fink's lack of published statistics entries after November 15. Our morning reports were refreshing older observations. Collector idleness during this outage is expected. Retaining the enabled overnight schedule allows collection to resume when data return.

## Morning automation and installed update

The bright-alert report generated at 09:00 EST with 60 detections, 42 objects or ungrouped detections, zero file errors and a newest-observation age of 4 days 9 hours. The research report generated at 09:10 EST and reproduced the PGC history and known-object controls.

The first research run still used the earlier script. Two browser downloads with numbered filenames contained the update. The user installed the numbered copy and regenerated at 09:58:54 EST. The new strict benchmark section appeared and correctly reported pending controls and verified footprints. Installation is now verified. The first scheduled run of that updated version is still ahead.

## Historical Research project opened

A separate workstream now covers all available Fink LSST alerts from **July 16 through November 15, 2026 inclusive**. The dates are our chosen interpretation of the requested four-month period. It covers extragalactic variability and moving-object recovery, with later conditional size/mass estimates and distant-body candidate analysis.

Five monthly statistics queries returned **13 nights with entries in the selected interval**, totaling **1,043,458 alerts**. The listed nights run from October 30–31 and November 5–15. Empty entries in the earlier portion remain unknown coverage; the dataset is not a continuous four-month observing sequence.

An initial all-field request was submitted with a 136.33 GB estimate. The user clarified the desired practical scale before any of that export was downloaded locally. The replacement request keeps every alert and selects **diaSource, diaObject, ssSource and mpc_orbits**, estimated at **1.39 GB**, topic **ftransfer_lsst_2026-11-19_639723**. The earlier topic **ftransfer_lsst_2026-11-19_268035** is superseded for our download workflow. Pots has yet to retrieve the compact topic using its existing credentials.

## Data obtained and reports generated

All returned fields for four public watchlist histories were downloaded and retained. The selected-window counts are **8** alerts for PGC 766016, **8** for 313774266976305153, **26** for 313862200773574662, and **3** for 170653056044630027. Reports compare positive fluxes by filter, keeping science and difference measurements distinct. They retain the source JSON for uncertainties, flags and later review. PGC's latest i-band science flux is **1.477 times** its earlier median, while its difference flux is **0.981 times** its earlier median. This repeats the unresolved science/difference discrepancy.

Fink's all-known-Solar-System bulk snapshot downloaded successfully at approximately **41.8 MB**. The November snapshot contains **145,133 cataloged object rows** across its full date range. Filtering to our selected interval gives **46,050 measurements for 29,038 objects**, spanning **October 30–31 UTC**. Its monthly update explains the absence of November measurements from this particular snapshot. The compact alert export supplies the needed later observations.

The training-only scan selected slow-control candidates using at least three detections over at least 30 minutes on one UTC date, a fitted rate of **0.001–0.1 arcsec/min** and a maximum residual of **1 arcsec**. One candidate, **2014 WV203**, has an apparent rate of about **0.00429 arcsec/min** and fit residual **0.036 arcsec**. Slow apparent motion alone does not establish great distance. Independent test observations, known-object identification and real usable visit coverage are still required before recovery scoring.

## Next actions

1. Download and verify the complete compact topic on Pots, then build the transactional local alert index and regenerate the historical reports.
2. Use the expanded cataloged detections to resolve the slow-control shortlist and find independent test nights. Apply fixed search radii and documented usable detector footprints.
3. Review PGC's image/reference/calibration context and the other watchlist histories. Expand to archive-wide extragalactic triage after ingestion.
4. Extend validated linking to unassociated detections. Record uncertainties and follow-up predictions for credible distant-body candidates.
5. Calibrate conditional size and mass estimates using known objects with suitable distance and photometric information. No mass estimate or Planet Nine candidate identification was produced in this session.

The historical reports and reproducible scripts are delivered as a separate project package. Live timer operation remains on Pots' Kubuntu installation.

The two slow-control histories were subsequently resolved through Fink. **2014 WV203**, ssObjectId **21164724125905750**, has four October 30 detections, two November 12 detections and one November 15 detection in our window. **2013 CR7**, ssObjectId **21164719493625682**, has three October 30 detections and one November 12 detection. Returned heliocentric distances are approximately **2.3–2.5 AU**, demonstrating that very slow apparent motion can occur for comparatively nearby bodies. These give concrete held-out November tests once the compact dataset and usable footprints are available.

The aggregate SSO phase-model table also downloaded successfully, approximately **10.5 MB** with **62,780 rows**. Its filter-specific absolute magnitudes require calibration and fit-quality review before size or mass scenarios. The reproducible importer was checked for repeat ingestion, exact large integer identifiers, duplicate handling and malformed Avro failure.

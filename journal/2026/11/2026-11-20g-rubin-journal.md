# Rubin research journal · November 20, 2026 · g

## Session closeout

The user requested final archiving, commit and publication of the astronomy work, including downloads, test results, reports and journal finalization. The physical-orbit entry is **November 20f**, as directed by the user. The earlier QY297 entry **e** is preserved separately. This **g** entry closes the current session.

## Work completed

- Preserved the archive-wide extragalactic scan, source-response snapshots and PGC image/reference investigation, including quantitative PSF/reference diagnostics and original FITS cutouts. The separate extragalactic entry d remains closed historical evidence.
- Investigated the known trans-Neptunian binary 2001 QY297, checking ten returned detections against JPL. The user supplied a completed full-night recovery: rank 1 among 235,039 November 12 alerts in 145 visits, with 0.0940 arcsecond miss and no additional source inside the fixed 60-arcsecond radius.
- Implemented a physical Sun-only orbit fitter using earlier observations, observer motion and light travel time. No target JPL orbital state initializes or constrains the fit. Withheld catalog-position errors are 0.652 arcsecond for QY297, 0.054 arcsecond for CR7, and 0.539 arcsecond for WV203 after three training dates.
- Preserved the failed WV203 two-date fit: a small training residual accompanied a 1,493-arcsecond November 15 miss. The later successful fit does not erase this failure.
- Retained input responses, exact observer-geometry queries, hashes, all optimizer trials, state covariances, plots and reports. Four numerical/information-isolation checks passed both in the preparation workspace and, as documented by the user's screenshot, on Pots.
- Restricted moving-object research to **2001 QY297**, **2014 WV203**, **2013 CR7**, and **2026 ED138**. ED138 awaits usable public astrometry and has not been fitted.

## Interpretation and unfinished objectives

The physical-fit results demonstrate useful retrospective prediction of withheld known-object positions. They do not establish a precision orbit, a blind discovery, a new binary signal or a new mass measurement. QY297's formal uncertainty ellipse assumes independent 0.15-arcsecond coordinate errors and one local branch; the full orbital parameters remain considerably less certain than the near-term predicted sky position.

Next work remains confined to the named list: add planetary perturbations; explore orbit ambiguity and global uncertainty; cross-check with an established fitter; evaluate the new fitted tracks against all-alert lists; acquire usable footprints/masks; obtain ED138 astrometry; and assess whether QY297 image/forced-photometry data can support a binary-specific signal. The existing literature system mass remains an external benchmark.

The user deferred the binary discussion for a later session, particularly how resolved observations established two orbiting components and how the mutual orbit yielded the system mass. Potential thesis work requires new, identifiable information beyond the already published binary orbit/mass.

## Archive and publication scope

All available relevant scientific artifacts in this preparation workspace are included in the final commit. Additional Pots-generated reports, research source files and downloaded archives must be captured on Pots, where the authenticated GitHub CLI and full compact alert archive reside. The finalizer captures the allowlisted astronomy directories, snapshots SQLite consistently, creates split release assets for large/raw data, records checksums, and archives the named astronomy delivery ZIPs when present.

The GitHub repository is public, as confirmed by the user. Preparation is not proof of a completed push. Publication receipts are written only after the authenticated finalizer verifies uploaded assets and remote commits. The current environment has no authenticated GitHub write session; the existing Pots login is a separate session.

## Release-listing compatibility repair

Research commit 9edd7ee was successfully pushed to main and release research-archive-20261120T175302Z was created. The initial asset-listing command failed before uploads. The repair replaces --slurp pagination with explicit page requests and makes captured API errors visible. It resumes the existing capture and release; asset publication remains pending until the finalizer writes its verified receipt.

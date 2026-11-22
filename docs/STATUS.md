# Status · November 21, 2026

[Current review](../reports/2026/11/21/overnight-review.md): scheduled overnight reports completed; fresh public watchlist histories remain unchanged and statistics still end November 15. ED138 public MPC data are now acquired and a new historical prediction benchmark completed. PGC image-fit sensitivity was explored without a flare claim. [Journal](../journal/2026/11/2026-11-21-rubin-journal.md).

## Earlier November 20 status notes

# Status · November 20, 2026

Current moving-object addendum: work is restricted to QY297, WV203, CR7 and ED138. User-supplied Pots results confirm QY297's full-night JPL recovery (rank 1/235,039; 0.094 arcsec). New independent Sun-only fits predict withheld detections within 0.652 arcsec (QY297), 0.054 arcsec (CR7), and 0.539 arcsec (WV203 after three training dates). WV203's two-date fit fails badly and is retained as a control. Physical fitted-track all-alert ranking, planetary perturbations, global orbit uncertainty, usable footprints and ED138 astrometry remain pending. See [new report](../reports/2026/11/20/physical-orbit-watchlist/report.md) and [journal f](../journal/2026/11/2026-11-20f-rubin-journal.md). Earlier paragraphs below retain previous status observations and pending statements superseded by this addendum.

Later moving-object addendum: [2001 QY297 investigation](../reports/2026/11/20/qy297-investigation/report.md) retrieved ten catalog detections and checked them against JPL within 0.140 arcsecond. Simple angular fits failed the existing 60-arcsecond November 12 radius. QY297 is a published binary with an external system-mass benchmark; no new mass was measured. Full-night QY297 recovery remains to run against the Pots database using `bash tools/run-qy297-review.sh`. [Journal e](../journal/2026/11/2026-11-20e-rubin-journal.md) records this work. The paragraphs below retain earlier status observations; later dated reports supersede them.

Seven fresh Fink queries found no added or removed source IDs in four watchlist histories or two named slow-control histories compared with saved November 19 responses. November statistics still ended November 15.

The official repair notice last found earlier on November 20 was dated November 17. It described loss of pumped-coolant cooling capacity on November 15, safe camera shutdown and continued troubleshooting. No restart date was established in that check. This is a dated status observation, not a continuously updated operations feed.

The full compact export on Pots contained 1,043,458 unique valid sources across October 30–31 and November 5–15. Counts matched published statistics for those 13 dates. A July 16–November 15 request does not imply four months of continuous observations.

PGC 766016's latest i-band science flux is 1.477 times its earlier median, while difference flux is 0.981 times it. Template measurements rise alongside science measurements. This discrepancy requires image/reference/calibration review. The other watchlist sources remain in their dated reports.

Independent JPL known-orbit predictions recovered four out of four labeled later detections on November 19, with position errors 0.013–0.086 arcsec. Earlier empirical linear predictions failed; a WV203 quadratic prediction still missed by 122.979 arcsec, outside the preselected 60 arcsec radius. These successes and failures address different prediction methods. A 60 arcsec circle also admitted an unrelated detection in one JPL test.

Physical orbit fitting from our training data, verified usable detector footprints, ED138 astrometry integration, unknown-object linking and conditional size/mass work remain pending.

The repository has all five available journal files, including the original November 15 file containing an appended November 18 entry. It has the available analysis scripts and scientific snapshots, with original source checksums. It does not yet have the full Pots raw archive or a fresh export of installed host services. See `data/manifests/external-data.json`.

GitHub creation and publication of the initial archive were subsequently confirmed by the user's successful Pots terminal log. New changes prepared elsewhere still need installation and push from Pots.

Follow-on November 20 work: a broad discovery-triage scanner is implemented and checked on synthetic data and a 45-source real subset. The full million-alert run remains pending on Pots. See [scan methodology](EXTRAGALACTIC-SCAN.md).

PGC image/reference review retrieved all nine November 11/13/15 FITS cutouts. Both PGC and comparison object 313862200773574662 show increasing reported PSF shape moments alongside increasing science/template flux, with unchanged reported template date summaries. WCS orientation and mask interpretation remain gates for independent photometry. See the [investigation report](../reports/2026/11/20/image-reference/report.md) and the extended November 20b journal.

Session closeout: [journal g](../journal/2026/11/2026-11-20g-rubin-journal.md) records final archive preparation. The physical-orbit entry is journal f; the earlier QY297 entry e is retained separately. PGC quantitative reference diagnostics and follow-up source snapshots are now included in this checkout.

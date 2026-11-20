# Rubin daily journal · November 20, 2026 · fourth entry

## Scope and outcome

This entry closes today's extragalactic session. It covers the completed first archive-wide screening, initial classification checks, PGC 766016 image/reference diagnostics, Fink chart review and a public literature check. It does not claim a new extragalactic discovery or verified nuclear flare. Remaining research is recorded as objectives rather than completed work.

## Full archive screening completed on Pots

The user ran the scanner on Pots and supplied its generated report. It read **1,043,458 indexed alerts** spanning October 30–November 15, scored **32,732 eligible object/filter groups**, and found **10,008 groups representing 8,891 objects** passing the initial heuristic cuts. This is an unclassified screening list. Its size is not a discovery count.

The first pass requires three visits on three UTC nights in the same filter, absolute Galactic latitude at least 20 degrees, maximum group centroid offset of 2 arcseconds, nightly-median difference-flux range at least 1,000 nJy, and fractional range at least 0.20. All eligible and passing groups are retained in CSV; only the displayed/detailed list is capped at 100. Known SSO-associated groups are excluded when present, while missing static-object IDs are accounted for separately. The reported 236,428 missing-ID rows cannot all be classified from the report alone.

The ranking lacks original flux uncertainties, pixel flags, template measurements and host/star associations. Small residual baselines can inflate fractional ranges. Single-night transients and sources outside the declared cuts are not covered. No completeness estimate or calibrated false-discovery rate was obtained.

## Initial classification and quality checks

Four nonrandom sources were checked in fresh Fink histories.

| Object | Finding in retrieved histories |
|---|---|
| 170604728153538580 | First-ranked source; all seven in-window i-band measurements carry isDipole=True; near-zero residual baseline inflates its fractional change |
| 313629129709715483 | VSX RRAB variable-star match returned |
| 170666303791562781 | VSX RRAB match returned; one of eleven in-window i-band measurements carries a dipole flag |
| 170591538211979278 | VSX RRAB match returned |

These checks demonstrate the need for stellar classification and image-quality filtering. They are not a representative sample and cannot estimate contamination across all 8,891 objects. Catalog matches require appropriate positional/association review. No unmatched object was promoted to a confirmed extragalactic discovery.

## PGC 766016: science rise and residual behavior

Between November 11 and 15, science flux increased by approximately **380,412 nJy**, measured template flux increased by **375,796 nJy**, and difference flux changed by **−1,984 nJy**. The latest i-band science measurement is about 48% above its earlier median, while its difference measurement is nearly unchanged relative to its earlier median.

The user supplied Fink science, difference and template charts. The difference chart shows earlier i-band residual brightening between October 30 and November 9, then a roughly steady/slightly fainter November 11–15 sequence. The late template-magnitude rise mirrors the late science-image rise. These charts visualize the same underlying alerts and are not independent confirmation.

The distinction matters: the source has earlier measured residual variation, but the dramatic late science-image increase has no corresponding late residual surge. It should not be reported as a demonstrated new flare.

## Existing-image/reference investigation

All nine requested FITS cutouts were retrieved: science, template and difference products for November 11, 13 and 15. Original FITS bytes, hashes and product metadata were retained. Cutout sizes are 30×30, 53×53 and 62×62 pixels respectively. Display stretches and changing cutout sizes prevent brightness inference from the contact sheet alone.

The actual supplied science PSF kernels have per-axis RMS widths of **2.728, 3.651 and 5.363 pixels**. Template kernels remain near **2.240, 2.219 and 2.280 pixels**. These are kernel moments, not seeing FWHM. Both PGC and comparison object 313862200773574662 also show increasing reported PSF shape moments alongside increasing science/template flux, with unchanged reported template date summaries within each object. Matching summaries do not prove identical reference pixels or weights.

A local-background-subtracted fixed 2-arcsecond aperture on the PGC template cutouts returned approximately **854,858, 855,002 and 854,698 nJy**. The roughly **0.036% span** is a descriptive, unmasked pixel-sum comparison; it is not a precision estimate or certified photometry. It supports investigating the changing catalog template measurement rather than assuming the reference image gained light.

A controlled experiment took one unchanged real template image, broadened it and its PSF with the same Gaussian kernels, and fitted a PSF-plus-constant model within 10 pixels. The fitted amplitude increased from approximately **578,877 to 702,302 nJy (21.3%)** as added Gaussian sigma increased from zero to five pixels. A synthetic point-source control retained its amplitude to numerical precision. This demonstrates model/measurement sensitivity in this experiment. It does not reproduce Rubin processing, establish a unique host-light explanation or explain the complete observed catalog trend.

Diagnostic difference-image fits using their own PSFs returned approximately **100,641, 99,008 and 105,382 nJy**. No independently calibrated nuclear light curve or significance calculation was produced.

The products contain variance, mask and PSF image planes, but the FITS mask-plane bit mapping is absent. Rubin documentation warns that assignments can change. Inspected headers also omit CTYPE1/CTYPE2, and Fink documents orientation issues. Mask-aware photometry, covariance, background/host decomposition, PSF matching, independent calibration and validated WCS handling remain limitations. No arbitrary mask-bit mapping was imposed.

## Previous professional study versus a recent verified flare

A November 20 public search used PGC 766016, AT 2018fcv, ASASSN-18sf, ZTF18acuavde and Rubin ID 171141216913588260. It found prior identification and spectroscopy, but no public notice located confirming a new November 2026 flare or announcing dedicated present follow-up. Unpublished monitoring remains unknown.

ATel 11972, issued August 20, 2018, reports SCAT spectroscopy obtained August 17 and classifies ASASSN-18sf / AT2018fcv as AGN at redshift approximately 0.095. The indexed TNS record lists ASAS-SN and ZTF reports; WISeREP lists AGN at z=0.094. These establish earlier professional attention. Direct TNS/WISeREP object pages returned access errors during this check, so complete current follow-up records were not inspected.

## Decisions and next extragalactic objectives

1. Retain PGC as a follow-up target, but do not describe its 48% scienceFlux increase as a verified flare. Keep earlier difference variation separate from the late science/template discrepancy.
2. Enrich the archive shortlist with original uncertainties and quality flags, then recompute variability after excluding problematic measurements. Separate known stellar variables from possible galaxy/AGN sources; do not infer an extragalactic identity from latitude alone.
3. Correct the ranking's sensitivity to near-zero residual baselines using uncertainty-aware selection with an explicit validation strategy. Preserve the first-pass report as evidence rather than replacing it.
4. Inspect candidate light curves and science/template/difference images after those checks. Resolve masks, WCS and calibration before accepting independent nuclear photometry.
5. Commit the full scan outputs already on Pots, the completed journal and supporting diagnostics. No new timer or installed collector configuration is required by these findings.

The GitHub repository was created and its initial update published successfully on Pots earlier today. This entry and the quantitative extension are finalized for publication through the supplied Git block; the preparation environment has not pushed them. The moving-object discussion is a separate workstream.

## Evidence and sources

- Pots scan output: reports/2026/11/20/archive-scan-20261120T154225Z/ . Only its human-readable report was supplied to the preparation workspace; the full CSV/JSON outputs remain on Pots until archived there.
- Supporting local diagnostic: reports/2026/11/20/psf-reference-diagnostic/ . Original nine-cutout retrieval: reports/2026/11/20/image-reference/ .
- Four follow-up histories: data/snapshots/2026-11-20-extragalactic-followup/ .
- Fink photometry: https://doc.lsst.fink-broker.org/data/photometry/
- Fink image API: https://doc.lsst.fink-broker.org/services/api/imagesearch/
- Fink known issues: https://doc.lsst.fink-broker.org/data/issues/
- Rubin masks: https://dp1.lsst.io/products/images/mask_planes.html
- Historical classification: https://www.astronomerstelegram.org/?read=11972

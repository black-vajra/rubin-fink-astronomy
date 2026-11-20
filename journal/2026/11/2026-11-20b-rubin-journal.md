# Rubin daily journal · November 20, 2026 · second entry

## Research repository prepared

Prepared `rubin-fink-astronomy` for the GitHub account `black-vajra`. The archive separates dated journals and reports, evaluations, scientific snapshots, source code, configuration examples, historical source versions and data provenance. Added a current objectives page, status summary, operational caveats, daily workflow, journal index and source attribution.

Collected 120 existing research source files, approximately 62.3 MB before Git compression, including both monthly Parquet products, public histories, consistent pilot SQLite backups, original reports supplied from Pots, recovery output and available verification logs. Original imported files have SHA-256 checksums. Five pre-existing dated journal files are retained unchanged; this entry is the sixth. The November 15 file includes a historical November 18 append and is explicitly indexed that way rather than silently retitled.

GitHub CLI and the browser were not authenticated in the preparation session. Remote repository creation and push therefore remain pending. A publication helper checks the `black-vajra` account, defaults to a private repository, and pushes without force after authentication. No claim of remote backup is made until publication is verified.

## Remaining data capture

The full 1,043,458-source index and approximately 2.6 GB of raw historical packets remain on Pots. Earlier full-night/live packet directories and exact installed start/stop timer units also require a local capture. These are explicitly listed as missing from this preparation workspace.

Added an allowlisted Pots capture utility. It preserves small reports/scripts, takes consistent SQLite backups, inventories all selected raw data and can package large files into numbered release assets with checksums. A documented verification step follows upload. Git history holds reports, small scientific products and inventories; release assets preserve the larger raw bytes. No credentials, SSH keys, VPN files or arbitrary home backups are intended for this repository.

## Research priorities retained

Continue PGC science/template/image-quality investigation, physical-orbit fitting with withheld observations, verified footprint controls, and ED138 public astrometry integration. Unknown-body linking and conditional size/mass estimates follow validation. The repository setup adds documentation and archival infrastructure; it does not create new scientific detections or change the installed nightly observing schedule.

Going forward, create a new journal file for each day's changes, with `b`, `c` and later suffixes for additional entries on that day. Preserve failed tests and superseded conclusions as dated evidence, and keep current interpretations in the status/objectives pages.

## Publication subsequently confirmed on Pots

The user authenticated GitHub CLI as `black-vajra` and ran the publication helper on Pots. The supplied terminal output confirms creation of `black-vajra/rubin-fink-astronomy`, successful push of `main`, upstream tracking and verification of the remote commit. Existing HTTPS authentication worked; no new SSH key was required. This supersedes the earlier pending-publication state in this entry. The additional work below is prepared as a follow-on local commit for installation and push from Pots.

## Today's extragalactic interpretation

PGC 766016 remains the first image/reference follow-up. Between November 11 and 15 its science flux increased by approximately **380,412 nJy**, while measured template flux increased by **375,796 nJy** and difference flux changed by **−1,984 nJy**. Almost the entire science increase has a corresponding template-measurement increase. This requires measurement/reference/calibration investigation before calling the apparent rise a nuclear flare; it does not yet identify the cause.

The quasar crossmatch shows modest changes in this sparse sample. Object 313862200773574662 has a smaller, related science/difference discrepancy. AT 2019hkw has only one in-window measurement per returned band, preventing a same-band trend test. The daily watchlist report covers four selected sources and is not an archive-wide discovery search.

## Broader discovery scan implemented

Added a read-only, offline first-pass scanner for the full Pots `sources` index. It is not restricted to the four watchlist objects. It excludes known SSO-associated groups, keeps exact source IDs and filters separate, reduces repeated measurements by visit before nightly medians, and screens position-consistent multi-night objects at high Galactic latitude. Every eligible object/filter is scored and written to CSV; only the displayed/detailed review list is capped.

The initial declared cuts require three visits on three UTC nights, |Galactic latitude| ≥20 degrees, maximum centroid offset ≤2 arcseconds, nightly-median difference-flux range ≥1,000 nJy and fractional range ≥0.20. These are screening choices, not a calibrated detection completeness or false-discovery threshold. The index lacks uncertainties, quality flags, template flux and host/star matches. Single-night transients, low-latitude sources and weaker variability are outside this first pass. Catalog and original-packet validation follow the shortlist.

Synthetic verification covered variable/constant objects, a science-only increase, known SSO exclusion, negative difference flux, repeated visits, RA wrapping and large exact IDs. A real 45-source watchlist subset also ran successfully. PGC's i-band historical difference range passed the heuristic cut; this reflects variation over the full sampled interval, not a newly detected flare. **The million-alert run itself is pending execution on Pots. No new archive-wide candidate count or discovery is claimed.**

## Existing-image/reference investigation started and produced new evidence

Retrieved and parsed **all nine requested FITS cutouts** for PGC 766016: science, template and difference images for November 11, 13 and 15. Retained the original FITS bytes, hashes, image-plane/header metadata, uncertainty-plane types and a contact sheet. The returned image dimensions are 30×30, 53×53 and 62×62 pixels respectively. Independent display stretches and changing cutout sizes prevent brightness inference from the contact sheet alone.

Metadata review found an important additional association. The reported PSF trace (`ixxPSF + iyyPSF`) grows alongside science/template flux in both objects:

| Object | November 11 | November 13 | November 15 | November 15 / November 11 |
|---|---:|---:|---:|---:|
| PGC 766016 | 0.249989 | 0.472646 | 1.915500 | 7.662 |
| 313862200773574662 | 0.248430 | 0.395490 | 1.438182 | 5.789 |

These are native returned shape quantities, not a derived seeing FWHM. For each object, the reported template minimum/mean/maximum MJD and version agree across these three epochs. That does not prove identical reference pixels, weights or fitting. The shared pattern strengthens the case for investigating PSF/host-light measurement effects; it does not establish causation or exclude intrinsic variability.

The FITS products contain `UNCERT` planes labeled `VarianceUncertainty`, `MASKPLANE` and `PSFIMAGE`. The inspected headers omit `CTYPE1`/`CTYPE2`; Fink documents a cutout WCS/orientation issue. Resolve WCS handling and mask-bit definitions before quantitative alignment or aperture/PSF-matched comparisons. No independently recalibrated photometry or new flare identification has been produced.

References: https://doc.lsst.fink-broker.org/data/photometry/ ; https://doc.lsst.fink-broker.org/services/api/imagesearch/ ; https://doc.lsst.fink-broker.org/data/issues/ .

## Next steps from this extension

Run the new scanner against the full index on Pots and inspect its accounting and shortlist. Then recover original errors/flags, catalog associations and cutouts for shortlisted sources before making extragalactic claims. Continue PGC with WCS/mask-aware, aperture-consistent or PSF-matched photometry, comparing the science and template response to image quality. Preserve each new scan report and selection parameters in the repository. Existing orbit-fitting and footprint objectives remain unchanged.

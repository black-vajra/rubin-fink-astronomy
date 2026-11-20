# Rubin research journal · November 20, 2026 · f

## Scope and state of the project

The moving-object daily research list is now restricted, at the user's direction, to four named targets:

| Object | Purpose | Current gate |
|---|---|---|
| **2001 QY297 / 275809** | Primary distant binary; orbit prediction and external mass benchmark | Improve dynamics/uncertainty and assess binary-signal feasibility |
| **2014 WV203** | Apparent-slow-motion and orbit-ambiguity control | Retain enough separate training dates; reject misleading short-arc solutions |
| **2013 CR7** | Independent comparison control | Extend held-out tests and compare with an established fitter |
| **2026 ED138** | Priority follow-up target | Obtain usable public astrometry before fitting |

No additional moving-object candidates were searched or fitted in this phase. Broader moving-object discovery is deferred. The extragalactic project retains its separate scope. The user confirmed public GitHub publication of commit `6987baf`, including the closed November 20d extragalactic entry. This f entry records the physical-orbit work following the earlier e entry. The user assigned the f designation before publication.

## QY297 identity and historical coverage

Fresh Fink designation and number queries returned the same ten unique positions on six UTC dates, June 27–November 12. The Fink ssObjectId is `21163611629303641`. Four detections lie in the original July 16–November 15 historical interval; the six June/early-July detections explicitly extend this target-specific investigation. Returned histories are not guaranteed complete.

All ten positions agree with the external JPL known orbit within 0.140 arcsecond; November 12 differs by 0.094 arcsecond. Limited quality checks found pixelFlags=False, centroid_flag=False and isDipole=False. Those checks do not certify all image/astrometric quality.

## Full-night known-orbit recovery: completed on Pots

The user supplied the completed report generated **2026-11-20T16:55:37Z**. It scored **235,039** indexed November 12 alerts across **145** visits against external JPL predictions. QY297 source `171198373954584702`, visit `2026111100115`, ranked **first**, with **0.0940 arcsecond** miss. It was the only detection inside the unchanged **60-arcsecond** radius; no other label or unassociated source fell inside.

This replaces the earlier pending status. The completed report is user-supplied evidence; the full Pots database was not independently opened in this workspace. The result verifies known-orbit matching within that archive, not a coverage-normalized false-match rate or all physical detections. The report generator's stale next-step wording was corrected for future completed local runs.

## Physical orbit fits using earlier observations only

A new offline fitter estimates six Cartesian heliocentric state parameters. It uses solar gravity, Rubin's changing observer position, TDB dynamical times and iterative light travel time, with a small linearized correction for Sun motion during light travel. JPL supplies only the Sun/observer geometry; no target catalog state, elements, distance, mass or ephemeris enters initialization or optimization.

Eight trial distances (2–160 AU) are tested. The lowest training chi-square among converged bound solutions is selected without using held-out positions. The existing 60-arcsecond gate is retained. A uniform **0.15 arcsecond per-coordinate error** is an assumed analysis floor, not an empirically calibrated uncertainty. No observations were removed as outliers.

For the November 12 tests, only positions strictly earlier than that date are fitted. A separate forward-chain WV203 control adds its November 12 measurements to training, then withholds November 15. These are retrospective tests of known objects with future detections already known; they are not prospective blind discoveries.

| Target | Training points / dates | Withheld UTC date | Miss (arcsec) | Inside 60 arcsec? |
|---|---|---|---:|---|
| 2001 QY297 | 9 / 5 | 2026-11-12 | 0.652 | Yes |
| 2014 WV203 | 5 / 2 | 2026-11-12 | 1022.237 | No |
| 2014 WV203 | 5 / 2 | 2026-11-12 | 1022.446 | No |
| 2014 WV203 | 5 / 2 | 2026-11-15 | 1493.072 | No |
| 2013 CR7 | 5 / 3 | 2026-11-12 | 0.054 | Yes |
| 2014 WV203 | 7 / 3 | 2026-11-15 | 0.539 | Yes |

### What succeeded

QY297's nine training positions on five dates predict November 12 within **0.652 arcsecond**. All eight starting-distance trials converge to the same solution. Its maximum training residual is **0.0723 arcsecond**. This is a substantial improvement over the earlier October 30 straight-line prediction's **128.766 arcsecond** miss.

The formal QY297 95% position-ellipse semiaxes are **6.841 × 0.234 arcseconds**, conditional on the assumed errors and selected orbit branch. The 0.652-arcsecond test miss is consistent with this local uncertainty estimate. The orbit's distance/velocity and especially eccentricity remain much less constrained than its near-term sky position; the fit is not a precision replacement for JPL. Local Gaussian state draws and their broad element spreads are retained in the report rather than hidden behind a single best-fit value.

CR7's five training positions on three dates predict November 12 within **0.054 arcsecond**. WV203's seven-position, three-date fit predicts the withheld November 15 point within **0.539 arcsecond**.

### What failed and what it means

WV203's five-position training arc has only two separate dates. Its selected converged solution fits training positions within 0.036 arcsecond yet misses later detections by **1,022–1,493 arcseconds**. Only one initialization converged to a bound solution within the stated budget; other incomplete/failed trials remain recorded. The failure is not erased by the later successful test.

Adding November 12 as a third training date reduces the November 15 miss from **1,493.072** to **0.539 arcsecond**. Date diversity and orbit ambiguity matter more than a tiny training residual. A large formal ellipse around an ambiguous solution does not make it useful.

The new fitted physical tracks have been tested against withheld catalog measurements here. They have **not** yet been ranked against the full Pots all-alert lists. The earlier full-night rank-one result used the external JPL predictor; the two evaluations must remain distinct.

## Binary mass and possible thesis direction

Grundy et al. (2011), Table 8, already measured QY297's resolved mutual orbit: period **138.110 ± 0.023 days**, relative semimajor axis **9,960 ± 31 km**, and total system mass **(4.105 ± 0.038) × 10^18 kg**. This is our external dynamical-mass benchmark. The present fit concerns motion around the Sun and does not determine the mutual orbit, individual masses, size or density, or improve the published system mass. Earlier variability research also exists (Thirouin et al. 2012).

The binary could support a focused PhD research question if the work adds new, defensible information. A candidate direction is testing whether Rubin-era unresolved astrometry/photometry constrains photocenter motion or binary variability, validated against resolved observations and suitable controls. The present ten alert positions establish neither such a signal nor thesis-level novelty.

Before treating that as a thesis proposal, audit the current literature and resolved observations, obtain actual usable cutouts/forced photometry and seeing/SNR information, simulate the expected binary signal against calibration/centroid systematics, and establish parameter identifiability and access to enough data. A degree project would also need appropriate academic supervision. Broader target expansion is not authorized by this proposal.

## Deliverables and validation

- New report, plot, retained input responses/observer queries, input hashes and complete trial/covariance results: `reports/2026/11/20/physical-orbit-watchlist/`.
- Restricted list: `config/moving-object-watchlist.json`. The fitter permits only these named objects and leaves ED138 explicitly unfitted pending data.
- New fitter and optional local runner: `tools/physical_orbit_review.py`, `tools/run-physical-orbit-review.sh`. It downloads no alert archive and requires SciPy, NumPy and Astropy.
- Four numerical/information-isolation tests pass: analytic circular-orbit propagation, energy conservation, nonzero light-time effect, and synthetic training-only recovery with the same fitted state after altering a held-out observation. The last combined check also verifies a withheld synthetic prediction within 0.001 arcsecond.
- The full local-night JPL recovery is completed as reported above. A future all-alert evaluation of the new fitted track remains a separate gate.

## Objectives moving forward, within the restricted list

1. Include planetary perturbations, cross-check with an established orbit fitter and explore alternative orbit branches/global uncertainty.
2. Add genuinely new withheld epochs for QY297 and CR7; keep WV203 as a training-geometry control rather than accepting a two-date solution.
3. Retrieve usable ED138 astrometry with explicit provenance before attempting a fit.
4. Obtain usable detector footprints/masks before matched-coverage false-match or sensitivity claims.
5. Assess the QY297 binary-signal question with image-level and forced-photometry evidence before pursuing component size/mass work.

The Sun-only model omits planetary perturbations, solar reflex acceleration in heliocentric dynamics, relativity, mutual binary motion and correlated/image-level astrometric errors. Formal uncertainty is conditional and local, not a global posterior. No unknown-body search, Planet Nine identification or new mass measurement ran in this phase.

Sources: [Fink SSO API](https://api.lsst.fink-portal.org/api/v1/sso), [JPL Horizons definitions](https://ssd.jpl.nasa.gov/horizons/manual.html), [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html), [Grundy et al. 2011](https://arxiv.org/abs/1103.2751), [Thirouin et al. 2012](https://academic.oup.com/mnras/article/424/4/3156/1062105).

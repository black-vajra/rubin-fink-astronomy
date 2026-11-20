# Rubin research journal · November 20, 2026 · e

## Moving-object investigation: 2001 QY297

The user confirmed that commit `6987baf` published the November 20d extragalactic journal and scan results, and that `black-vajra/rubin-fink-astronomy` is now public. This entry begins the separate moving-object work; it does not alter the closed extragalactic entry.

Fresh Fink SSO queries by both `2001 QY297` and numbered designation `275809` returned the same ten unique source IDs on six UTC dates, June 27–November 12. Fink ssObjectId is `21163611629303641`. Only four returned detections lie in the original July 16–November 15 historical interval. Six earlier measurements explicitly extend this target-specific investigation; they are not silently counted as in-window archive coverage.

JPL SBDB identifies QY297 as a trans-Neptunian object. Solution 23 gives heliocentric semimajor axis 43.7575 AU, perihelion 40.1882 AU, aphelion 47.3268 AU and orbital period about 289.46 years. These elements are not instantaneous distance measurements.

## What the astrometry showed

Using Rubin topocenter X05, astrometric ICRF positions, and TAI-to-UTC conversion, all ten measured positions agreed with JPL Horizons within 0.140 arcsecond. The November 12 point differed by 0.094 arcsecond. No positional offset or time correction was fitted. The ten returned measurements had pixelFlags=False, centroid_flag=False and isDipole=False; these limited checks are not an exhaustive quality certification.

With November 12 excluded from fitting and the existing 60-arcsecond radius unchanged:

| Prediction method | November 12 miss | Inside fixed radius? |
|---|---:|---|
| October 30 linear angular fit, three measurements | 128.766 arcsec | No |
| June 27–October 30 linear angular fit, nine measurements | 408.081 arcsec | No |
| June 27–October 30 quadratic angular fit, nine measurements | 793.969 arcsec | No |
| External JPL known-orbit prediction | 0.094 arcsec | Yes |

The angular fits omit observer parallax and orbital dynamics. More data did not rescue this unsuitable model. This is a retrospective diagnostic for a catalog-known object, not a blind discovery test or a physical orbit fitted independently from Rubin observations.

## A useful external mass benchmark

Grundy et al. (2011), Table 8, report a binary mutual orbital period of 138.110 ± 0.023 days, relative semimajor axis 9,960 ± 31 km, and total system mass **(4.105 ± 0.038) × 10^18 kg**, based on resolved Hubble/Keck observations. This supplies an external dynamical-mass benchmark. It is not a mass measured by our analysis, and it is not the mass of either component separately. Reusing the published mutual-orbit parameters in Kepler's law reproduces approximately 4.104 × 10^18 kg but is not an independent measurement.

Rubin alert brightness alone does not establish mass, component size, density or a resolved mutual orbit. Possible binary photocenter motion should be considered in future astrometric modeling rather than assumed absent or assigned a measured amplitude here.

## Deliverables and remaining gates

- Report, complete returned Fink rows, SBDB response, cached Horizons responses, source-query provenance and machine-readable scores are retained in `reports/2026/11/20/qy297-investigation/`.
- `tools/qy297_review.py` reproduces these checks and optionally scores every indexed November 12 alert against the visit-specific JPL track, using the unchanged 60-arcsecond radius.
- `tools/run-qy297-review.sh` runs that recovery on Pots without downloading another alert archive. The full local-night test has **not** run in this reporting workspace: the 235,039-alert November 12 database is on Pots. A synthetic fixture verified date isolation, exact IDs, near/far distractor accounting and reproduction of the known 0.094-arcsecond residual. That fixture is not a real full-night result.
- Physical orbit fitting from earlier observations, uncertainty propagation and additional withheld nights remain the next independent-prediction gate.
- Usable detector footprints/masks and matched-coverage comparison positions remain required for a coverage-normalized false-match assessment.
- Unknown-body linking, Planet Nine screening and new size/mass estimates have not run. QY297 is a known binary, not a new discovery.

Next discussion: review the Pots all-alert recovery, including competing matches, then develop a physical orbit benchmark using only training observations. Keep the earlier ED138 and broader slow-control objectives; QY297 complements them.

Sources: [Fink SSO API](https://api.lsst.fink-portal.org/api/v1/sso), [JPL SBDB](https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=275809&full-prec=true), [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/), [Grundy et al. 2011](https://arxiv.org/abs/1103.2751), DOI [10.1016/j.icarus.2011.03.012](https://doi.org/10.1016/j.icarus.2011.03.012).

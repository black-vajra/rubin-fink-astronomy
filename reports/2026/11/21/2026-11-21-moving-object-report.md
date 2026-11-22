# Moving-object review · 2026-11-21

Generated 2026-11-22T01:27:20+00:00.

Active scope remains **2001 QY297, 2014 WV203, 2013 CR7 and 2026 ED138**. The three successful Fink histories are unchanged; ED138’s Fink query failed with HTTP 400. The public MPC route succeeded.

## ED138 public-astrometry gate completed

Retrieved MPEC 2026-U85 and parsed **74 public observations**: **30 Rubin/X05** positions on **20 dates**, March 4–July 11, 2026; and **44 DECam/W84** positions on **14 dates**, February 25, 2016–April 7, 2023. The latter are retained but not included in this initial fit.

Before numerical scoring, the training cutoff was fixed at **June 13, 2026 UTC**. We fitted 25 Rubin positions on 17 earlier dates and withheld five later positions. No target catalog orbit, orbital elements printed in the circular, or restricted Rubin image/catalog release entered the fit.

| Withheld UTC | Miss (arcsec) | Inside fixed 60 arcsec? |
|---|---:|---|
| 2026-06-27T05:23:48.336+00:00 | 0.027 | True |
| 2026-07-09T04:04:54.307+00:00 | 0.043 | True |
| 2026-07-09T04:49:07.046+00:00 | 0.038 | True |
| 2026-07-11T06:43:24.182+00:00 | 0.039 | True |
| 2026-07-11T07:21:14.515+00:00 | 0.075 | True |

This is a retrospective known-object benchmark with a Sun-only physical model, observer motion and light travel time. It is not an independent discovery, a globally unique precision orbit, or a size/mass result. Formal errors remain conditional on the assumed 0.15 arcsec coordinate floor and selected branch.

See [ED138 raw data, geometry, trials and benchmark](ed138-public-astrometry/report.html). Native MPC line numbers/station codes are retained; no Fink source IDs or visit IDs were fabricated.

## QY297 and comparison controls

The prior QY297, CR7 and WV203 fits remain their November 20 results, not freshly recomputed orbital solutions. Next numerical gate remains planetary perturbations, global orbit ambiguity/uncertainty and an established-fitter cross-check. The fitted-track full-night ranking remains separate from the already verified external-JPL recovery.

## Methodology follow-up

The discovery announcement prompted a targeted review of linking and precovery methods. See [methods and source-access notes](methods-and-data-sources.html). Our next archive searches should remain confined to the named watchlist, preserving candidate provenance and image-level validation. No authenticated ADAM search was submitted and no broad new-object search ran.

The public astrometry and restricted image/catalog release are distinct products. ED138 is now an active public-astrometry benchmark; its proprietary RSP images were not accessed.

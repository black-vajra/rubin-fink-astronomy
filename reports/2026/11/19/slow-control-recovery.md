# Slow-control recovery
Generated 2026-11-19T16:14:13+00:00
Radius fixed before scoring: 60 arcsec.

## 2014 WV203
2026-10-30: 4 detections over 37.92 min | east +0.00144, north +0.00404 arcsec/min | speed 0.00429 arcsec/min.
2026-11-12: 2 detections over 2.05 min | east +0.22933, north +0.10910 arcsec/min | speed 0.25396 arcsec/min.
  Short baseline: rate is sensitive to positional errors.
2026-11-15: 1 detection; nightly rate unavailable.
Requesting JPL topocentric predictions for 145 visits on 2026-11-12...
2026-11-12, JPL known-orbit recovery: 235,039 test alerts | 3 inside 60 arcsec.
  Control 171198378851958839 | visit 2026111100151 | rank 1 | miss 0.060 arcsec | inside radius True
  Control 171198378362798086 | visit 2026111100148 | rank 2 | miss 0.086 arcsec | inside radius True
  Recovered labeled detections inside radius: 2.
  Coverage-normalized false-match rate remains unavailable without detector footprints.
2026-11-15, Oct 30 + Nov 12 linear empirical fit: 138,867 test alerts | 0 inside 60 arcsec.
  Control 171211556189634583 | visit 2026111400026 | rank 28 | miss 610.045 arcsec | inside radius False
  Recovered labeled detections inside radius: 0.
  Coverage-normalized false-match rate remains unavailable without detector footprints.
2026-11-15, Oct 30 + Nov 12 quadratic empirical fit: 138,867 test alerts | 0 inside 60 arcsec.
  Control 171211556189634583 | visit 2026111400026 | rank 3 | miss 122.979 arcsec | inside radius False
  Recovered labeled detections inside radius: 0.
  Coverage-normalized false-match rate remains unavailable without detector footprints.
Requesting JPL topocentric predictions for 60 visits on 2026-11-15...
2026-11-15, JPL known-orbit recovery: 138,867 test alerts | 1 inside 60 arcsec.
  Control 171211556189634583 | visit 2026111400026 | rank 1 | miss 0.034 arcsec | inside radius True
  Recovered labeled detections inside radius: 1.
  Coverage-normalized false-match rate remains unavailable without detector footprints.

## 2013 CR7
2026-10-30: 3 detections over 67.50 min | east +0.00120, north -0.00822 arcsec/min | speed 0.00831 arcsec/min.
2026-11-12: 1 detection; nightly rate unavailable.
Requesting JPL topocentric predictions for 145 visits on 2026-11-12...
2026-11-12, JPL known-orbit recovery: 235,039 test alerts | 1 inside 60 arcsec.
  Control 171198373978701903 | visit 2026111100115 | rank 1 | miss 0.013 arcsec | inside radius True
  Recovered labeled detections inside radius: 1.
  Coverage-normalized false-match rate remains unavailable without detector footprints.

Quadratic fits are empirical extrapolations. JPL predictions use an external known orbit.
These checks assess matching and prediction models. Unknown-object orbit linking remains pending.
Source https://ssd-api.jpl.nasa.gov/doc/horizons.html

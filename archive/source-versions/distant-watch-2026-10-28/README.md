# Rubin Distant Watch 0.1 — experimental public-data pilot

A dedicated search for distant-body-compatible motion linkages in small samples
of public Rubin/Fink detections. This differs from the earlier brightness monitor:
it links across broker object IDs and tests Earth-parallax-corrected motion models.

This program does not discover a planet merely by running. It proposes evidence
for follow-up. The public API, limited fields, and incomplete alert representation
prevent an exhaustive unknown-object search. A null result excludes no planet.

## Run on Pots, as pepper

Requires Python 3, NumPy, Astropy, and Matplotlib. Uses the virtual environment
already prepared for Rubin Public Watch. No Fink registration or SciPy required.

Download `rubin-distant-watch.zip` into `~/Downloads`, then:

```bash
python3 -m zipfile -e ~/Downloads/rubin-distant-watch.zip ~/rubin-distant-watch
bash ~/rubin-distant-watch/rubin-distant-watch.sh --once --report
```

If the shared environment has not yet been created on Pots:

```bash
mkdir -p ~/rubin-watch
python3 -m venv ~/rubin-watch/venv
~/rubin-watch/venv/bin/python -m pip install numpy astropy matplotlib
```

Run continuously (30 minutes between completed cycles):

```bash
bash ~/rubin-distant-watch/rubin-distant-watch.sh
```

Ctrl+C stops cleanly. Keep the terminal/session running. Collection and evidence
persist across restarts in `~/rubin-distant-watch/rubin-distant.sqlite3`.
This is a separate database from the brightness monitor. `rw_core.py` is included;
it supplies proven raw-record versioning, exact integer IDs, quality parsing,
time conversion, HTTP limits, and deduplication. Both monitors can run alongside
each other. The package contains NO database to overwrite your measurements.

Reports are generated on the first cycle, then at least 24 hours after the last
report, at the end of the next completed cycle. The schedule survives restarts.
Closing the terminal or stopping the machine stops this local program. Downtime
is recorded; missed data are not guaranteed to be recovered.

Immediate report after a collection:

```bash
bash ~/rubin-distant-watch/rubin-distant-watch.sh --once --report
```

Analyze already stored data and make a report with NO network queries:

```bash
bash ~/rubin-distant-watch/rubin-distant-watch.sh --report-only
```

Open `~/rubin-distant-watch/reports/latest.html` in your browser and follow the
link to the newest report. Each dated folder contains a self-contained HTML
report with plots for up to six proposals, full `report.json`, and a CSV of
measured positions for proposed tracks. All proposals are in the JSON/CSV even
when plots are limited. No observation is submitted to the MPC automatically.

## Where it searches — IMPORTANT

Without a custom field file, a one-time public tag query supplies coordinates of
actual observed alerts. The program creates three ten-arcminute-radius pilot
fields around spatially separated locations, saves them as `fields.auto.json`,
and searches them through Fink's general cone API. These are software-pilot
fields around hostless-alert locations, NOT a scientifically selected Planet
Nine sky region, an unbiased survey, or a sky probability map. The tag is used
only to choose initial sky patches; the subsequent general cones contain other
types of objects too.

For a deliberate target region, create a JSON list with label, RA/Dec in ICRS
decimal degrees, and radius_arcsec. Use the included example only as a known
observed patch, not as a prediction of a planet:

```bash
bash ~/rubin-distant-watch/rubin-distant-watch.sh \
  --fields ~/rubin-distant-watch/example-fields.json --once --report
```

The custom file becomes the active field set. Editing a field's coordinates resets
that field's collection rotation. All raw detections remain archived. Omitting
--fields later keeps the saved field set. Up to 20 fields; radius 30–1800 arcsec;
declination -80 to +30 degrees in this pilot.

The default collects two fields and at most six object histories per cycle.
Each cone requests n=100 objects. The live API can return MORE than requested,
so this is not a trusted server-side row cap. All returned records within the
20 MB response limit are archived; row counts at/above the request are flagged
as coverage-unverified. Per Fink's documentation, the latest alert per indexed object is returned by a
cone. The program queues each object's `/sources` history separately, with a
24-hour retry/refresh cooldown and round-robin rotation. It does NOT assume
the cone response contains every detection or that pagination is available.
Objects absent from the index and truly unassociated packets may be missing.

Raw versions and retrieval URLs are saved; exact detection IDs prevent duplicate
storage. Different endpoint payloads or revisions may add versions of an existing
detection. Known measurements can be downloaded again to detect changes.
Requests are separated by at least two seconds, responses capped at 20 MB,
and errors recorded. No massive public-API scraping is attempted.

## What the linker actually tests

1. Keep positive difference-image detections at S/N>=5 with explicit core
   quality flags and acceptable astrometric errors. Reject observed bad flags,
   withdrawn data, negative template ghosts, and populated known ssObjectId.
   Missing quality is archived but excluded. A missing ssObjectId alone never
   means unknown or new.
2. For each field/filter, collect its latest 90 *observed* days, even if those
   observations are months old. Include histories within a 0.5-degree buffer
   of the discovery cone. The report labels observation ages. It never invents
   a fresh time stamp for an old observation.
3. Test heliocentric-radius assumptions of 50, 80, 120, 200, 300, 400, 600, 900,
   1500, and 2500 AU. For each detection, compute the Earth–Sun vector using
   Astropy's built-in ephemerides and intersect the observed direction with a
   Sun-centered sphere at the trial radius. Project those deparallaxed positions
   into a local tangent plane. A trial radius is NOT an estimated distance.
4. Generate seed pairs separated by 1–30 days; extend along a linear trajectory
   in deparallaxed coordinates, across DIFFERENT broker object IDs if appropriate.
   Refit and retain at most one detection per visit. Each linkage uses one filter.
5. Require at least SIX independent visits across FOUR night bins spanning
   7–90 days, with 0.8-arcsec linkage tolerance by default. A night bin runs from
   UTC noon to the following UTC noon; it is a convenient approximation for Chile.
6. Fit weighted linear angular motion, with a 0.20-arcsecond systematic error
   floor. Require reduced chi-square <=4 and angular speed below 1.2 times the
   local solar escape-speed angular scale, sqrt(2)*k/R^(3/2). This is a rejection
   prior; it does not establish a bound orbit. Radial motion and acceleration
   are not fitted. Topocentric offsets, light-time dynamics, and RA–Dec covariance
   are not included.
7. Compare to a fixed-sky explanation; require >=1 arcsec measured sky extent
   and heuristic chi-square improvement >=30. Leave each night out in turn and
   check whether the fit predicts its selected detections within 1.2 arcsec.
   These are INTERNAL consistency tests on selected data, not independent
   confirmation or calibrated false-alarm probabilities.
8. Merge heavily overlapping linkages and trial-radius duplicates. Prioritize
   proposals compatible with at least one >=200 AU trial. Keep the tested
   compatible radius list explicit; aliases and grid degeneracies are expected.

Per field/filter, at most 1000 eligible points and 1500 seed pairs per trial
radius are used by default. These bounds keep this feasible on Pots/EliteBook;
when reached, the report flags the incomplete analysis. Changing limits changes
the selection and can change the proposed tracks. No sensitivity/completeness
claim is made. This version does not perform shift-and-stack on images and
cannot detect bodies whose individual detections are below the alert threshold.

## The large-planet specialization

Deep-radius-compatible trajectories are considered first. For proposals with
at least three positive r-band science-flux measurements at S/N>=5 and
explicit good forced-photometry flags, the report also calculates a
CONDITIONAL reflected-light diameter range at each compatible
trial radius:

```
D = 2 AU * r * delta * sqrt(10**(-0.4*(m_r - m_Sun_r)) / p_r)
```

Distances r and delta are in AU, D is converted to km; p_r is geometric albedo.
The solar proxy m_Sun_r=-26.93 AB is for SDSS-r (Willmer 2018). Rubin-r color
terms are omitted. Assumes zero phase and all science-image flux from one
unblended body, with albedo 0.04–0.60. Source crowding can make this assumption
wrong. Only science-image flux is used for this step; difference flux is never
substituted for total brightness. Non-r proposals have no size scenario.

A flag notes when an >=200 AU trial could allow an Earth-sized diameter under
these assumptions. That is a follow-up prioritization, not an inferred mass,
physical size, probability of a planet, or Planet Nine identification. A star
mis-association can also create such a scenario. Orbital/parallax solutions,
image evidence, and independent observations are needed to establish distance
and identity. Brightness and motion alone cannot establish planetary mass.

## Known-object checks

For up to two highest-priority proposals per cycle, query SkyBoT at the FIRST,
MIDDLE, and LAST actual observation times, converted from MJD TAI to UTC, using
Rubin observatory code X05 and 10-arcsecond cones. Queries/results and raw XML
are cached for seven days. Errors remain UNCHECKED. A nearby catalog object is
flagged as a proximity requiring review, not automatically assigned as identity.
A no-match result means only that these specific catalog queries returned no
object; it NEVER proves novelty. Increasing --skybot increases bounded checks.

Broker-provided Gaia, SIMBAD, and TNS metadata are retained. Image cutouts are
not independently inspected; the report links all participating Fink objects
for human review of science/template/difference cutouts and associations.

## Evidence, reports, and validation

Separate SQLite tables retain raw detections/versions, field memberships, query
coverage, errors, linkage evidence snapshots, and SkyBoT results. Unchanged
evidence does not generate duplicate audit entries. A previous proposal not
reproduced by the current bounded search is retained as `not_reproduced`; this
is not a scientific disproof, particularly when a budget is reached or the
90-day observed window changes.

The included tests use synthetic distant bodies with actual Earth ephemerides
and DIFFERENT object IDs, plus stationary, nearby/fast, one-night, duplicate-
exposure, quality, catalog-error, geometry, persistence, report, and size-scenario
controls. They test software behavior, not real-survey completeness or discovery
efficiency. Synthetic observations exist only in temporary test databases.

```bash
~/rubin-watch/venv/bin/python ~/rubin-distant-watch/test_distant_watch.py
bash ~/rubin-distant-watch/rubin-distant-watch.sh --help
```

## Primary sources

- Fink cone API and latest-alert/history distinction:
  https://doc.lsst.fink-broker.org/services/api/conesearch/
- Endpoint parameters: https://api.lsst.fink-portal.org/swagger.json
- Photometry: https://doc.lsst.fink-broker.org/data/photometry/
- Quality and missing/incorrect associations:
  https://doc.lsst.fink-broker.org/data/quality/
  https://doc.lsst.fink-broker.org/data/issues/
- Larger registered datasets: https://doc.lsst.fink-broker.org/services/data_transfer/
- SkyBoT epoch/location/query rules:
  https://ssp.imcce.fr/webservices/skybot/api/conesearch/
- Solar photometry proxy: Willmer (2018), https://mips.as.arizona.edu/~cnaw/sun
- Published Planet Nine survey methodology and limits:
  Brown, Holman & Batygin (2024), https://arxiv.org/abs/2401.17977

Independent experimental software; not endorsed by Rubin, Fink, MPC, or IMCCE.

# Rubin daily journal · November 18, 2026 · second entry

## Pots scheduling and report automation

The Kubuntu user timers on Pots show the collector starting at **5:00 p.m. Eastern** and stopping at **9:00 a.m. Eastern**. The existing bright-alert report is also due at **9:00 a.m.** The collector was inactive during the daytime window and user lingering was enabled. This verifies the installed schedule and the daytime state. The next timed transitions still need to be observed. The first research report was generated manually on Pots at **11:18:51 a.m. EST**. The research timer is configured in the installer for **9:10 a.m. Eastern**. The first unattended run is still pending. Both reports depend on the Z890 being booted into Kubuntu and online.

The research report fetches PGC 766016’s Fink history and recent published-night counts, inventories saved Avro batches, and reruns the known-object tests. The Nov 13, 14, and 15 batches passed record-count and UTC-span checks with **76,350**, **59,725**, and **138,867** records respectively and zero file errors. Fink showed no published statistics entry for Nov 16–18 at the time of this run. Data Transfer job submission is still manual.

## Science results from the first report

**PGC 766016.** Fink returned six i-band alert measurements. The November 15 science-image flux was **1,168,054 ± 4,200 nJy (AB 16.231)**, about **48%** above the median of the five earlier i-band points. The difference-image flux was **99,608 ± 3,841 nJy**, about **2% below** its own earlier median. The returned pixel, saturation, bad-pixel, and dipole flags were clear on all six points. The science-image rise merits follow-up, while the difference images show no corresponding increase across those measurements. Compare the November 13 and 15 cutouts and check the next i-band point. [Fink object history](https://lsst.fink-portal.org/171141216913588260)

**Full-night asteroid recovery.** The primary control ranked **1st of 138,867** November 15 alerts across all visits. Its error improved from **115.11″** with November 13 training alone to **36.21″** with November 13–14 training. For the secondary control, the two true November 14 detections ranked **1st and 2nd of 59,725**, at **49.04″** and **49.21″**. The fits used earlier known-object detections. Test-night catalog IDs were checked after ranking. The original shifted predictions found zero unrelated alerts within their diagnostic radii, but those radii were derived from the observed misses, and some shifted positions may have lacked coverage. Those zeros do not establish a false-match rate.

## Stricter benchmark implemented

- **Configurable slow movers.** Each control specifies its catalog ID, separate training and later test transfers, and a maximum apparent rate in arcseconds per minute. The rate check uses the training detections alone.
- **Fixed search radii.** Each control declares its radius and east/north comparison offsets before scoring. Recovery and comparison searches use the same radius. The report shows ranks inside the radius and the observed residuals.
- **Same-visit usable coverage.** The predicted search circle and each comparison circle must fit inside a supplied usable detector polygon and clear any supplied mask polygons. Comparison circles must also clear the prediction circle and one another. Visits with missing geometry and visits outside usable coverage are counted separately. The report gives the number of comparison circles actually tested.

Synthetic verification covered successful recovery, an unrelated comparison alert, a missing visit footprint, detector-edge exclusion, mask exclusion, and a polygon crossing RA 0°. The updated file is ready to install on Pots. Real slow controls and calibrated visit geometry have yet to be supplied. Until they are, the new section explicitly reports that no strict benchmark ran. The original full-night benchmark remains available as a baseline. Mass estimation and Planet Nine screening remain deferred.

### Inputs for the next run

The optional file is `~/rubin-live/research/strict-benchmark.json`. Its top-level fields are `footprints_source`, `controls`, and `footprints`. Each control uses `label`, `ss_object_id`, `training_topics`, `test_topic`, `radius_arcsec`, `max_rate_arcsec_min`, and `comparison_offsets_arcsec`. The `footprints` map uses visit IDs as strings. Each visit supplies `usable_polygons` and optionally `mask_polygons`. Polygons are ordered convex arrays of ICRS RA/Dec pairs in degrees. Geometry should come from calibrated images or independently verified detector coverage. Alert positions themselves do not define usable coverage. The routine scores visits represented in the test Avro batch and uses the median alert timestamp for each visit.

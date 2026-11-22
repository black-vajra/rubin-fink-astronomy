# Overnight review · 2026-11-21

Generated 2026-11-22T01:27:20+00:00. Reporting date is America/New_York.

## Delivery and automation

Both scheduled reports completed successfully on Pots: bright-object report at **09:00 EST** (60 detections, zero file errors), morning research at **09:10 EST**.
The collector ran from **19:26:23 EST November 20** until **09:00:01 EST November 21**. Its late start reduced the intended window by 2 h 26 min; that is consistent with the stated dual-boot practice. The reported 626.4-minute gap includes the planned daytime stop.
Kafka session/heartbeat/fetch timeouts occurred around 07:21 and 07:32. These are communication interruptions, distinct from the camera status. The collector remained running until its scheduled stop. The user-supplied inbox check found **zero new Avro files** in the assessed window; the newest files remain dated November 15. Missed-message counts are not established.

Eight small Fink queries succeeded: monthly statistics, four extragalactic histories and three moving-object histories. The ED138 Fink query returned HTTP 400. All seven successful object histories have unchanged source-ID membership and unchanged returned records versus their saved November 20 baselines. None has a returned non-withdrawn observation in the assessed November 20 17:00–November 21 09:00 EST window.

**Freshly generated reports do not mean freshly observed sky data.** The latest returned Fink published-night key is **20261115**. Missing statistics entries are not independently asserted to mean zero telescope visits.

Rubin’s homepage as retrieved for this review still displays a temporary off-sky notice; the latest formal cooling-issue notice found is dated November 17. No newer restart date was established.

## Work advanced with existing observations

| Track | Work completed | Result |
|---|---|---|
| Extragalactic | Refreshed four histories; twelve image-fit choices per PGC cutout | No changed history; residual-image amplitudes depend on measurement choice; no confirmed flare |
| Moving objects | Retrieved public ED138 astrometry; fitted earlier Rubin positions and withheld later ones | 74 public records retained; five withheld errors 0.027–0.075 arcsec |
| Methodology | Reviewed discovery/precovery sources | Targeted archival workflow identified; no ADAM login/search or new-object scan |

## Reports

- [Extragalactic review](2026-11-21-extragalactic-report.html)
- [Moving-object review](2026-11-21-moving-object-report.html)
- [Freshness data and query accounting](freshness-review/report.html)
- [PGC fit-choice diagnostic](pgc-fit-sensitivity/report.html)
- [ED138 public-astrometry benchmark](ed138-public-astrometry/report.html)
- [Methods and data-source follow-up](methods-and-data-sources.html)

Official sources: https://rubinobservatory.org/ ; https://www.rubin.community/t/rubin-status-november-17-2026/12959 . Fresh Fink response provenance and user-supplied host evidence are retained in this directory.

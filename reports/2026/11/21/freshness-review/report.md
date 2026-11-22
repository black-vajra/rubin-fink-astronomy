# Overnight data review · 2026-11-21

Generated 2026-11-22T00:55:22.893054+00:00.

Collection window assessed: 2026-11-20T22:00:00+00:00 through 2026-11-21T14:00:00+00:00 (17:00–09:00 America/New_York).

Fresh API retrieval time and observation time are reported separately. Returned histories are sparse; absence of a row does not establish non-observation. No local host collection success is inferred from these queries.

| Target | Unique returned source IDs | Latest observation UTC | Added / removed / revised IDs | In assessed overnight window |
|---|---:|---|---|---:|
| PGC 766016 | 8 | 2026-11-15T05:31:12.579 | 0 / 0 / 0 | 0 |
| Quasar crossmatch | 9 | 2026-11-15T05:30:32.245 | 0 / 0 / 0 | 0 |
| Science-image high | 426 | 2026-11-15T05:33:18.561 | 0 / 0 / 0 | 0 |
| AT 2019hkw | 5 | 2026-11-15T00:35:36.762 | 0 / 0 / 0 | 0 |
| 2001 QY297 | 10 | 2026-11-12T01:21:40.083 | 0 / 0 / 0 | 0 |
| 2014 WV203 | 8 | 2026-11-15T00:21:48.506 | 0 / 0 / 0 | 0 |
| 2013 CR7 | 6 | 2026-11-12T01:21:40.083 | 0 / 0 / 0 | 0 |
| 2026 ED138 | query failed | unknown | unknown | unknown |

## Broker statistics

Latest returned published-night key: **20261115**.

| Published-night key | Alerts | Visits |
|---|---:|---:|
| 20261108 | 34119 | 39 |
| 20261109 | 18005 | 21 |
| 20261110 | 39735 | 41 |
| 20261111 | 69458 | 70 |
| 20261112 | 235039 | 145 |
| 20261113 | 76350 | 67 |
| 20261114 | 59725 | 46 |
| 20261115 | 138867 | 60 |

## Local overnight evidence

User-supplied Pots logs confirm reports completed at 09:00 and 09:10 EST. Collector start 19:26:23; scheduled stop 09:00:01; Kafka timeouts around 07:21 and 07:32. The inbox check found **0 new Avro files** in the assessed window; newest files remain dated November 15. See the retained pots-overnight-evidence.json for the supplied file timestamps.

Counts in the freshness table cover all returned history epochs; the science report tables apply the July 16 onward interval. This explains differences between history totals and the science-table counts.

Raw responses, request parameters, retrieval timestamps, response hashes and source-ID changes are retained. The ED138 Fink query returned HTTP 400; it was not a successful empty result. Public MPC astrometry was retrieved separately and used for the historical benchmark.

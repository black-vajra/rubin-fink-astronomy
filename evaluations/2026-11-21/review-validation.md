# November 21 review validation

- Four new native-MPC/source-ID tests passed: 74 records with station/date/cutoff counts, independent sexagesimal conversion, ignored non-observation orbital text, and exact large IDs/revision detection.
- The existing four physical-model tests passed: analytic circular orbit, energy conservation, light travel time and synthetic training/holdout isolation.
- All eight successful fresh API response hashes match retained files. Source-ID membership and per-ID payload sets are unchanged for all seven successful histories. ED138 HTTP 400 is recorded as failure, never as a successful empty result.
- The MPC circular hash matches the test plan. ED138 has 25 training positions and five disjoint held-out positions, all with errors below 0.08 arcsecond. Exact predictions and every initialization are retained.
- The new PGC diagnostic ran 108 fits over nine retained cutouts. Its masks are inventoried rather than interpreted; results are labeled diagnostic, with no calibrated significance claim.
- User-supplied local evidence confirms zero new Avro files in the assessed overnight window and successful 09:00/09:10 reports. This host evidence was not independently executed from the preparation workspace.
- New Python sources compile. Original preserved-source checks remain intact. Runtime versions and code hashes are retained with the dated reports.

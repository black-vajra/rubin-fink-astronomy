# Implementations and installed operations

| Directory | Provenance and caveat |
|---|---|
| `src/public-watch` | Earlier public-API watcher; shipped examples may contain limited coverage |
| `src/distant-watch` | Later live/Avro distant-body candidate linker; not an orbit solver |
| `src/bright-watch` | Original bright-alert package and original systemd units; some text still says Pavilion |
| `src/morning-research` | Updated report script with optional strict-benchmark configuration; real footprint inputs still needed |
| `src/historical` | Original historical importer and JPL control-recovery implementation |
| `archive/source-versions` | Earlier distant-watch source retained as historical evidence |
| `archive/report-generators/2026-11-20` | Workspace reporting copies; never installed into Pots nightly jobs in this session |

The original historical importer resolves data next to its script, while JPL recovery assumes `~/rubin-historical-2026`. The morning report assumes `~/rubin-live`. Preserve those deployment directories or deliberately adapt/test configuration before running. This repository reorganizes and archives sources; it is not an implicit installation or automatic path migration.

Recorded Pots/Kubuntu schedule: collector window 17:00–09:00 America/New_York; bright report at 09:00; research report at 09:10. This follows Eastern daylight-saving changes. It is not fixed UTC-5 year-round. Kubuntu must be running, awake and online. Seasonal observing windows and delayed broker delivery still need review.

The installed collector-window start/stop services and current timer definitions were not available in this preparation workspace. Original packaged units must not be described as their exact installed replacements. Capture current units on Pots with `tools/capture-pots.py` before claiming a deployment snapshot is complete.

Do not publish Fink credentials, WireGuard configs, SSH keys or home-directory backups. Public topic names, scientific packet data and non-secret service definitions are sufficient for this archive.

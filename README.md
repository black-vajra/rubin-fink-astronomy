# Rubin–Fink Astronomy Research

Research archive for extragalactic variability and moving-object recovery using public Rubin/Fink products. Intended GitHub home: `black-vajra/rubin-fink-astronomy`.

Start with [current objectives](docs/OBJECTIVES.md), [current status and limitations](docs/STATUS.md), [daily workflow](docs/DAILY-WORKFLOW.md), and the [journal index](journal/README.md).

## Research streams

| Stream | Work demonstrated | Next gate |
|---|---|---|
| Extragalactic | Same-band science/difference comparisons for four watchlist objects; PGC template-flux review | Review images, references, seeing and calibration before claiming a flare |
| Moving objects | Four labeled held-out detections recovered with independent JPL predictions | Fit physical orbits from training observations, validate holdouts and usable-footprint controls |

No unknown-body discovery, Planet Nine identification or mass measurement has been established.

## Contents

| Directory | Purpose |
|---|---|
| `journal/2026/11/` | Original dated journal entries, including same-day suffixes |
| `reports/2026/11/` | Dated reports, including source reports supplied from Pots |
| `evaluations/` | Retained implementation verification logs |
| `src/` | Collected analysis/collector implementations; installation details vary |
| `data/snapshots/` | Public responses, monthly Parquet products and consistent pilot SQLite backups |
| `data/manifests/` | Checksums, origins and explicit external-data inventory |
| `archive/` | Earlier code versions, generator copies, pilot reports and historical plans |
| `config/examples/` | Non-secret examples |
| `tools/` | Repository validation, local host capture and GitHub publication |

## Latest reports

- [November 20 extragalactic report](reports/2026/11/20/2026-11-20-extragalactic-report.md)
- [November 20 moving-object report](reports/2026/11/20/2026-11-20-moving-object-report.md)
- [November 19 all-alert control recovery](reports/2026/11/19/slow-control-recovery.md)
- [November 20 journal](journal/2026/11/2026-11-20-rubin-journal.md)
- [November 20 image/reference investigation](reports/2026/11/20/image-reference/report.md)
- [Broader extragalactic scan methodology and run instructions](docs/EXTRAGALACTIC-SCAN.md)

On Pots, `bash tools/run-extragalactic-scan.sh` generates a dated first-pass review list from the full local index. It downloads no data and does not push automatically.

The November 20 refresh made seven successful small Fink queries. The million-alert database on Pots was not present in that reporting workspace. See [external data](data/manifests/external-data.json). An initial commit is an archive of the available work, not proof that every file on Pots has been uploaded.

## Local use

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
python3 tools/verify_archive.py
```

Original scripts are preserved with their original path assumptions. Consult [source and operations notes](docs/OPERATIONS.md) before running them. Merely cloning this repository does not install services or download alerts.

For GitHub publication, run `bash tools/publish-github.sh` from this checkout after authenticating `gh` as `black-vajra`. It creates a private repository if absent and pushes `main` without force. [Publication and large datasets](docs/ARCHIVING.md) explains how to capture the remaining Pots files and upload large raw data as release assets with committed checksums.

Public scientific data retain their upstream terms and attribution. No blanket redistribution license is asserted for third-party data or earlier code of unverified licensing. See [sources](docs/SOURCES.md).

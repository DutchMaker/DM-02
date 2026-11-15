# Git and evidence checkpoints

The project sources, verification harness, candidate schematics and authored
study scripts are committed to `DutchMaker/DM-02`. Study scripts retain their
original paths under `Verification/build/` so archived relative paths work.
The working BOM workbook is also tracked there.

Large generated evidence is backed up as GitHub release assets. The
[`checkpoint-2026-11-15` release](https://github.com/DutchMaker/DM-02/releases/tag/checkpoint-2026-11-15) contains two compressed archives:

- `completed-runs.tar.gz`: the six preserved experiment/run directories,
  including the complete run finished at 14:45 UTC on 15 November 2026.
- `studies-and-workbook.tar.gz`: standalone board/model studies, programming
  bundles, BOM/inventory workbook, staging checkpoints and their evidence.

`checkpoint-manifest.json` records every archived file's SHA-256, size and
original repository path, plus each archive's SHA-256 and the Git source
commit. Restore with `tar -xzf` from the repository root; archives use paths
under `Verification/build/`. To inspect without extracting, use `tar -tzf`.

All 14,926 files were verified locally and after downloading from GitHub.
The [backup receipt](checkpoint-2026-11-15.json) records the asset hashes and
the published release identity.

The completed normal run had 22 passing checks, 16 limited checks, six blocked
checks and the documented baseline timing failure, with no harness errors.
All 134 tests passed. The analogue integration subsequently passed all 155
tests in staging and was promoted. Its new full-system run was still in
progress when this Git checkpoint was made; the release contains completed
evidence rather than a snapshot of that run's changing outputs.

Private licensed IBIS inputs, the model checker and derived manufacturer-model
circuits remain outside the repository. `Verification/prepare_analog.py`
recreates the pinned private cache from the original sources.

To create another backup while ordinary verification is running:

```sh
python3 Backup/create_checkpoint.py /path/outside/repository/checkpoint
```

The script archives the preserved experiment trees and the supplemental study
directories. It excludes normal stages' changing output directories and build
caches. Existing archive files are never overwritten. After uploading, download
the release assets and run:

```sh
python3 Backup/verify_checkpoint.py /path/to/downloaded/checkpoint
```

Verification streams every file from both archives, checks its hash and rejects
unlisted, duplicate or missing members. It does not extract files.

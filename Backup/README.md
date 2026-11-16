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

For an incremental backup of a completed study, use
`--study clock-integration` with `create_checkpoint.py`. The selected directory
must have passing remote-hash and browser checks. This produces one archive
and a manifest; keep the earlier release for the other project evidence.
Use `--experiment <directory-name>` to select a preserved run beneath
`Verification/build/experiments`. The options can be combined. Backup checks
verify preservation; a failed run keeps its original acceptance status.

## ACH 4 MHz staging checkpoint

The [clock-integration-2026-11-15 release](https://github.com/DutchMaker/DM-02/releases/tag/clock-integration-2026-11-15)
preserves the full staged candidate tree and its evidence at source commit
`4132cd84c19dee8e73fd414b2c62af3651aa74de`. All 2,464 archived files matched
both locally and after downloading from GitHub. The
[receipt](clock-integration-2026-11-15.json) records asset hashes and validation.

Staging passed 158 regressions, 150 clock profiles and connected FD1 execution.
All 46 interval paths pass conditionally at 4 MHz. The publication's 1,855
artifact hashes and desktop/mobile browser checks passed. Normal-source
promotion awaits completion and archival of the analogue-integrated full run;
physical-clock qualification remains open.

## Preserved analogue timeout

The [analog-timeout-2026-11-15 release](https://github.com/DutchMaker/DM-02/releases/tag/analog-timeout-2026-11-15)
preserves the full run that hit the 180-second ALU-sequence limit, plus the
isolated replay that passed all 145,536 rows in 156.126 seconds. All 3,812
archived files matched locally and after downloading. The
[receipt](analog-timeout-2026-11-15.json) includes asset hashes and retains the
failed run's error status. Its stale ALU log and coverage are explicitly marked.
A fresh unchanged full run was active when this backup was recorded.

## SRAM turnaround review

The [sram-turnaround-2026-11-15 release](https://github.com/DutchMaker/DM-02/releases/tag/sram-turnaround-2026-11-15)
preserves the static review of ME1/FD1 SRAM loads and command-release paths.
All 24 archive files were verified locally and after downloading; the
[receipt](sram-turnaround-2026-11-15.json) records the hashes. Conditional
blanking requirements are 56.5 ns read-to-write and 58 ns write-to-read.
Actual command gaps, loaded release and full-temperature capacitance remain
unqualified. Normal verification inputs were unchanged.

## Compact DIP redesign

The [compact-design-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/compact-design-2026-11-16)
preserves the complete CP1 source snapshot, native KiCad evidence, simulations,
BOM workbook and programming images at commit `22fee58`. All **1,784 files**
matched locally and after downloading from GitHub. The
[receipt](compact-design-2026-11-16.json) records the archive and manifest hashes.

CP1 uses **192 logic/memory ICs versus 288**, with all logic and memories in DIP.
Digital verification completed: 227 opcodes, exhaustive counter/address/memory
checks, 150 clock profiles, and ROM boot through graphics HALT across 2,840,175
microcycles. The observed 43,829 IO events produced exact text and zero errors
across 48,000 pixels. The earlier simulated-time watchdog failure is preserved
alongside the successful replay. Physical electrical qualification remains open.

The separate [normal analogue retry archive](https://github.com/DutchMaker/DM-02/releases/tag/analog-retry-timeout-2026-11-15)
preserves its graphics timeout and blocked boot dependency. All 3,796 files were
downloaded and verified; see its [receipt](analog-retry-timeout-2026-11-15.json).
CP1's staged results do not overwrite that run or its formal milestone totals.

## CP1 active verification

The [cp1-promotion-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-promotion-2026-11-16)
preserves the promotion report and bounded CD74HCT273E timing study at commit
`5fb7718`. All **176 files** matched locally and after downloading; the
[receipt](cp1-promotion-2026-11-16.json) records the archive hashes.

The default verification target is now CP1. Replay regenerates 446 HDL artifacts
and ten clock models from 430 pinned source files, runs a fresh CPU profile and
checks the current harness. All 161 tests passed. The unchanged milestone gates
now read **3/5, 3/5 and 8/9**; MOD-03 is satisfied by CP1's instruction evidence.
The reference run's timeout and boot error retain their original status.

This is an incremental archive. Restore `compact-design-2026-11-16` and
`analog-retry-timeout-2026-11-15` first for the reused evidence, then this archive.
The active source overlay and replay entry point are tracked in Git. See
[`Verification/CP1.md`](../Verification/CP1.md) for execution and source locations.

The alternative HCT273 passed eight sampled CPU/memory profiles with an added
3 ns hold monitor, with a smallest observed hold interval of 252.5 ns. The
alternative has not been adopted; physical loading and full qualification remain
open. This study does not close a physical milestone gate.

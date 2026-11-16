# Git and evidence checkpoints

## CP1-BR1 native-pin bridge candidate

The [cp1-bridge-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-bridge-2026-11-16)
archives source checkpoint `2ecbda7`. All **230 files** matched locally and
after download; see the [receipt](cp1-bridge-2026-11-16.json).

The bridge study is an additional bounded-replay dependency at
`Verification/build/cp1-bridge/`. It contains the native MQ1/BR1 sheets and
netlists, four passing simulation profiles, four detected mutations, seven TI
datasheets, explicit R2/CN1 bindings and both earlier iterations. The checked-in
`Verification/bridge-evidence.json` pins its sources and evidence.

The bounded replay passed **197 tests**; desktop/mobile browser checks and
**225 remote hashes** passed at `/build/cp1-bridge/`. Each of four bridge
profiles passed 70,020 read cases and 256 writes; all four injected faults
were detected. Earlier load-overage and common-reset runs remain preserved.

Restore the `cp1-bridge-2026-11-16` release assets using
`Backup/verify_checkpoint.py`, then extract `studies-and-workbook.tar.gz` from
the repository root. The R2, reference and readiness releases below are still
required. The bridge is a separate 41-DIP candidate; physical qualification
and incorporation into the CPU remain open.

## CP1-MC1 mechanical selection and CP1-CN1 draft connectors

The [cp1-connectors-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-connectors-2026-11-16)
preserves the approved mechanical target, native-linked contact tables, candidate
footprints, manufacturer catalog and bounded replay at `3c3704b`. All **47 files**
matched locally and after download; see the [receipt](cp1-connectors-2026-11-16.json).

The replay passed **190 tests**. Allocation checks cover 1,242 contacts; the
catalog/footprint screen covers 192 candidate contacts, mounting-hole spacings
and offsets, and drill nominals. Desktop/mobile checks and 42 remote hashes
passed at `/build/cp1-connectors/` on the Tailscale dashboard.

The historical partition proposal remains unchanged. MC1 records the subsequent
owner approval. CN1 remains a draft pin plan: exact mating/keying/stack-height,
implemented bridge/service circuitry, load/current/timing and physical gates
remain open. This release does not promote a circuit revision.

Default replay uses the MC1 source files and tracked historical partition screen,
plus the R2/reference/readiness evidence described below. This release is an
optional publication snapshot. Reproduce pin planning with a new `--output`
directory; preserve this published snapshot and its manifest.

## CP1-SC1 scope and CP1-IO1 logical expansion interface

The [cp1-io-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-io-2026-11-16)
preserves the approved first-machine scope, logical IO specification, native
connector audit and fresh replay at `1fc82eb`. All **29 files** matched locally
and after download; see the [receipt](cp1-io-2026-11-16.json).

The replay passed **182 harness tests**. The logical model checked 65,536
address reads and 1,024 write cases; the boundary audit checked 139 native
connector/storage pins. Desktop/mobile checks and 24 publication hashes passed
at `/build/cp1-io/` on the Tailscale dashboard.

The new addressed-read bridge, physical connectors and real text endpoint
remain unimplemented. These results do not promote a circuit revision or close
physical gates. The separate PCB partition proposal and reproducible area
screen are tracked in Git under `Verification/build/cp1-partition`; they await
owner approval and placement/routing checks.

This release is an optional report snapshot. Default replay still requires
the R2, reference and readiness releases described below.

## CP1-OC1 selected operating contract

The [cp1-contract-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-contract-2026-11-16)
preserves the selected operating contract, generated qualification matrix,
fresh replay report and source snapshots at `cb89622`. All **27 files** were
verified locally and after download; see the [receipt](cp1-contract-2026-11-16.json).
The replay passed **172 harness tests**. Desktop/mobile dashboard checks and
22 publication hashes passed.

CP1-OC1 selects 500 kHz microcycles, 4 MHz oscillator, 4.75–5.25 V at IC pins
and 0–50 °C ambient. Its 54 physical rows and 90 digital coverage requests
specify future qualification; they do not record completed measurements.
The circuit remains CP1-R2 and physical gates remain open. The publication is
at `/build/cp1-contract/` on the Tailscale dashboard.

This archive is a report snapshot. Default replay still needs the R2,
reference and readiness releases listed under restoration dependencies below.

## CP1-R2 clock and electrical readiness study

The [cp1-readiness-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-readiness-2026-11-16)
preserves 66 frequency experiments, three diagnostic traces and 35 conditional
timing rows at source commit `6ecedb2`. All **1,610 files** matched locally and
after download; the [receipt](cp1-readiness-2026-11-16.json) records their hashes.
Failed profiles and the source-drift rejection remain preserved.

The study recommends a conditional 4 MHz oscillator / 500 kHz microcycle target.
Its seven ranked electrical closure routes are documented in
`Verification/CP1-readiness.md`. It does not promote a new design revision or
close either physical release gate. The Tailscale publication is at
`/build/cp1-readiness/`; desktop/mobile checks and 1,605 remote hashes passed.

Download the release assets and verify them with `Backup/verify_checkpoint.py`,
then extract `studies-and-workbook.tar.gz` from the repository root. Restore
the CP1-R2 release separately for the pinned HDL/fixture dependencies. The
archived `Verification/build/cp1-readiness/REPRODUCE.md` gives commands for a
new isolated replay directory.

## Source and evidence storage

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

At this checkpoint, the alternative HCT273 passed eight sampled CPU/memory profiles with an added
3 ns hold monitor, with a smallest observed hold interval of 252.5 ns. The
alternative had not been adopted; physical loading and full qualification remained
open. This study does not close a physical milestone gate.

## CP1-R2 active revision

The [cp1-hct273-2026-11-16 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-hct273-2026-11-16)
preserves the accepted revision at commit
`606d816ad4a9888dc60b7fe4c5e68cb9526c4317`. All **1,906 files** matched locally
and after downloading from GitHub. The [receipt](cp1-hct273-2026-11-16.json)
records the archive and manifest hashes. The archive includes the complete
candidate, simulations, updated BOM, programming images, failed native-audit
attempt and final promotion report.

Three CD74HCT273E DIP registers replace SN74HCT273N at AL1 U2 and ME1 U11/U15.
Their documented clock/clear delay bounds resolve the earlier specification
ambiguity. The full fresh digital suite passed with a 3 ns data-hold monitor;
the smallest sampled interval was 243 ns. ROM boot completed 2,840,175
microcycles and 43,829 IO events, with exact text and zero errors across
48,000 pixels. All **164 harness tests** passed.

CP1-R2 remains at 192 DIP logic/memory ICs, saving 96 against the 288-package
baseline. Milestone totals remain **3/5, 3/5 and 8/9**. Exact stock/sourcing,
independent electrical review, actual loads and input edges, bus/SRAM release,
HC377 supply compatibility, reset/oscillator behaviour, programming/readback
and PCB/bench qualification remain open.

### Restoration dependencies

For default locked-evidence replay, restore this release,
`analog-retry-timeout-2026-11-15` and `cp1-readiness-2026-11-16` into the repository
root. The reference release supplies the pinned method evidence; the readiness
release supplies the hashed clock-selection evidence required by CP1-OC1.
The active overlay, operating contract and runner are tracked in Git; run
`python3 Verification/run.py --allow-design-failures` after restoration.

For full study reproduction, also restore `compact-design-2026-11-16` for the
comparative pin/net audit and original workbook. The R2 `run.py --prepare`
expects `Verification/build/microcode/microcode.rom` and
`Verification/build/alu/alu0.rom` through `alu7.rom`. Matching archived copies
are under `Verification/build/cp1-hct273/candidate/Verification/build/`;
copy them to those normal input paths before preparation. Full simulation
commands are in the archived `Verification/build/cp1-hct273/README.md`.

The [live dashboard](https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/)
and [R2 evidence](https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-hct273/)
are available through Tailscale.

# CP1 active verification

[CP1-MC1](Mechanical-contract.md) records the approved four-card/eight-position geometry. The [CP1-CN1 draft connector study](Connector-plan.md) maps native crossing nets onto candidate contacts and adds the live-read/debugger paths. The bounded replay checks this allocation separately from circuit and physical acceptance.

[CP1-BR1](IO-bridge.md) is a separate native-pin bridge candidate with 41 added DIP packages, four private returns and reset-safe write arming. The replay checks its pinned sources, regenerated HDL, R2/CN1 bindings and saved profile/mutation evidence through `bridge-evidence.json`. Restore `build/cp1-bridge/` from its release as an additional replay dependency. CPU integration, real text output and physical timing remain open.

[CP1-BI1](IO-CPU-integration.md) composes BR1 with all R2 CPU modules for a fetched diagnostic. Its 34-run matrix contains 29 passes, two endpoint-latency failures and three detected wiring faults. `io-cpu-evidence.json` pins this separate study; restore `build/cp1-io-cpu/` for bounded replay. The test uses preloaded memories and behavioral endpoints. A native integrated revision, autonomous boot with BR1 and real text remain open.

The active revision is **CP1-R2**. Three CD74HCT273E DIP registers replace SN74HCT273N at AL1 U2 and ME1 U11/U15. TI SCHS174D provides explicit clock/clear delay bounds of 38/40 ns at 4.5 V, −40 to 85 °C and 50 pF. The model retains the conservative 42 ns envelope and now enforces 3 ns data hold. A fresh complete digital suite, including ROM boot, passed before promotion. Evidence and the updated BOM are in `build/cp1-hct273/`.

`python3 Verification/run.py` now selects CP1. It writes the normal dashboard report with the existing milestone requirements. `--allow-design-failures` allows exit 0 while physical acceptance gates are open; missing or changed evidence still exits 2.

The active source overlay is in `targets/cp1/overlay/`. `targets/cp1/lock.json` maps its files and shared repository sources to the accepted 430-file CP1 input set. The overlay includes the ACH clock configuration, so the reference clock remains independently runnable. Historical copies of the runner, dashboard and reference documentation keep the accepted snapshot reproducible; the current runner and dashboard are fingerprinted separately.

## What a run checks

1. Verify the pinned evidence hashes, including receipts, fixtures, logs, HDL, programming images and the preserved reference report.
2. Materialize the active source set in a temporary isolated directory. A source mismatch requires new verification; the runner never updates its lock automatically.
3. Regenerate all 12 schematics and the assembly indices, then compare all 430 source files with the accepted snapshot.
4. Regenerate and compare 446 HDL artifacts plus ten clock models. Run a fresh continuous CPU profile in Icarus.
5. Run the current harness tests. Recheck sources and archived evidence before completing the report.

The long simulations are reused from [the CP1-R2 release](https://github.com/DutchMaker/DM-02/releases/tag/cp1-hct273-2026-11-16). The lock selects its evidence directory explicitly. The dashboard labels this mode **locked-evidence-replay**. A checkout needs the restored release evidence to replay it; see `Backup/README.md` for archive restoration and `build/cp1-hct273/README.md` for full simulation commands. The [original CP1 release](https://github.com/DutchMaker/DM-02/releases/tag/compact-design-2026-11-16) remains preserved.

The synthetic pilot, fault-monitor qualification, bounded analogue experiment, compiler comparison and exhaustive software control-flow oracle retain their original reference evidence and scope. Their sources are pinned by the CP1 input set. The original hardware-programs timeout and dependent boot error remain visible in the linked reference report.

## Reference execution

```sh
python3 Verification/run.py --target reference
```

This runs the original AL1/FD1 pipeline and replaces the dashboard report with that run. Select `--target cp1` to restore the CP1 report. The archived CP1 and failed reference runs remain separate immutable evidence sets.

## Acceptance

CP1 has 192 DIP logic/memory packages, down from 288. Digital acceptance covers all 227 opcodes, full counter/register/module checks and ROM boot through the 48,000-pixel graphics output.

Milestone gates are 3/5, 3/5 and 8/9 when replay and harness checks pass. MOD-03 is now satisfied by CP1's complete instruction-contract evidence. BASE-02/05, PILOT-04/05 and MOD-08 remain open. The conditional 4 MHz oscillator / 500 kHz microcycle result does not demonstrate the historical 1 MHz operating envelope.

The owner clarified on 16 November 2026 that 1 MHz is preferred rather than mandatory. The [clock and electrical readiness study](CP1-readiness.md) supports the selected [CP1-OC1 operating contract](Operating-contract.md): 500 kHz microcycles, 4 MHz oscillator, 4.75–5.25 V at IC pins and 0–50 °C ambient. The active report composes this contract with the unchanged requirement/gate map; the locked R2 requirements retain their historical values. Restore the readiness release as well as the R2/reference evidence before replay. Physical qualification remains open.

The approved [CP1-SC1 first-machine scope and CP1-IO1 logical interface](IO-interface.md) add text-first peripheral expansion and a separate ESP32/LCD debugger to the stack/backplane plan. The computer must boot and run independently. The active replay checks the logical address/handshake model and audits the native R2 IO pins. R2 exports a latched write address but no addressed read interface at J903; a qualified bridge and real endpoints remain engineering work. These checks do not promote a new circuit revision.

The selected HCT273's delay-table ambiguity is resolved. Its physical output loads and input edges still need qualification, alongside HCT245 IO loading/release, SRAM DQ loading/turnaround, full-supply HC377 compatibility and reset/oscillator behaviour. Hardware identities/counts, independent electrical review, programming/readback, PCB review and bench measurements are also outstanding.

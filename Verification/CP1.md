# CP1 active verification

`python3 Verification/run.py` now selects CP1. It writes the normal dashboard report with the existing milestone requirements. `--allow-design-failures` allows exit 0 while physical acceptance gates are open; missing or changed evidence still exits 2.

The active source overlay is in `targets/cp1/overlay/`. `targets/cp1/lock.json` maps its files and shared repository sources to the accepted 430-file CP1 input set. The overlay includes the ACH clock configuration, so the reference clock remains independently runnable. Historical copies of the runner, dashboard and reference documentation keep the accepted snapshot reproducible; the current runner and dashboard are fingerprinted separately.

## What a run checks

1. Verify the pinned evidence hashes, including receipts, fixtures, logs, HDL, programming images and the preserved reference report.
2. Materialize the active source set in a temporary isolated directory. A source mismatch requires new verification; the runner never updates its lock automatically.
3. Regenerate all 12 schematics and the assembly indices, then compare all 430 source files with the accepted snapshot.
4. Regenerate and compare 446 HDL artifacts plus ten clock models. Run a fresh continuous CPU profile in Icarus.
5. Run the current harness tests. Recheck sources and archived evidence before completing the report.

The long simulations are reused from [the checksum-verified CP1 release](https://github.com/DutchMaker/DM-02/releases/tag/compact-design-2026-11-16). The dashboard labels this mode **locked-evidence-replay**. A checkout needs the restored release evidence to replay it; see `Backup/README.md` for archive restoration and `build/compact-design/README.md` for full simulation commands.

The synthetic pilot, fault-monitor qualification, bounded analogue experiment, compiler comparison and exhaustive software control-flow oracle retain their original reference evidence and scope. Their sources are pinned by the CP1 input set. The original hardware-programs timeout and dependent boot error remain visible in the linked reference report.

## Reference execution

```sh
python3 Verification/run.py --target reference
```

This runs the original AL1/FD1 pipeline and replaces the dashboard report with that run. Select `--target cp1` to restore the CP1 report. The archived CP1 and failed reference runs remain separate immutable evidence sets.

## Acceptance

CP1 has 192 DIP logic/memory packages, down from 288. Digital acceptance covers all 227 opcodes, full counter/register/module checks and ROM boot through the 48,000-pixel graphics output.

Milestone gates are 3/5, 3/5 and 8/9 when replay and harness checks pass. MOD-03 is now satisfied by CP1's complete instruction-contract evidence. BASE-02/05, PILOT-04/05 and MOD-08 remain open. The conditional 4 MHz oscillator / 500 kHz microcycle result does not demonstrate the unchanged 1 MHz operating envelope.

The timing review still needs a guaranteed HCT273 clock-to-Q bound, HCT245 IO loading and release bounds, actual SRAM DQ loading/turnaround, full-supply HC377 compatibility, and qualified reset/oscillator behaviour. TI's HCT273 table labels both switching rows `CLR`; 42 ns remains a simulation assumption. Hardware identities/counts, independent electrical review, programming/readback, PCB review and bench measurements are also outstanding.

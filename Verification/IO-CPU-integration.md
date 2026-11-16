# CP1-BI1 CPU/bridge diagnostic

This study connects the [BR1 native-pin bridge](IO-bridge.md) to all eleven functional CP1-R2 CPU modules. It executes a short fetched program and observes the resulting writes at the slot pins. The accepted digital circuit remains CP1-R2; this composition is an experimental integration candidate.

## What executes

The CPU HDL, control ROM and ALU image are copied from hash-checked R2 profiles. MQ1/BR1 HDL is regenerated from the pinned native KiCad netlists. The new testbench retains the R2 clock/reset distribution, physical data-bus branches and source-contention monitor. HARD_ALU, HARD_REGISTERS, HARD_ADDRESS and HARD_MEMORY are all enabled. No host process advances registers or supplies expected bytes to the CPU data bus.

MQ1 receives live MAR, MEM_n, LOAD_n10 and the actual ME1_RESET_n branch. BR1 receives the reset root, ME1's registered IO_ADDRESS/IO_DATA/IO_STROBE and four private fixture returns. Its output drives ME1 IO_INPUT, then the existing ME1 output multiplexer, source driver, BF1 and CPU destination register. The composition follows the 45 R2 boundary bindings audited in BR1; it does not produce a newly accepted native CPU schematic assembly.

The 115-byte diagnostic initializes three fixture registers through `$FF10/$FF20/$FF30`, reads those values and text status at `$FF03`, and echoes every captured byte through `$FF00`. A second round changes all three values and reverses the read order. Unmapped `$FF11/$FF01` reads must return zero. A RAM read at `$FE03` must return `$3C`. The most recent write address differs from subsequent read addresses. All 14 echoed bytes are checked against a literal oracle; an independent architectural interpreter also checks the diagnostic's direct-address instruction encoding.

Program bytes are preloaded into the ROM and SRAM simulation models. The diagnostic starts from reset and hardware fetch, but this is **not an autonomous ROM-loader boot test**. It does not replace R2's preserved complete ROM-boot evidence.

## Endpoint fixtures and timing observations

Slot 5 returns `$81` at its status register. Slots 6–8 implement one byte each, written only by their matching W_ADDR at the actual buffered strobe. Returns depend on the slot's forwarded read address, read qualifier and reset, with a configurable inertial response delay. Absent slots drive high impedance and are masked by PRESENT_n. A passive slot-5 observer records echo writes even when the slot is marked absent; it never supplies data.

These fixtures are behavioral test partners. They do not implement the text mailbox, persistent ready credit, serializer, display or physical card. Response-delay experiments specify neither a guaranteed endpoint budget nor an accepted peripheral design.

At each I/O load of A, the probe measures the interval from the latest CPU data-bus transition to AL1_PH3. The sampled setup threshold is 35 ns: the model's 25 ns setup plus OC1's 10 ns reserve. It also reports the first subsequent bus change and requires at least 5 ns sampled hold. Existing device-level timing monitors remain active. Slot write data/address are checked against a 40 ns fixture setup/hold requirement. These observations cover the diagnostic's transitions, not every possible min/max arc assignment.

Complete qualification still requires actual IC output edges, loads, routing/connector bounds, endpoint timing, reset/strobe recovery and independent review. Zero-delay and alternating arc profiles are sensitivity experiments; passing them cannot establish a positive physical minimum delay.

## Preserved development evidence

The final matrix contains **34 runs: 29 passed, two deliberately slow endpoint cases failed, and three wiring mutations failed for the expected reason**. Twelve CPU delay profiles, four BR1 profiles including the all-maximum combination, five absent-slot masks and four oscillator duty/±30 ppm corners passed with a 40 ns endpoint fixture. Each passing run checked 14 echoes, 12 I/O captures and 334 microcycles, then reset inactivity after HALT. This integrated diagnostic does not exercise reset during an active transaction; BR1's separate reset-abort evidence remains scoped to its standalone fixture.

| Endpoint response | Microcycles | Smallest sampled setup | Outcome |
| --- | --- | --- | --- |
| 0 ns | 500 kHz | 181.5 ns | Pass |
| 40 ns | 500 kHz | 165.5 ns | Pass |
| 80 ns | 500 kHz | 125.5 ns | Pass |
| 120 ns | 500 kHz | 85.5 ns | Pass |
| 160 ns | 500 kHz | 45.5 ns | Pass |
| 200 ns | 500 kHz | Below the 35 ns threshold | Setup-reserve check failed |
| 400 ns | 500 kHz | Stable but wrong data | Echo comparison failed |
| 400 ns | 250 kHz | 555.5 ns | Pass at diagnostic lower clock |

The table uses all-maximum CPU/bridge arc models at nominal oscillator duty/rate. The 40 ns endpoint fixture's fastest sampled oscillator corners had 165.476 ns minimum setup; the lowest sampled hold across the main profiles was 250 ns. These are observed intervals, not guaranteed margins. The study does not select a new clock or qualify 160 ns as a universal endpoint limit.

The 400 ns failure also confirms why a stable-data interval alone is insufficient: the bus held zero long enough to pass a setup check, but the CPU captured the wrong value. Literal echo comparison caught it. Disconnected-return, stale-write-address decode and return-slot alias mutations also failed their echo checks.

`build/cp1-io-cpu/initial-max40` records an early bench-extraction failure. `baseline-max40` retains an elaboration failure caused by declarations following their use. `max40` and `trace-max40` preserve a diagnostic-encoding mistake: this CPU uses parentheses for pointer-indirect addressing, so those programs never reached the intended I/O addresses. `direct-max40` records the corrected direct-address diagnostic. The final study matrix is under `profiles/`; earlier runs are not counted as acceptance evidence.

## Reproduction

Restore the R2 and BR1 dependencies in `Backup/README.md`. Run a new profile in a new directory:

```sh
PYTHONPATH=Verification python3 -m dm02.io_cpu \
  --output Verification/build/io-cpu-new --endpoint-ns 40
```

Existing profile directories are never overwritten. `build/cp1-io-cpu/run_study.py` defines the bounded profile matrix; run a copied script in a new study directory to preserve the publication.

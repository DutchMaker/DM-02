# CP1 compact DIP computer

CP1 implements the ROM, register, counter, snapshot and shared-bus reductions as a complete pin-derived candidate. It has **192 logic/memory ICs versus DL1's 288**, including the added reset, counter-control, fanout and bus support circuitry. The oscillator and passives are outside both IC totals.

| Area | DL1 ICs | CP1 ICs |
|---|---:|---:|
| Clock | 11 | 10 |
| Control word | 17 | 14 |
| Sequencer | 21 | 21 |
| Program counter | 15 | 15 |
| ALU | 48 | 21 |
| B/C/H/L registers | 27 | 17 |
| Stack pointer | 27 | 20 |
| MAR | 46 | 33 |
| Memory/IO | 27 | 25 |
| Clock/reset/data distribution and selection | 49 | 16 |
| **Total** | **288** | **192** |

The selected memories are M27C322-100F1, M27C1024-10F1, W27C512-45Z and UM61512AK-15. Six SN74HC377N registers, eight HCT191 counters, nineteen HCT245 buffers and nine HCT574 registers are used. ACT175 count falls from 48 to 10; 157 mux count falls from 84 to 29. Exact stock counts and several manufacturer suffixes remain unknown. The workbook preserves unknown quantities as blanks and the confirmed ACT175 quantity as zero.

## Circuit changes

- One word-wide M27C322 replaces the eight-flash ALU array, address muxes and associated buffers. The PH1 result snapshot and PH3 flag capture are retained.
- One word-wide M27C1024 replaces the two byte-wide control EPROMs.
- Four enabled HC377s replace the B/C/H/L feedback-mux register cores. Shared zero-data selection and oscillator-clocked initialization implement reset; no simulator power-on zero is assumed.
- Four HCT191s each implement SP and MAR. Opposite-edge command staging, asynchronous-load windows and a delayed preset-data enable preserve count, load and reset timing. Ripple carry spans all sixteen bits.
- Three compatible 175 pairs become HCT273s. Other former 175s disappear through the register/counter architecture changes; the remaining ten have distinct clock/reset or complementary-output requirements.
- Four buffered source branches feed a shared DATA receiver. BF1 explicitly disables that receiver during reset, including forced-active output-command tests.
- DT1 distributes clock, initialization clock and reset through physical buffer branches. BP1 contains all 52 module connectors. Its 230 net groups are independently compared with the generated HDL interface bindings.

## Verification and reproduction

`verification-state.json` is authoritative for the serial regression's completion. A running or interrupted record is not a pass. `native-audit.json`, `physical-review.json`, `interconnect-check.json` and the dedicated `*-check.json` receipts have narrower scopes.

The standalone memory suite passed 131,073 reads, 48,897 SRAM writes, 16,384 protected ROM writes and 256 IO writes. The MAR suite passed 197,376 rows: complete 16-bit increment/wrap, byte loads, every PC/SP snapshot address and fetch-address transfers. These fixtures test the physical modules independently; the integrated CPU profiles include the actual distribution and shared-bus circuits.

The complete isolated source snapshot and native KiCad evidence are preserved in the release archive. Git tracks the changed/new candidate sources. On a fresh checkout, `restore.py` fills unchanged snapshot files from the checksum-pinned baseline commit. Unpack the evidence archive to restore ROM/compiler outputs and original execution artifacts, or regenerate those with the baseline verification toolchain.

From the repository root:

```sh
python3 Verification/build/compact-design/restore.py
python3 Verification/build/compact-design/run.py --prepare
python3 Verification/build/compact-design/audit.py --native
python3 Verification/build/compact-design/physical.py
python3 Verification/build/compact-design/component_review.py
python3 Verification/build/compact-design/verify.py
python3 Verification/build/compact-design/interconnect.py
python3 Verification/build/compact-design/finalize.py
python3 Verification/build/compact-design/publish.py
```

The full ROM-booted graphics run has millions of microcycles. `run.py` derives its timeout from measured completed profiles with 2.5× headroom. `resume.py` retains matching completed profiles after the execution-budget correction; it checks emitted HDL, schematic and completed-log hashes before accepting them.

The first complete boot replay reached the inherited four-second **simulated-time** watchdog after correctly reconstructing 16,542 payload bytes with 24,326 SRAM writes. The independent fixture requires 2,840,175 microcycles: 5.68035 simulated seconds at CP1's rate. That failed run is preserved in `failed-runs/boot-watchdog-4s/`. The corrected watchdog allows two expected schedules plus 1 ms (11.3617 seconds). `check_program_budget.py` checks that real-valued delay in Icarus before replay. Circuit delays, cycle-by-cycle expectations and final HALT/IO checks are retained. The inherited 128 KiB SRAM fixture is cropped to its identical first 64 KiB for the actual UM61512.

The normal analogue retry is separately preserved under `../experiments/2026-11-15-analog-retry-timeout/`. Its graphics simulation exceeded the inherited one-hour timeout, and its dependent boot stage did not run. CP1 does not turn that failed run into a pass.

## Electrical boundary

The target is a **4 MHz oscillator / 500 kHz microcycle**. Digital delay models and sampled corners do not establish the complete physical operating envelope:

- HCT245 propagation/enable bounds use the 150 pF table. Its disable bound is specified at 50 pF. IO-port capacitance is an allocation, not a guaranteed maximum.
- SN74HCT273 SCLS068H labels both switching-delay rows CLR. The model's 42 ns clock-to-Q value is an explicit assumption pending manufacturer clarification, not an accepted guaranteed clock bound.
- UM61512 read timing uses 30 pF; high-impedance timing uses 5 pF. Actual DQ loading and turnaround need qualification.
- The HC377 receiver review covers a common 4.5 V DC table point. Full-supply thresholds and loaded edges remain open.
- Reset request is an external qualified input. The owned MCP100-450D does not by itself establish valid 4.75 V startup.
- Oscillator startup, supply integrity, PCB routing, external display/front-panel electronics, programming/readback and bench measurements remain open.

The normal milestone requirements are unchanged. This candidate is not a fabrication release, and its results do not inherit FD1's private-link timing or analogue qualification.

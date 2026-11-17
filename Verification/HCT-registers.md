# HR1 HCT377 candidate

HR1 extends HB1 with six **CD74HCT377E** DIP-20 packages. AL1 U6/U7 become U5006/U5007 in the integrated hierarchy; RG1 U3/U8/U13/U18 become U6003/U6008/U6013/U6018. Their pin assignments, footprints and nets match HB1. The candidate contains 610 fitted components, 272 DIP ICs and 7,368 physical pins: 134 HCT, 115 AHCT, nine AHC, ten ACT and four memories.

The checked-in root is `Circuits/KiCad/Integrated/candidates/HR1/HR1.kicad_sch`. **CP1-R2 remains the accepted digital design.** HR1 supplies conditional digital evidence for the substitutions; physical qualification and production promotion remain open.

## Manufacturer conditions and connected paths

TI **SCHS184C**, HCT rows on pages 4–6, specifies the following at 4.5 V, −40 to 85 °C and a 50 pF output fixture:

| Parameter | Model requirement |
| --- | ---: |
| Clock to Q, maximum | 48 ns |
| Data and enable setup | 15 ns |
| Data hold | 3 ns |
| Enable hold | 5 ns |
| Clock HIGH and LOW pulse width | 25 ns |

Input timing edges use 6 ns between 0.3 and 2.7 V, with 1.3 V delay references. The output-transition maximum is 19 ns at that fixture. The 57 ns clock-Q value belongs to the wider −55 to 125 °C column; 16 ns at 5 V/15 pF is typical. None supplies a guaranteed minimum propagation delay. Zero and alternating 0/48 ns profiles are sensitivity experiments.

HCT inputs require HIGH ≥2 V and LOW ≤0.8 V across 4.5–5.5 V. At 4.5 V/4 mA and −40 to 85 °C, the HCT377 output table gives HIGH ≥3.84 V and LOW ≤0.33 V. The 45 connected output receivers are M27C322 address inputs and SN74HCT245 data inputs, both with 2/0.8 V thresholds. The table-point margins are 1.84 V HIGH and 0.47 V LOW before rail/ground offsets. Three unused Q outputs have no receivers.

The upstream drivers are SN74AHCT00N/08N/157N/244N, SN74HCT245N and SN74HCT574N. The reviewed 4.5 V tables give at least 1.8 V HIGH and 0.36 V LOW margin into HCT377 at their stated test currents. `path-review.json` enumerates all 108 signal pins, exact peers, source hashes and load scenarios. Rail-tied inputs are recorded separately. The IC-only output load screen is 0 or 10 pF; AL1's incoming DATA nets retain 90–100 pF before parasitics and their existing HCT245 obligations.

These comparisons do not establish actual total DC current, input-voltage ceilings under rail gradients, loaded slew, socket/layout/probe capacitance or full OC1 timing. HCT's extra supply current with TTL-level inputs is distinct from input leakage. OC1 remains 4 MHz oscillator / 500 kHz microcycles, 4.75–5.25 V at IC pins and 0–50 °C.

## Resetless storage and the startup finding

The six 377s have no reset pin. `hdl/hct377.sv` starts storage unknown, captures on rising clocks with active-low enable, and retains storage through reset. Its reset observation port never clears storage. Data hold follows whether the last clock captured data; it does not depend on the current enable value. Enable hold has its own monitor.

The stricter initial model found RG1 enable/setup violations during the reset transition. The maximum-delay standalone register fixture first failed at 60 ns; the zero-delay fixture failed at 1 ns. Those runs remain in `iteration-2/`. The previous model suppressed these checks during reset.

The final model records each reset-time timing violation and poisons storage with X. A later clean clocked capture can recover digital state. Each RG1 device must have a valid capture and known storage before reset release; otherwise the model fails. Violations outside reset fail immediately. This models digital recovery, not the analogue behaviour or settling time of a metastable physical register.

Final valid register profiles record 4/4/2 reset-time events. The three instruction profiles record 1,816/1,816/1,362 events across their repeated test resets. The four boot profiles record 4/4/6/1 events. Those events are retained in the logs rather than counted as clean timing. Physical reset-clock mux transitions and recovery remain with Beads `dm02-57n.3.5` and `.3.9`.

## Verification

`build/cp1-hct-registers/iteration-3/summary.json` records:

- Three valid register profiles, each with 2,052 captures, 4,096 transfers and four resets. Disabled enable and missing initialisation-clock faults fail with unknown stored state.
- ALU diagnostics with 8,192 full-profile vectors and 256 mixed-profile vectors; both also exercise 256 flag cases and 64 command cases.
- Three complete fetched-instruction profiles, each with 454 cases and 23,002 microcycles.
- Four ROM-only text boots. Each reconstructs 160 SRAM bytes, enters `$4000`, and finishes `TX1` CR/LF after HALT. All retain HB1's actual 42 ns address-buffer model, including the zero/mixed HCT377 profiles.
- Eleven cell-model cases: two valid behaviours and nine detected timing/startup faults. One deliberately relaxes enable hold to zero only in the monitor unit test so that an enable change cannot hide a data-hold violation.
- Three native mutations: swapped data pins, exchanged clock/enable and a wrong part identity. All fail native comparison.

The native-derived bindings check every target pin against the pinned R2 node map before replacing a model instance. The intentionally disabled-enable fixture has an explicit fault binding; ordinary mismatches are rejected.

| Check | Smallest sampled valid-event reserve |
| --- | ---: |
| Data setup beyond 15 ns | 65.5 ns |
| Enable setup beyond 15 ns | 168.5 ns |
| Data hold beyond 3 ns | 109 ns |
| Enable hold beyond 5 ns | 1.5 ns |
| HIGH pulse beyond 25 ns | 30.5 ns |
| LOW pulse beyond 25 ns | 55.5 ns |

These minima exclude the explicitly poisoned reset violations and cover only the exercised profiles. The boot CPU/IO setup observations are 81.5/710/373/352 ns; hold observations are 425.5/250/367/364.5 ns. They do not establish physical worst-case margins.

## Replay and preservation

`hct-register-evidence.json` pins the candidate, cell model, source conditions, native bindings, diagnostic inputs and results. The normal bounded replay regenerates the affected HDL and compares the saved evidence; fresh long simulations are required when an affected input changes.

```sh
python3 Verification/run.py --allow-design-failures
PYTHONPATH=Verification python3 -m dm02.hct_registers --output Verification/build/cp1-hct-registers/new-attempt
```

Restore the HR1 release plus HP1/HB1, TB1, R2 and the dependencies listed in `Backup/README.md`. Earlier R2/MD1/HB1 sources and locks are preserved. HR1 iteration 1 retains the native mutation-coordinate failure; iteration 2 retains reset-transition failures and rejection of the intentionally altered binding; `startup-check/` records the recovery model before the final run.

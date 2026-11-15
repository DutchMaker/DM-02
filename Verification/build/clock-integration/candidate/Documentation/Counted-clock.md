# Counted-clock candidate C1

C1 uses the through-hole ACH-4.000MHZ-EK candidate to produce a nominal
500 kHz cycle from 4 MHz. PH1 lags PH0 by three oscillator periods (750 ns),
and PH3 lags PH2 by the same interval. This aligns C1 with FD1's 4 MHz target.
The candidate is in `Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch`.
The active seven-sheet baseline still contains the RC-delay clock.

## Circuit and controls

U1 is a CD74AC175M96 four-bit phase register. Its valid sequence is:

```
0000 → 0001 → 0011 → 0111 → 1111 → 1110 → 1100 → 1000 → 0000
```

Only 0000 can wait for a request. The next-state equation is
`D0 = NOT Q3 AND (Q0 OR REQUEST_SYNC)`, with D1–D3 shifted from Q0–Q2.
Removing a request lets an active cycle finish. Synchronization latency can
admit another complete cycle; RUN is not an instantaneous stop.

U2 captures the next state on the opposite oscillator edge. U1 then copies
U2 on its own edge. This provides a half-cycle hold window without assuming
a positive minimum propagation delay. U3 conditions the TTL oscillator output;
U10 provides one buffered clock branch per edge. U9 drives the phase outputs:

| Signal | Source | Idle level |
| --- | --- | --- |
| CLOCK_PH0 | NOT Q0 | 1 |
| CLOCK_PH1 | NOT Q3 | 1 |
| CLOCK_PH2 | Q0 | 0 |
| CLOCK_PH3 | Q3 | 0 |

The complementary and delayed phase relationships match the existing circuit,
but the idle levels change. PH2 must park low: the extracted Memory circuit
keeps RAM/IO writes active when PH2 and a write command are both high. The
candidate checks write inhibition during idle across all 256 address pages.
An end-to-end controller and bus hookup review is still required.

The request synchronizer uses opposite-edge flip-flops. U7's second flip-flop
latches a rising STEP input while idle. Starting a cycle clears that pending
request. Holding STEP high produces one cycle; STEP during an active cycle is
ignored. STEP must already be debounced. RUN high requests continuous cycles.

J1 pins 1–8 are 5V, GND, RESET_IN_n, RUN, ACTIVE, READY, GND, STEP.
J2 pins 1–8 are 5V, GND, PH0, PH1, PH2, PH3, GND, unconnected.

## Reset and startup

Three reset-release stages cross alternating edges. The phase and staging
registers leave reset on different half-cycles, with an interval before their
next clock edge. Assertion is asynchronous and **aborts** an active cycle.
It can shorten a phase pulse and cause a temporary setup/hold collision while
reset propagates. Tests report those collisions as `RESET_ABORT` events and
check subsequent clearing and restart.

Receivers must be inhibited during reset and controller initialization. C1
does not yet provide that system-wide inhibition. Reset drives PH2/PH3 low,
but the resulting PH0/PH1 rising edges can still affect a connected controller.

The archived ACH family sheet specifies a 10 ms maximum startup time. C1 allocates
25 ms of external reset after the supply becomes valid. The digital test uses
an already-running ideal oscillator; it tests reset sequencing, not oscillator
startup. READY reports internal reset release, not supply validity. A power
supervisor remains to be selected and connected.

## Selected parts and sources

| References | Manufacturer part | Package |
| --- | --- | --- |
| Y1 | Abracon ACH-4.000MHZ-EK | Half-size four-lead oscillator, DIP-8 outline |
| U1–U2 | TI CD74AC175M96 | SOIC-16 |
| U3 | TI SN74AHCT04N | PDIP-14 |
| U4 | TI SN74AHC32N | PDIP-14 |
| U5 | TI SN74AHC08N | PDIP-14 |
| U6–U8 | TI SN74AHC74N | PDIP-14 |
| U9–U10 | TI SN74AHCT244N | PDIP-20 |

There is a 100 nF capacitor for each logic package and the oscillator. Exact
passive parts, distributor availability and footprint review remain open.
SOIC adapters would be needed for a socketed breadboard build.

`Verification/clock-parts.json` records limits and source pages.
`Verification/vendor/clock/manifest.json` records manufacturer URLs, downloaded
PDF hashes and retained text-excerpt hashes. The repository retains the relevant
extracted pages. Limits cover the project's 4.75–5.25 V and 0–50 °C envelope,
subject to the specified load and input-transition conditions.

ACH pins are 1=NC, 4=GND, 5=output and 8=5V. The model checks the exact symbol,
footprint, pin map, NC isolation and sole U3 input receiver. Its 15 pF standard
load is fully allocated: 10 pF receiver input plus 5 pF routing/socket/probe.
The nominal footprint grid matches the manufacturer's 7.62 mm square. Full
lead/hole insertion tolerance, actual loading and owned inventory are open.
The archived manufacturer-origin ACH sheet is dated 2016-11-15; current
lifecycle, latest revision and procurement remain unconfirmed.

## Conditional timing budget

The analysis uses ±30 ppm oscillator tolerance, an assumed 37–63% duty range
at receiver thresholds, maximum device delays and zero minimum propagation
delay. ACH specifies 45–55% duty at half supply. The wider receiver-duty range
is a sensitivity assumption; the sheet does not establish receiver-threshold
duty, edge measurement levels, monotonicity or cycle-to-cycle jitter.

| Quantity | Bound |
| --- | ---: |
| Output launch-to-capture interval | at least 718.28 ns |
| Existing synthetic pilot requirement | 208 ns |
| Conditional pilot margin | +510.28 ns |
| Phase-output pulse width | at least 968.27 ns |
| Narrowest internal setup margin | +44.80 ns |
| Shortest internal hold margin | +62.00 ns |

The bounds depend on these allocations:

- Critical U4/U5 outputs stay within the 15 pF timing bin: one receiver with a
  10 pF maximum input capacitance plus 5 pF for routing. Increasing the global
  routing allocation to 6 pF also exceeds the oscillator's 15 pF load rating,
  so the candidate no longer passes its conditional interface budget.
- Other characterized outputs stay at or below 50 pF. Clock branches and
  connector loads are counted separately. The old 1 nF load is absent.
- Internal routing and jitter allowance is 2 ns; output timing allows 10 ns.
  The oscillator data sheet provides no cycle-to-cycle jitter bound.
- Delay tables assume specified input transition times. Oscillator/buffer/gate
  slew compatibility needs electrical modelling or measurements.

PCB extraction and electrical qualification must support these allocations.
No typical value is used to establish hold time.

## Reproducible checks

`Verification/dm02/clock.py` reads KiCad pin nets and generates device HDL.
KiCad independently exports an endpoint review sheet and netlist. A second
route imports the original symbol libraries through KiCad and places their
native geometry. All pin groups, including singletons, must agree with the
Python source extractor. Native review drawings are under `build/clock/native/`.

150 runs cover zero delay, maximum delay and eight mixed-delay assignments
at every combination of 37/45/50/55/63% duty and −30/0/+30 ppm. Each run checks 24 one-cycle
request handshakes, 17 STEP-latch cases, 32 stop positions/offsets, reset from
all eight phase states and four startups with RUN already asserted. The phase
outputs also drive the existing register/ROM/buffer pilot with data, setup and
hold monitors.

Mutations change the staging edge, reset-release edge, stop logic, feedback
polarity, phase routing and pending-latch clear. Separate checks reject excess
loading, jitter and an insufficient startup allowance. Asynchronous entry-stage
metastability is outside this HDL model; downstream timing remains monitored.

All counted-clock benches consume the oscillator period emitted from the
selected part contract. Independent cycle/phase monitors reject a doubled
actual oscillator rate. FD1 records the same part identity and rejects a
frequency mismatch. Its interval review keeps 8 MHz as a counterfactual test,
which now also fails the HALT synchronization path under the wider receiver-duty
assumption, alongside ROM delivery, SRAM delivery and external IO setup.

```sh
PYTHONPATH=Verification python3 -c 'from dm02.clock import run; print(run())'
PYTHONPATH=Verification python3 -m unittest discover -s Verification/tests -p test_clock.py -v
```

Evidence is under `Verification/build/clock/`: review schematic, pin netlist,
manufacturer excerpts, budget, VCD and per-corner logs. The drawing helper
`Verification/designs/clock_candidate.py --write` recreates the legacy sheet;
without `--write`, it checks for divergence. Verification reads the checked-in
schematic, not the drawing generator.

## Next integration work

1. Connect a qualified debounce/HALT/CONTINUE front end and power supervisor.
2. Implement receiver reset inhibition, including writes and flag captures.
3. Verify input slew and oscillator jitter; extract loads and clock routing
   from a candidate layout. Revise the critical-path logic or frequency if the
   15 pF and 2 ns allocations cannot be met.
4. Connect C1 to controller, MAR/stack and ALU timed models, including bus
   output-enable handover, before replacing the active clock.

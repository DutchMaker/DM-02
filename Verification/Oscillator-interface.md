# CP1-OS1 oscillator interfaces

OS1 audits the two independent ACH-4.000MHZ-EK oscillators in MD1. Each output has **one 10 pF receiver allocation**, with different receiver families and timing conditions. The circuit is unchanged; CP1-R2 remains accepted.

| Link | Raw output | First receiver | Timing input-edge fixture |
| --- | --- | --- | --- |
| CPU C1 | Y1001.5 | U1003.1, SN74AHCT04N inverter | ≤3 ns |
| Text TX1 | Y14001.5 | U14002.2, CD74HCT244E buffer | 6 ns |

The earlier generic description of both clocks as HCT-fed was incomplete. CPU's first stage is AHCT. Its recommended input-transition limit is 20 ns/V, distinct from the timing-generator condition. HCT244 lists 500 ns input rise/fall at 4.5 V and 400 ns at 6 V, also distinct from its 6 ns timing fixture. No interpolation of those table points into a full-rail guarantee is claimed.

## Manufacturer evidence

The archived Abracon 2016 sheet specifies the selected 4 MHz part at 15 pF output load, 10 ns maximum rise/fall, 45/55% symmetry at half supply and 10 ms maximum startup. The `E` option covers −20 to +70 °C; `K` is ±30 ppm. Its stated stability includes initial tolerance and temperature stability. The sheet supplies no jitter maximum or explicit rise/fall reference voltages.

The selected suffix includes neither the optional `50` load rating nor the `A` tri-state option. Pin 1 is NC in both native instances. The optional enable/disable times cannot be used as reset control for these fitted candidates.

The full TI AHCT04 data sheet was retrieved and matches the previously archived PDF SHA-256 exactly. Figure 6-1 on page 7 was visually reviewed: input-generator edges are ≤3 ns, input timing reference is 1.5 V and output reference is VCC/2. The figure's text had been omitted by the earlier text extraction. The full PDF and extracted page are preserved in `build/cp1-oscillator/sources/`.

HCT244's section 5.9 specifies a 50 pF load and 6 ns input edges. At the inherited 4.5 V / −40 to +85 °C review point, its propagation maximum is 31 ns and output transition maximum 15 ns. A 15 ns output-transition specification does not establish the next receiver's 6 ns timing-fixture condition. Similarly, the presence of an AHCT04 inverter does not by itself qualify the CPU's downstream edges.

The ACH 10 ns specification therefore proves neither the CPU's 3 ns fixture nor TX1's 6 ns fixture. This identifies unsupported delay assumptions; it does not demonstrate a malfunction. Input transition recommendations, characterized propagation conditions, clock frequency capability and actual loaded waveforms are separate checks.

## Native front ends and load targets

CPU C1 first inverts the raw oscillator through U1003 pins 1→2, then inverts again through pins 3→4. The first root feeds U1010's CLK_P and INIT_CLK paths; the restored-polarity root feeds CLK_N. TX1's first HCT244 stage is non-inverting and always enabled. Its OSC_CLK output clocks two HCT161 counters and the first HCT74 request synchronizer.

The audit retains all native receiver pins and conditional capacitances on both raw links and six conditioned links. It checks power/ground, NC pins, clock-buffer enables and opposite CPU root nets. Both oscillators free-run through HALT; CPU phase control and TX1 serialization use their separate clocks.

| Link | IC-only subtotal | Socket/routing/probe target | Total planning load | Remaining margin |
| --- | --- | --- | --- | --- |
| Each raw oscillator | 10 pF | 4 pF | 14 pF | 1 pF to 15 pF rating |
| CPU ROOT_P, U1003.2 | 30 pF | 7 pF | 37 pF | 13 pF to 50 pF fixture |
| CPU ROOT_N, U1003.4 | 10 pF | 5 pF | 15 pF | 35 pF to 50 pF fixture |
| CPU CLK_P, U1010.18 | 40 pF | 8 pF | 48 pF | 2 pF to 50 pF fixture |
| CPU CLK_N, U1010.16 | 30 pF | 7 pF | 37 pF | 13 pF to 50 pF fixture |
| CPU INIT_CLK, U1010.14 | 10 pF | 5 pF | 15 pF | 35 pF to 50 pF fixture |
| TX1 OSC_CLK, U14002.18 | 30 pF | 7 pF | 37 pF | 13 pF to 50 pF fixture |

Raw links allocate 1 pF per attached socket pin, 1 pF for route/via/pad and 1 pF for the probe including attachment. There are two attached IC pins. The conditioned links allocate 1 pF per attached pin, 2 pF routing and 1 pF probe. These are restrictive design targets, not measured or manufacturer-guaranteed values. A nominal 10 pF passive probe would put the raw planning load at 23 pF; it cannot be attached under this target.

The selected socket, actual layout and low-capacitance probe must be qualified against these targets. No trace length is inferred without the board stack and geometry. AHCT input capacitance is specified at 5 V; HCT244's capacitance supply condition is unresolved in the inherited review. Complete loads across OC1 remain unknown even when the planning sums fit. The targets are recorded in `oscillator-interface.json`.

## Threshold duty and synthetic checks

Half-supply symmetry is not receiver-threshold duty. OS1 supplies a piecewise-linear waveform analyzer that reports crossings at Vdd/2, 1.5 V, 0.8 V and 2 V, plus 10–90% edges. It checks period consistency and exposes the different high-width results. Threshold brackets presume monotone edges; ringing can add clock events.

The reproducible matrix contains **81 synthetic cases**: three supplies (4.75/5/5.25 V), three half-supply duties (45/50/55%), three frequency offsets (−30/0/+30 ppm), and three assumed 10–90% edge durations (3/6/10 ns). These are mathematical analysis fixtures, with no temperature or physical device model. Their numerical edge comparisons cannot establish equivalence to the manufacturer's unspecified ACH edge definition or qualify a logic delay.

For example, a synthetic 5 V waveform at 45% half-supply duty and 10 ns 10–90% edges has a 112.5 ns half-supply high interval but a 117.5 ns high interval at 1.5 V. Reusing 45% at the receiver would lose that distinction. The inverter's propagation asymmetry and downstream load can change duty again.

Extra-edge and missing-cycle fixtures fail the period screen. Startup-contract fixtures accept a qualified clock after a full 25 ms continuously valid-supply guard and reject a shortened guard, brownout without restarting the guard, and an unqualified clock. These checks exercise the analysis and acceptance logic; they do not implement a physical supervisor.

Six static mutations are rejected: extra raw-clock receiver, treating CPU as a 6 ns timing fixture, borrowing the 50 pF oscillator option, driving NC pin 1, attaching a 10 pF probe and changing the CPU's first-stage polarity.

## Measurement route

The selected route is explicit layout/probe targets followed by manufacturer clarification and representative loaded measurements. Adding another buffer without these checks could increase raw loading and would not automatically supply a valid downstream edge guarantee.

`summary.json` includes a measurement plan for both front ends at the OC1 nine-point voltage/temperature grid. It requires:

- Actual pin supply, full loads and input/conditioned-output waveforms, including probe and fixture response.
- Rise/fall definitions, monotonicity, overshoot, repeated crossings, first-stage propagation/asymmetry, CPU CLK_P/CLK_N separation and TX1 OSC_CLK.
- Period and cycle-to-cycle jitter, high/low widths and duty at half supply and receiver references, with uncertainty.
- Startup and interrupted ramps, reset, stop/resume, step and HALT. Reset release requires both a qualified clock and the restartable 25 ms guard.

OC1's receiver-duty range 0.37–0.63 and 2 ns internal routing/jitter allowance remain design targets. The oscillator's 10 ms startup maximum alone does not qualify reset release. Exact part/lot coverage, repetitions and sample-qualified bounds require independent review; every measured field in OS1 remains null.

Physical work stays in Beads under `.3.6`, `.4.2.2`, `.8.1`, `.8.2` and review `.7.2`. Jev workflow guidance was unavailable; no advisory or independent review is claimed.

## Replay

`oscillator-evidence.json` pins the native analysis, 81 synthetic cases, faults, measurement plan and manufacturer sources. Normal bounded replay regenerates all analysis and verifies upstream MD1 evidence:

```sh
python3 Verification/run.py --allow-design-failures
```

Restore MD1 and its earlier dependencies through `Backup/README.md`, then `build/cp1-oscillator/`. No circuit change was made, so unchanged long CPU/ROM/text simulations were not repeated. Their existing evidence remains pinned upstream.

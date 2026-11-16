# CP1-R2 clock recommendation and electrical closure study

Engineering study, 16 November 2026. Beads: `dm02-57n.1.5` and `dm02-57n.3.10`.

## Clock recommendation

**Use a 4 MHz oscillator / 500 kHz microcycle rate as the first-build engineering target.** Keep the existing 4.75–5.25 V at IC pins and 0–50 °C ambient requirements. Instruction throughput depends on the instruction's microcycle count. The owner's preferred 1 MHz microcycle rate would require an 8 MHz oscillator.

This recommendation is conditional on closing the electrical and timing issues below. It does not select a physically qualified fabrication envelope or promote a new design revision. `dm02-57n.1.1` owns that contract and its downstream requirements updates; CP1-R2 and its historical requirements remain the accepted digital baseline.

The new study supports retaining 500 kHz:

- The 4 MHz reference reproduces the archived 1,424-cycle test, including three HALTs and twelve single steps, under both observation methods.
- At 5 MHz / 625 kHz, all nine capture-observed short profiles pass (delay selections 1, 4 and 7; receiver duties 37%, 50%, 63%; +30 ppm). A targeted maximum-delay, 37%-duty all-opcode profile also passes: 227 opcodes, 454 cases, 23,002 cycles. This gives sampled digital speed headroom, not a guaranteed 25% timing margin.
- At 6 MHz / 750 kHz, all three maximum-delay profiles have the wrong bus value at the capture edge. Six mixed-delay profiles pass.
- At 8 MHz / 1 MHz, all nine nonzero-delay capture-observed profiles fail. Six fail the HCT191 asynchronous-load pulse/data-setup assertion in MA1; three have invalid data at capture. The unmodified device checks provide direct reasons not to select this rate with the current circuit/model.

The initial 37-profile proportional-observation sweep is retained in full. Its earlier functional observation window creates false failures at 5 MHz: `2.4 × 200 ns = 480 ns` is earlier than the observed 514.5 ns same-word memory path. A second, 28-profile sweep observes the bus at the existing PH3 connector-monitor edge and retains the original 250 ns state-settle interval. Device delays and setup/hold assertions are identical in both sweeps. The all-opcode run is an additional profile. No long ROM boot was repeated.

### The limiting path is the same-word address transfer

Opcode 0x42, first execute word 0xd68c, transfers PC to MAR and reads the immediate byte into SP in the same microcycle. A stable-address SRAM budget misses this dependency. The path is:

`PH2 → SQ1 execute gate → CW1 function decode → MA1 PC transfer/preset → HCT191 address outputs → W27C512 → two AHCT157 muxes → ME1 U9 → BF1 U104 → BF1 U105 → SP1 load`.

In MA1, the transfer-control branch runs through U119 (two OR gates), U124 (fanout), U121 (transfer-window AND), U120 (preset OR), U117 (inverter), U121 (reset AND), then U3/U4 or U5/U6 asynchronous load. The transfer window itself comes from the opposite-edge U2/U8 circuit and needs separate min/max closure.

Observation-only traces of the first three cycles give these maximum-delay, 50%-duty samples:

| Oscillator | PH2 → MAR updated | PH2 → correct DATA | Correct DATA → root PH3 |
|---|---:|---:|---:|
| 4 MHz | 236.5 ns | 527.5 ns | 222.5 ns |
| 5 MHz, +30 ppm | 223.5 ns | 514.5 ns | 85.482 ns |
| 6 MHz, +30 ppm | 223.5 ns | Still old data at PH3 | Fails |

The original address connector contract requires 40 ns setup. The first two samples therefore exceed that contract by 182.5 ns and 45.482 ns respectively. These are individual simulation samples, not whole-machine minima or physical measurements. At 6 MHz, the unchanged post-MAR model chain needs 291 ns (45 + 24 + 3×74); it would settle about 14.5 ns after the capture edge.

### Conditional analytical screens

`build/cp1-readiness/timing_screen.py` checks pinned CP1 HDL and evaluates seven selected paths. It uses CD74ACT175E's 13 ns bound, 50 pF clock-gate bounds, zero earliest capture delay, +30 ppm, a hypothetical 37% minimum receiver duty, and the existing 2 ns internal / 10 ns output routing-and-jitter allocations. It does not reuse the FD1 interval results.

| Screen | Margin at 4 MHz | Margin at 5 MHz | Margin at 8 MHz |
|---|---:|---:|---:|
| Opposite-edge clock next-state | +40.0 ns | +21.5 ns | −6.3 ns |
| PH0 control address → PH1 word | +479.0 ns | +329.0 ns | +104.0 ns |
| PH3 operands → PH1 ALU result | +752.5 ns | +552.5 ns | +252.5 ns |
| PH1 word → PH2 format readiness | +116.5 ns | +66.5 ns | −8.5 ns |
| Fetch SRAM → IR | +322.5 ns | +172.5 ns | −52.5 ns |
| Execute SRAM, stable address, receiver data-side envelope | +266.0 ns | +116.0 ns | −109.0 ns |
| Same-word MAR → boot ROM, transfer-control branch | +153.0 ns | +3.0 ns | −222.0 ns |

The final row assumes preset data and TRANSFER_WINDOW are already ready. Later window arrival worsens it; the 4 MHz trace demonstrates that the window can dominate. The receiver envelope excludes destination-specific counter/control logic. These screens identify speed constraints; they are not an exhaustive setup/hold certificate. At 625 kHz the control-branch screen has only 3 ns remaining, so the passing simulation is insufficient reason to increase the first-build target.

A 2 MHz oscillator / 250 kHz microcycle is an analytical fallback if measured maximum-delay paths require more time. It has not been simulated here; the archived fixed HALT/STEP waits require review before slower-clock tests. Slowing the clock does not establish output-release, minimum-delay, threshold, reset or power guarantees.

## Electrical work ranked by build risk

The order below favours faults that can corrupt memory or prevent reliable startup, followed by shared-interface uncertainties. Exact identities and stock counts remain prerequisites (`dm02-57n.2.1`, `.2.2`). All proposed fitted logic/memory changes must remain DIP and all other fitted parts through-hole. None of the substitution routes below is an approved part change.

### 1. Reset, brownout and valid supply

The owned MCP100-450D is not a 4.75 V power-good detector. The existing reset model records a 4.25–4.50 V trip interval and 150–700 ms release delay; a delay does not prove that the supply has reached the required voltage. CP1 assumes an externally qualified reset input. See `models.json`, `vendor/reset/mcp100.pdf`, and R2 `physical-review.json`.

Recommend a supervised reset design with a guaranteed lower release threshold above the invalid-supply region after tolerance, rail drop and measurement error, plus oscillator startup delay and immediate write inhibition. Manufacturer clarification can settle the exact grade/suffix but cannot raise its specified threshold. A selected through-hole supervisor or comparator/reference circuit can address the threshold; neither has been selected or qualified. Controlled tests alone would qualify sampled hardware, not establish a new component guarantee.

Minimum fixture: representative C1/ME1 reset and write-inhibit loads, programmable ramp/dip supply, oscilloscope, and rail/reset/write-enable probes at the IC pins. Exercise slow and nonmonotonic ramps, brownout, manual reset during writes and repeated restart. Acceptance requires the downstream write path to remain inhibited until voltage and clock validity are established. Beads: `.3.5`, `.3.8`, `.8.1`, `.8.2`.

### 2. SRAM turnaround and asynchronous hazards

UM61512AK-15 has a 15 ns access bound, 9 ns write pulse and 7 ns write-data overlap in the archived UM61512A tables. Read timing uses 30 pF; release/low-Z tests use 5 pF. Its 8 pF input / 10 pF IO capacitances are sampled maxima at 25 °C, not full-temperature guarantees. See `build/cp1-hct273/sources/um61512a.txt`, PDF pp. 4–5 and 10. The table's AC supply heading differs from its 5 V ±5% DC operating conditions; preserve that distinction rather than broadening the operating envelope.

All eight ME1 RAM nets are allocated 25 pF: within the read-test load, five times the release-test load. They connect U2 DQ, U4 write driver and U5/U7 read-mux inputs. Actual loading and the write driver's disabled capacitance remain unmeasured. Slower cycling cannot eliminate combinational write glitches or simultaneous drive at a local handover.

Recommend a short ME1 fixture and explicit break-before-make/write-inhibit timing before layout. Ask for manufacturer load-dependent release limits if obtainable. Controlled measurement should cover the real DQ load, both read/write directions, address changes, reset and supply/temperature extremes with quantified instrument error. Isolation/buffering changes add delay and input load but can separate the load and driver-control problems. An exact DIP SRAM alternative is a fallback only after comparing pinout, access, release, write constraints and sourcing; a generic “slower SRAM” is not a qualification.

Minimum equipment: programmable pattern source, adjustable supply, temperature control and a scope/probe combination that resolves the 5–15 ns events without materially changing DQ loading. Use a calibrated release fixture and current/voltage observations; output high-Z is not simply a logic threshold crossing. Beads: `.3.4`, `.3.2`, `.8.1`, `.8.2`.

### 3. HCT245 loading and release

For selected SN74HCT245N, TI SCLS020H §6.5 explicitly excludes transceiver IO ports from the 10 pF Ci maximum. The 3 pF typical value is for control inputs and must not be assigned to IO ports. §6.7 bounds data/enable at 150 pF (38/74 ns); §6.6 bounds disable at 50 pF (50 ns). The R2 model conservatively uses 74 ns for data and enable. Its 10 pF per IO-port allocation is an assumption. Sources: `sources/sn74hct245.txt`, PDF pp. 6–8.

R2 has 48 HCT245-driven physical nets. Eight DATA nets are allocated 100–110 pF, driven by BF1 U105; the remaining nets are allocated 40–50 pF. BF1's eight trunk nets are 45 pF. Thus even the allocation-based audit does not justify applying the 50 pF disable bound to U105. U105 is the sole DATA driver, so its issue is release/hold timing rather than competition with a second DATA driver; trunk/source handovers still require contention analysis.

Recommend separate data/enable and disable load budgets, with a measured shared-bus fixture. Manufacturer clarification of maximum IO capacitance and disable behaviour above 50 pF would close the strongest missing specifications. Measurement must include inactive outputs, sockets, connectors, trace and probes, and retain lot/temperature/supply limits. Splitting the final DATA driver into buffered leaf groups reduces load but changes skew and package count. An exact DIP transceiver/buffer substitution is viable only with explicit IO-capacitance and timing evidence; family initials alone are insufficient.

Minimum fixture: ME1 or RG1 source, both BF1 stages, representative inactive source packages and receiver loads; pattern generator, low-capacitance probes, fast scope and a documented capacitance/edge characterisation method. Beads: `.3.2`, `.3.3`, `.2.2`, `.8.1`, `.8.2`.

### 4. HC377 thresholds across the supply range

SN74HC377N's TI SCLS307D §6.2 specifies VIH/VIL at discrete supply points: 3.15/1.35 V at 4.5 V and 4.2/1.8 V at 6 V. The R2 comparison uses the common 4.5 V table point only. It reports a smallest high margin of 0.55 V for the HCT574-driven inputs; this is not a 4.75–5.25 V dynamic noise-margin certificate. See `sources/sn74hc377.txt`, PDF p. 4, and `physical-review.json:hc377_inputs`.

Recommend a per-driver DC and loaded-edge budget using correlated local rail limits and manufacturer-approved threshold interpretation. Do not interpolate the table and call it a guarantee. Manufacturer confirmation is preferable to relying on a typical threshold curve. Measurements of HC377 data, enable and clock inputs can qualify the selected board/lot with a stated noise allowance. Local HCT/AHCT buffering can restore levels but adds delay and load; an exact DIP HCT377 replacement requires its own sourcing, pinout and timing review.

Minimum fixture: each distinct driver family with actual receiver fanout, independently adjustable rail offsets, temperature control, scope and DMM. Beads: `.3.1`, `.3.2`, `.2.2`, `.8.2`.

### 5. Oscillator, distributed clock and transfer window

ACH-4.000MHZ-EK specifies ±30 ppm, 45–55% duty at half supply, 10 ms maximum startup and 15 pF standard load. The receiver-threshold 37–63% duty range and 2/10 ns internal/output uncertainty are allocations, not guaranteed ACH jitter/threshold bounds. The nominal oscillator load leaves only 5 pF beyond the allocated 10 pF AHCT04 input for routing, socket and probes. Source: `targets/cp1/overlay/Verification/clock-parts.json` and its cited Abracon source.

Recommend measuring the exact oscillator into C1's real input load, then the worst DT1/local-clock branches and MA1 U2/U8 transfer window. Ask Abracon for threshold, monotonicity and cycle-jitter limits. A socketed exact through-hole oscillator with explicit limits is a possible substitution; it requires new clock qualification. Buffering must respect the oscillator's initial load and input slew. Lower frequency improves phase windows but leaves input edge quality and asynchronous-entry metastability unresolved.

Minimum fixture: C1, representative DT1 fanout and MA1 transfer chain; low-capacitance probes, multi-channel timing scope, supply ramps, temperature control and controllable request/step timing. Report timing uncertainty before claiming a positive margin. Beads: `.3.6`, `.3.7`, `.3.9`, `.8.1`, `.8.2`.

### 6. HCT273 output load and input edges

The selected CD74HCT273E has explicit SCHS174D bounds at 4.5 V, −40…85 °C, 50 pF and 6 ns test input edges: clock/clear-to-Q 38/40 ns, setup 15 ns and data hold 3 ns. R2 retains 42 ns output delay, 25 ns setup/release separation and 20 ns clear pulse. These are conservative model choices. All 24 output allocations are within 50 pF, but actual loading and source slew are unqualified. Sources: `sources/cd74hct273.txt`, `part-qualification.json` and the selected-model qualification text.

Recommend retaining the R2 part and verifying its actual load, clock/reset edges and 3 ns hold at AL1 U2 and ME1 U11/U15. Manufacturer clarification can address timing with slower input slew; typical plots cannot replace a bound. Controlled measurement with probe skew calibration is the direct first-build route. Buffering can reduce load at the cost of added delay; another DIP register offers little benefit unless a specific unmet bound is identified.

Minimum fixture: populated representative register/ROM or register/IO path, calibrated paired probes, scope, supply and temperature control. Beads: `.3.2`, `.3.9`, `.8.2`.

### 7. ROM capacitance, edges and physical image integrity

M27C322 input/output capacitance maxima are 10/12 pF at 25 °C, sampled rather than 100% tested (Table 6, `vendor/alu/m27c322.txt`). M27C1024 lists 6/12 pF at 25 °C (Table 6, `sources/m27c1024.txt`). W27C512 lists 6/12 pF at 5 V, 25 °C; its 45 ns grade uses 30 pF output load and 5 ns test input edges (`sources/w27c512.txt`, §9–10, p. 9). These are condition-specific maxima, not typical values or full-temperature capacitance guarantees.

Recommend budgeting the actual ROM links and obtaining full-envelope manufacturer limits where possible. Controlled capacitance/edge measurements can qualify owned devices with explicit sample limits. Local address/output buffering reduces individual load but adds delay to the already critical same-word memory path. Exact DIP memory replacement also changes programming, pin mapping and access/release constraints. Preserve the owned ROM choice unless evidence justifies that work.

Minimum fixture: exact ROMs in intended sockets, representative address drivers and output receivers, capacitance/edge instruments and temperature control. Physical programmer/adaptor qualification and independent readback remain separate prerequisites; correct simulated images do not establish correct programmed devices. Beads: `.3.2`, `.2.4`, `.2.5`, `.8.2`.

## Evidence and acceptance boundary

Study outputs are under `build/cp1-readiness/`: `frequency-results.json`, `capture-results.json`, the additional all-opcode receipt, `trace/`, and `timing-screen.json`. Each experiment checks its source HDL/fixtures against the active R2 lock, preserves its inputs and records output hashes. Failed runs remain available alongside passing runs.

Every physical fixture above needs exact part/lot identity, IC-pin voltage, temperature, stimulus, load/probe model, raw traces and measurement uncertainty. Sample measurements must be labelled as sample qualification. Manufacturer clarification, measurement and design changes are different evidence routes; none has been completed by this study. Independent electrical review is still required.

The two release gates remain `dm02-57n.7.5` (fabrication readiness) and `.8.8` (measured working machine). The formal milestone totals remain 3/5, 3/5 and 8/9. Follow-up execution and dependencies live in Beads.

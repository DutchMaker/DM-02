# CP1-RR1 DATA and SRAM release requirements

RR1 traces the MD1 native wiring, checks the instantiated SRAM model and separates the release obligations of DATA, the private SRAM bus and SOURCE3. The result is a reproducible control-path audit, targeted simulations and a per-driver measurement specification. Physical release bounds remain open under `dm02-57n.3.3` and `dm02-57n.3.4`.

The circuit remains MD1, with 272 DIP logic/memory ICs. CP1-R2 remains the accepted digital revision. RR1 adds no hardware or clock change.

## Driver ownership

| Bus | Native drivers per bit | IC-only load per active driver | Relevant timing fixture |
| --- | --- | --- | --- |
| DATA0–3 | BF1 U105, native U10105 | 100 pF | HCT245 enable/data 150 pF; disable 50 pF |
| DATA4–7 | BF1 U105, native U10105 | 90 pF | Same |
| RAM0–7 | ME1 U2 SRAM and U4 write buffer, native U9002/U9004 | 20 pF | SRAM access 30 pF; high/low-Z 5 pF; AHCT244 50 pF |
| SOURCE3 | MA1 U20/U21 and ME1 U9, native U8020/U8021/U9009 | 30 pF | HCT245 disable 50 pF |

These subtotals exclude the active driver's own output capacitance. Inactive outputs count as loads. Socket, routing, contacts and probes remain unknown; several pin-capacitance values are conditional or allocations. The complete per-pin inventories, contact pairs, other outputs and capacitance qualifications are retained in `build/cp1-release/summary.json`.

BF1 U105's DIR pin is tied high. It alone drives DATA; U101–U104 compete on the upstream trunk. A late U105 release therefore has no competing DATA driver to overlap in MD1. The final stage still needs valid enable/data settling before capture, valid data through each receiver's hold interval, and characterized idle/reset behaviour. Its **maximum disable delay cannot establish a minimum data-hold time**. Adding a debugger bus master or another DATA driver would invalidate the sole-driver conclusion.

ME1 U9's OE is physically tied to SRAM U2's OE. During read shutdown, SRAM data can become invalid through the mux while U9 is still active. SOURCE3 exclusivity and downstream hold must therefore be checked independently of the private SRAM-bus handover. The final trace includes U8020/U8021 and BF1 U104 OE paths as well as the ME1 controls.

## Native OE/WE paths

`dm02.release_requirements.Graph` follows physical pins in MD1's checked load inventory. It expands the actual AHCT04/08/00/32 gates and always-enabled AHCT244 buffers. The report includes every input/output pin and conditional delay term; unresolved combinational inputs fail closed. Existing MD1 replay verifies the underlying inventory against the exported native hierarchy first.

At the ME1 command pins, let `R` be active-low read, `W` active-low write and `Z` the locally buffered reset release:

```
SRAM_OE_n = NOT ((NOT R AND W) AND Z)
U4_OE_n   = NOT ((NOT W AND R) AND Z)
SRAM_WE_n = NOT (write_request AND PH2 AND NOT PH3 AND RAM_address)
```

`RAM_address` permits `$4000–$FEFF`. Both CE pins select the SRAM continuously: CE1 is grounded and CE2 tied high. U4's two OE pins share one net. Its output drive follows the write command, while WE is additionally phase/address qualified. In particular, a low WE pulse cannot be relied on to release SRAM before U4 starts driving; OE must already provide the handover.

The static oracle checks **8,192 combinations** of reset, read/write commands, PH2/PH3 and the high address byte. No steady-state combination enables both SRAM and U4. Simultaneous read/write requests inhibit both in the settled truth table; this does not prevent transient overlap when command edges or gate delays differ.

| Endpoint | From read command | From write command | From distributed ME1 reset | From PH2 | From PH3 |
| --- | --- | --- | --- | --- | --- |
| SRAM/U9 OE | 26.5 ns | 18 ns | 18.5 ns | — | — |
| U4 OE | 26.5 ns | 35 ns | 27 ns | — | — |
| SRAM WE | 45 ns | 53.5 ns | 45.5 ns | 27 ns | 26.5 ns |

These are conditional maximum gate-path sums, excluding incoming distribution/route delays and endpoint release. Address-to-WE decode paths are listed separately for buffered address bits 8–15. BF1 U105 OE takes 37–55 ns from individual source-enable leaves, or 18.5 ns from its distributed reset input, under the same gate-delay assumptions.

With zero earliest activation of a new driver, sufficient conditional command-blank intervals are:

- Read to write: **26.5 + 10 = 36.5 ns** from read-command deassertion at ME1.
- Write to read: **35 + 13 = 48 ns** from write-command deassertion at ME1.
- ME1 U9 release before another SOURCE3 driver: **26.5 + 50 = 76.5 ns** from read-command deassertion, with the other source's earliest arrival checked separately.

Routing/skew, measurement uncertainty and positive residual margin must be added. The 10 ns SRAM term is the inherited generic simulation value. The manufacturer's OE-specific limit is 9 ns at its 5 pF fixture. None of these sums establishes a release guarantee for the assembled bus.

## Manufacturer definitions and model audit

The archived UMC UM61512A data sheet specifies the -15 part's OE-to-high-Z maximum as 9 ns, WE-to-high-Z as 8 ns and chip-disable-to-high-Z as 10 ns. Low-Z/high-Z timing uses the 5 pF fixture, including scope and jig, with 480 Ω/255 Ω bias resistors. Access timing uses 30 pF. The notes define high-Z as an open-circuit condition rather than a valid logic voltage; the measurement waveform uses a 500 mV departure from the steady output. These definitions do not justify capacitance-scaled extrapolation.

TI SCLS020H specifies SN74HCT245 disable at 50 pF, with a 50 ns maximum at the selected conservative 4.5 V table point. The separate 150 pF table gives 74 ns enable and 38 ns data propagation maxima, without a 150 pF disable limit. The accepted model uses 74 ns for both data and enable, and 50 ns for release. AHCT244's selected 50 pF enable/disable maximum is 13 ns. Applying any bound requires its supply, temperature, load and input-edge conditions.

The actual SRAM instance is `cp_sram #(15,10,15,12,9,7)` from pinned `support.sv`. The `me_sram` module also present in `ME1.sv` is unused. `cp_sram` has one generic TDIS, rather than distinct OE/WE/CE delays. It drives X immediately on a read request and resolves data after TACC. Generation-token cancellation and address events can restart resolution. This behavioural model is useful for functional checks but provides neither a measured release bound nor a characterized minimum activation time.

RR1 adds an independent drive-activity monitor: SRAM and U4 turn on immediately when requested, then remain active for their chosen release envelopes. It detects simultaneous activity even with identical data, without relying on X detection. The 10/13 ns envelopes are conditional sensitivity assumptions. The 5,000 ns fault changes this monitor's release envelope; it does not alter SRAM cell storage or claim a measured delay.

The earlier `build/sram-turnaround/` study used AS6C1008 and older ME1/FD1 sources. Its method remains informative; its numerical bounds are not imported into MD1's UM61512A audit.

## Targeted results

Four short native-derived control profiles pass read/write captures and reset during read/write: maximum, zero, slow-read/fast-write and fast-read/slow-write. Their fixture inserts explicit blank intervals; the initial transition uses 100 ns and later transitions include longer settling periods. Zero-delay paths are conservative sensitivity cases, not device minimum specifications.

Five short negative cases fail for the expected reason: unblanked read-to-write, unblanked write-to-read, same-data overlap, 200 ns SRAM release with a 100 ns command blank, and premature read capture. Four static inventory/control faults are also rejected: reversed DATA direction, grounded SRAM OE, split writer enables and an extra DATA driver.

Four fresh instrumented MD1 ROM/text boots reconstruct all 160 payload bytes, transmit `TX1\r\n` after HALT and report zero existing timing-monitor violations. Each completes **167 opposing-driver turnovers in each direction**. The minimum requested control-pin gaps are:

| Boot profile | Read to write | Write to read |
| --- | --- | --- |
| Maximum | 4,999.5 ns | 4,947.5 ns |
| Zero sensitivity | 5,000 ns | 5,000 ns |
| Mixed 2 | 4,991.5 ns | 4,955 ns |
| Mixed 3 | 4,981 ns | 4,991 ns |

These observations cover the loader/text workload and sampled profiles. They are not universal instruction/mode budgets. `summary.json` counts changes of opposing ownership once; the archived per-run event summaries also count repeated requests since the last opposing release.

Holding BF1 U105 permanently enabled in one additional boot still passes reconstruction, serial output and existing timing checks. This supports the digital sole-driver reasoning; it is a simulation sensitivity change only. The native OE circuit remains intact. A 5,000 ns SRAM-release envelope triggers an overlap fault on the first write handover, whose requested gap is 4,999.5 ns.

## Measurement specification

`dm02.release_measurements.plan()` emits **48 driver/bit cases**, each with native driver/control/receiver pins, other outputs, load qualifications, stimuli and acceptance equations. The OC1 grid is 4.75/5.0/5.25 V at IC pins and 0/25/50 °C. Every physical load and observed release field remains null.

The procedure first reproduces the manufacturer's measurement network, then measures the actual loaded link separately. It distinguishes cessation of drive from receiver-valid voltage, includes same-data contention/current observations, and requires calibrated probe/fixture loading and inter-channel timing uncertainty. Latest release and earliest activation must be measured separately. Both handover residuals must remain positive after uncertainty; capture setup retains at least 10 ns reserve, and hold/write/pulse residuals must be positive.

Exact part markings/lots, sample coverage, repetitions and the extra guard used to select a sample-qualified bound require independent review. The nine voltage/temperature points alone do not establish continuous-envelope or production-population guarantees. Reset abort, brownout inhibition, halted operation, step/resume and address-boundary hazards remain part of the specified physical tests. No interrupted write is assumed complete.

The Jev workflow skill was unavailable. No advisory result, independent review or physical measurement is claimed.

## Replay and provenance

`iteration-1` preserves the first short-test results and boot compilation errors: the monitor instance initially preceded signal declarations. `iteration-2` contains the corrected fifteen experiments, all event CSVs and exact simulation-source snapshots. `replay-draft-1` preserves the first replay summary before the address and neighbouring SOURCE3 traces were expanded. The final `summary.json` is regenerated from the current audit and original event logs.

The short-model wire declaration is now sorted for deterministic generation. Replay canonicalizes that declaration's ordering in archived experiments while requiring every connection, expression and delay to match. Long boot simulations were not repeated for this formatting change or the expanded static traces.

Restore MD1 and its dependencies through `Backup/README.md`, then RR1's release archive. Normal bounded replay is:

```sh
python3 Verification/run.py --allow-design-failures
```

For a new experiment matrix, use a new output directory:

```sh
PYTHONPATH=Verification python3 -m dm02.release_sim \
  --output Verification/build/release-new
```

`release-evidence.json` pins sources, original boot inputs, generated models, data-sheet excerpts, raw event logs and preserved development runs. Replay regenerates the native audit, short circuits, boot instrumentation, event analysis and measurement plan, checks expected fault signatures and refuses missing dependencies.

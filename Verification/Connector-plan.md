# CP1-CN1 draft connector plan

This pin-planning revision follows the owner-selected [CP1-MC1 geometry](Mechanical-contract.md) and [CP1-IO1 protocol](IO-interface.md). It starts from the locked CP1-R2 native netlists. [Generated contact tables](build/cp1-connectors/pin-tables.md), [machine-readable plan](build/cp1-connectors/pin-plan.json) and [checks](build/cp1-connectors/check.json) are reproducible with:

```sh
PYTHONPATH=Verification python3 -m dm02.connector_plan --output Verification/build/cp1-connectors-replay
```

CN1 is a provisional assignment for schematic development. Fabrication release requires the implemented schematic, exact connector drawings/footprints, current/load/timing budgets and mechanical qualification. Those acceptance gates remain in Beads.

## CPU card boundaries

Each CPU card uses two candidate 96-contact DIN 41612 Type C connectors. Assign contact names `a1` through `c32` by manufacturer identity. A mating-face view is mirrored relative to the opposing connector; identical contact names must mate. Do not copy a visual left-to-right sequence onto the opposite footprint.

For each connector, all 32 row-b contacts are GND. Contacts a1/c1/a32/c32 carry 5 V; a2/c2/a31/c31 are isolated NC coding reserves. Rows a and c, positions 3–30, provide 56 signal positions. This yields 112 signal positions, 64 grounds, eight supply contacts and eight coding reserves per CPU card. Power contacts share the card supply plane; the allocation does not establish allowable card current or guarantee equal current sharing. An unused contact has no connected logic input.

| Card | Existing crossing signals | New signals | Signal positions used |
| --- | ---: | ---: | ---: |
| Control | 71 | 0 | 71/112 |
| Compute | 57 | 0 | 57/112 |
| Counters | 66 | 0 | 66/112 |
| Memory | 92 | 17 | 109/112 |

The generator resolves each old board connector pin through its native local net and the native BP1 pin. The resulting `native_boundary.nets` lists the old connector endpoints and nonconnector component pins, with board-qualified references. This retains the distinction between DATA and source BRANCH buses and between independently buffered clocks/resets. Combining sheets must not merge similarly named local nets. Nets whose endpoints all move onto the same card are listed as internal links; they still require routing on that card.

The memory additions are LIVE_ADDRESS0–15 and IO_READ_VALID. LIVE_ADDRESS taps ME1's actual ADDRESS nets, with buffering/loading to be designed; it does not use ME1 U15's write-address outputs. Full address observation also supports the debugger. The intended read qualification is valid supply/reset, `$FF` page, `MEM_n=0`, and `LOAD_n10=1`. That expression requires hazard and latency analysis before implementation. R2 lacks this exported qualifier. All 17 contacts are marked circuit extensions, not accepted R2 wiring.

CPU slots have different pin functions. They are dedicated positions, not interchangeable peripheral slots. Role-specific positive mechanical coding must prevent a wrong card entering far enough to mate. NC reserves permit contact-loss coding investigation, but exact coding parts and legal positions have not been selected. Silk-screen labels alone are insufficient. The active backplane needs the existing 26 DIP packages plus new bridge/service/power parts; connector space does not prove that placement fits.

## Peripheral positions 5–8

Each peripheral uses one 96-contact connector with the same ground, supply and NC coding pattern. Thirty-six signal contacts carry the following functions; twenty signal-capable contacts remain NC.

| Function | Direction at card | Source or destination | Inactive requirement |
| --- | --- | --- | --- |
| W_ADDR0–7 | Input | Individually buffered registered IO_ADDRESS from R2 | No transaction without W_STROBE |
| W_DATA0–7 | Input | Individually buffered registered IO_DATA | No transaction without W_STROBE |
| W_STROBE | Input | Qualified IO_STROBE write event | Low during reset/supply invalid |
| R_ADDR0–7 | Input | Buffered live MAR low address | Reads have no side effects |
| R_VALID | Input | Qualified live read selection | Low during reset/supply invalid |
| RESET_n | Input | Qualified system reset | Low until valid startup release |
| R_DATA0–7 | Output | Private input byte to central selection | Select defined zero for absent/reset/invalid supply |
| PRESENT_n | Passive strap | Card ties to GND; backplane pull-up to its own supply | High for empty slot |

Every signal net is prefixed with SLOT5, SLOT6, SLOT7 or SLOT8. Outgoing copies are individual buffered branches; private returns are physically separate mux inputs and must never be wired together. PRESENT_n reports installation only, not readiness or supply validity. A fitted unpowered card must not load or back-power the system; presence alone cannot enable that card's return. Exact pull-up, powered-off isolation and input default circuits remain unimplemented. First-machine cards use the common qualified supply and are inserted/removed with all power off.

The address allocation remains IO1: text `$FF00/$FF03/$FF04`, graphics reservations `$FF01/$FF02`, expansion `$FF10–$FFFF`. Physical slot number does not automatically allocate an address. Decode collisions must fail the allocation check. Private returns avoid a shared return-driver collision, but still require mux timing and power-state qualification. The text readiness credit, overrun behaviour and reset rules are unchanged.

## Debugger service banks

SVC_A is a candidate shrouded 2 × 20, 2.54 mm through-hole header; SVC_B is 2 × 25. Exact manufacturer/mating cable parts are unselected. Every even pin is GND; signal/NC positions are odd. They carry no power output. The external debugger has its own supply, with signal-domain isolation required when either side is off.

SVC_A exposes buffered observation copies of DATA0–7, PH0–3 and ACTIVE/READY/HALTED/FETCH0/FETCH1/EXECUTING/PC_ADDRESS_n/ALU_ENABLE. SVC_B exposes buffered live ADDRESS0–15, RESET_n and five request inputs: RESET_REQUEST_n, RUN_REQUEST, HALT_REQUEST, RESUME_REQUEST and STEP_REQUEST. `OBS_` names are computer-to-debugger; `DBG_` names are debugger-to-computer. The request names describe a new command conditioner, not direct aliases onto R2 RUN/RESUME/STEP nets. Inactive reset request is high; the other request inputs are low. Local controls retain authority and work with both service banks disconnected. Qualify pulse capture, debounce/synchronization, request priority and OC1 stop/step/reset behaviour before attaching these inputs to the controller.

The service interface is a 5 V logic-domain planning boundary. Buffering, powered-off isolation and external 3.3 V translation must be implemented and checked before connection to ESP32 pins. Firmware polling cannot establish full-speed capture fidelity; capture timing, skew, probe capacitance and overflow detection belong to the debugger design. No numeric maximum cable length or supported capture rate is qualified yet.

## Connector candidates and layout references

Manufacturer product pages identify these candidates:

| Role | Part | Manufacturer description |
| --- | --- | --- |
| Vertical CPU/peripheral card | [09031966921](https://www.harting.com/en-DE/p/DIN-Signal-C096MS-30C1-2-09031966921) | Type C 96-contact angled male, wave solder |
| Horizontal backplane | [09032966824](https://www.harting.com/en-DE/p/DIN-Signal-C096FS-29C1-2-09032966824) | Type C 96-contact straight female, 2.9 mm termination, wave solder |

Both pages specify 2.54 mm contact spacing, up to 90 N insertion and 60 N withdrawal, at least 400 mating cycles, no hot plugging, contact resistance at most 20 mΩ and 2 A rated current **at 20 °C subject to derating**. These are catalog limits, not an assembled-machine current or force qualification. Two connectors imply a 180 N insertion-force planning bound per CPU card; provide guides, extraction assistance and backplane supports for assessment. The female 09032966821 is a wire-wrap variant and is not the solder candidate.

Individual drawing downloads were blocked or timed out. The [manufacturer DIN catalog](https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf) was subsequently retrieved through the installed KiCad footprint reference. PDF pages 48–51 (printed 01.20–01.23) list the exact candidate numbers and Type C drawings. The preserved catalog SHA-256 is `46280e3eedb9f76a61cbcc40c5bdff2652cb20bd4a89161bde1d3f630865fb41`.

The [footprint screen](build/cp1-connectors/footprint-screen.json) compares archived KiCad footprints with the visually read catalog dimensions. Both 96-contact grids use 2.54 mm spacing and 1.0 mm nominal holes, within the drawing's 1.0 ± 0.1 mm specification. Mounting-hole spacing differs: **88.9 mm male, 90.0 mm female**. KiCad's 2.85 mm mounting-hole nominals fall within the drawing's 2.8–2.9 mm range; fabrication must meet that finished-hole tolerance. The screen checks the row offset of each mounting pair as well as its spacing. Catalog body-length maxima are 94 mm male and 95 mm female.

This nominal-grid screen is not a mated-assembly fit check. Current manufacturer drawing revision, contact-number orientation through the 3D assembly, housing/flange clearances, tail protrusion at 1.6 mm board thickness, solder access and legal coding components still require reconciliation and physical confirmation. Exact footprint release remains open under `.2.3`/`.6.3`.

The coordinate screen uses the backplane top view with card planes at y=30,60,…,240 mm and card x-extents 10–260 mm. CPU connector centres are provisionally x=65 and 185 mm; peripheral connector centre x=65 mm. A **100 mm body-length allowance**, larger than the catalog bodies, leaves 20 mm between reserved CPU connector zones and 5 mm to each card side. These centres are planning datums, not pad origins or drill locations. Guides, flanges, active-backplane parts, service access and routing can still require revision within MC1 or an updated mechanical decision.

## Qualification ownership

`dm02-57n.4.1.2` covers this contact-allocation study. Parent `.4.1` retains the physical connector contract and implemented bridge; `.2.3` owns exact mating hardware/footprints; `.3.2` owns load, stub/route and edge limits; `.3.8` owns current/voltage/protection; `.3.9` owns complete timing; `.4.3` owns the debugger; `.6.3` owns mechanical qualification. The package rules apply to all added computer-side circuitry.

Apply OC1's ≥10 ns setup reserve and positive hold/release margin to the actual MAR-to-card-to-mux-to-ME1-to-BF1 path, including address changes within the microcycle. All eight positions, empty/populated combinations, connector insertion forces and powered-off endpoints need their specified acceptance evidence. Contact-allocation checks do not close those gates.

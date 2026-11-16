# CP1-BR1 I/O bridge candidate

BR1 implements the next circuit-level step after the [CN1 pin plan](Connector-plan.md). Its schematics are in `Circuits/KiCad/IO-Bridge/candidates/`. The accepted computer remains **CP1-R2**. This candidate has not been connected to the full CPU model or built on hardware.

## Circuit boundaries

MQ1 belongs on the selected memory card. Two CD74HCT244E buffers export the live 16-bit MAR address. A balanced gate tree forms IO_READ_VALID from the `$FF` page, active MEM_n, inactive LOAD_n10 and qualified reset release. The original registered IO_ADDRESS remains the write-address source. Each MAR bit acquires one additional HCT input; the complete existing MAR load must be rebudgeted before integration.

The explicit native binding audit maps MQ1 MEM_n to ME1 J1.7 (`MEM_out_n`) and LOAD_n10 to ME1 J1.8 (`MEM_load_n`). MQ1 uses the distributed **ME1_RESET_n** at ME1 J1.6, locally named `RESET_n`; BR1 uses the separate C1 reset root at J90.4 (`RESET_RELEASE_n`). These reset nets must remain separate. The testbench samples a 70 ns memory-reset branch delay; this does not qualify distribution skew. Live ADDRESS0–15 are tapped at ME1 J3.3–18 and traced to MA1. The audit checks all 17 CN1 extensions and 384 peripheral connector contacts against the native candidate.

BR1 belongs on the active backplane. It provides separate buffered write-address, write-data and live-read-address branches for all four peripheral positions. DIN contact names follow CN1. Connector symbols use the selected female-footprint candidate; exact mating, coding and mechanical release remain open. The generic headers marked `INTERNAL_BOUNDARY_NOT_FITTED` describe net joins between logical sheets/R2, not extra fitted production connectors.

Two CD74HCT154E decoders recognize exact low-byte addresses. Four CD74HCT153E dual multiplexers select the eight-bit private return. Their disable inputs force a driven zero, rather than leaving ME1's IO_INPUT floating. The present strap masks an absent slot. A 10 kΩ pull-up defines each empty PRESENT_n; 100 kΩ pull-downs define disconnected return inputs.

| Address | Position | Candidate purpose |
| --- | --- | --- |
| `$FF03` | 5 | Text status return |
| `$FF10` | 6 | Independently addressed qualification fixture |
| `$FF20` | 7 | Independently addressed qualification fixture |
| `$FF30` | 8 | Independently addressed qualification fixture |

The last three are **fixture allocations**, not installed production peripherals or a new general-purpose software ABI. Writes remain independently addressed and are forwarded to each card; the endpoint decodes W_ADDR itself. `$FF00` text writes and `$FF01/$FF02` graphics reservations retain IO1 semantics. Other reads return zero. Supporting more readable registers on a future card requires an updated route decoder and affected verification.

## Reset-safe writes

A NAND SR latch clears ARMED when reset is asserted. It can set ARMED only while the incoming registered IO_STROBE is low. WRITE_EVENT requires ARMED, raw IO_STROBE and qualified reset release. This prevents releasing reset during an already-high raw strobe from producing a new rising write edge. Assertion during a strobe aborts it; the peripheral's reset must clear any interrupted transaction.

The simulation checks reset release while the raw strobe is high, reset assertion during a strobe, a second release with no new raw edge and normal subsequent writes. It deliberately bypasses the arming condition in one mutation; that circuit produces an unwanted write and fails the test. Reset/strobe recovery near coincident edges, minimum pulse widths and distribution skew still require timing qualification. The circuit depends on the OC1 qualified reset source, whose physical supply supervisor remains separate work.

## Evidence and model limits

The candidate generator emits ordinary KiCad symbols and explicit physical pins. KiCad independently imports the legacy libraries and exports native netlists; all pin groups are compared with the source connectivity. The HDL compiler then reads those native netlists and models devices from physical pin numbers. It does not implement the intended bridge as a behavioral address-map function.

The independent testbench scans the full 65,536-address space, every low-byte address for all 16 presence combinations, walking bits on all 32 private-return wires, read/write qualification, empty-slot defaults, reset/abort behaviour and 256 separately addressed write events. Each profile checks 70,020 read cases. Four profiles use zero, maximum and two alternating zero/maximum arc-delay assignments. They exercise particular delay assignments; they do not exhaust all possible delay combinations or establish analog hazard immunity. Targeted reset/write waveforms are retained without dumping the entire address scan.

Four mutations must fail: decoding reads from the stale write address, aliasing a private return to the wrong slot, bypassing write arming and bypassing the high-byte IO page qualification. The fixtures supply return data at the peripheral pins. They implement neither the real text mailbox/serializer nor the physical display.

## Parts, loading and timing

`bridge-parts.json` pins exact TI DIP candidates and their downloaded manufacturer sources. Ownership is unknown; these part numbers are candidate choices, not inventory assertions or substitutions for the reported SN74HCT stock. The devices are CD74HCT00E/04E/08E/32E/153E/154E/244E. All other fitted components are through-hole. Each IC has a 100 nF decoupler; placement, capacitor selection and supply integrity still require review.

The first 40-DIP iteration passed its digital tests but exceeded the internal 50 pF screening condition on reset and read-valid. It is preserved under `build/cp1-bridge/iterations/01-load-overages/`. The revised candidate adds reset branches and splits read-valid fanout. It uses **41 additional DIP packages**, excluding the future text endpoint, debugger and supply supervisor. The active-backplane and memory-card area screens must include these additions before layout acceptance.

The intermediate common-reset fixture is preserved under `iterations/02-common-reset-fixture/`. The final binding uses the existing memory reset branch, so it adds no eighteenth memory-card crossing. MQ1 contributes six DIP packages and BR1 35. The prospective R2-plus-bridge total is 233 before further endpoints and reset/service circuitry, subject to integration accounting.

The load screen sums maximum IC input capacitances and a **5 pF planning allowance per connected net**. That allowance is not a measured trace or connector capacitance. Slot-side receiver loads, real route lengths and R2's existing loads need complete budgets. The static logic-path report sums manufacturer maxima at 4.5 V, −40 to 85 °C, 50 pF and 6 ns input edges. Actual HCT output edges do not establish that 6 ns test condition; the sums remain conditional. Unspecified minimum delays use zero. No positive hold margin is inferred.

A complete read budget must include R2's MAR arrival, forwarding to the peripheral, endpoint response, private return/mux, ME1, BF1 and destination setup. The candidate's internal delay sums omit endpoint response and the downstream CPU path. A lower clock alone cannot prove hold, release or reset safety.

Conditional internal table sums are 379 ns to IO_INPUT0, 93 ns to a slot read-address bit, 279 ns to slot R_VALID and 124 ns to slot RESET_n. These figures are not complete OC1 timing margins.

All candidate circuitry uses a common qualified 5 V rail and power-off insertion. PRESENT_n reports physical installation only. The selected HCT parts have clamp paths; this design **does not qualify separately powered or unpowered cards, back-power protection or hot plug**. Debugger level translation and isolation are not implemented here. Parent `.4.1`, `.2.3`, `.3.2`, `.3.8`, `.3.9`, `.4.2`, `.4.3` and `.6.3` retain those acceptance obligations.

## Reproduction

Restore the bridge release and the R2/reference/readiness dependencies described in `Backup/README.md`. The active bounded replay verifies the bridge candidate's pinned evidence separately from R2. For a new engineering run, preserve the publication and generate into a new build directory:

```sh
PYTHONPATH=Verification python3 -m designs.io_bridge_candidate
PYTHONPATH=Verification python3 -m dm02.io_bridge --output Verification/build/cp1-bridge-replay
```

`bridge-evidence.json` pins source and evidence hashes. Changes require a new candidate run and a new reviewed evidence snapshot; changing that file does not promote the bridge into R2 or close a physical gate.

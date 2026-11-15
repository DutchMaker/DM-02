# Fetch and sequencer candidate SQ1

`Circuits/KiCad/Controller/candidates/Sequencer.sch` adds instruction fetch,
an eight-bit instruction register, a four-bit microcode t-state counter and
HALT arbitration to C1, CW1 and PC1. Its pin-derived simulation executes a
continuous program without host assignments to opcode or t-state.

Memory, MAR, stack, general registers and ALU are behavioral test partners.
They respond to decoded pins and generate bus data and live flags. Physical
integration of these partners remains part of MOD-08; the milestone gate is open.
The additional [AL1 integration](./Timed-ALU.md) replaces the A/ALU/flag partner
with a pin-derived timed candidate and adds fetched coverage of all 227 opcodes.

## Sequence and phase contract

SQ1 has three modes: fetch address (`00`), fetch opcode (`01`) and execute
(`10`). Reset selects fetch address. C1's first cycle can precede CW1's first
word capture, so CW1 VALID qualifies both fetch controls and state advancement.
That initial invalid cycle produces no operation.

| Phase event | SQ1 operation |
| --- | --- |
| PH2 rises | Enable fetch controls or pass PH2 to CW1 for execution |
| PH3 rises | Receivers capture; U1 retains the next mode and execution-continuation decision; U5 retains HALT |
| PH0 rises (PH2 falls) | U2 publishes the next state; U4 advances or clears the ROM t-state |
| PH1 rises | U3 latches the mode for the next control window; CW1 captures its ROM word |

The PH0 update gives the ROM address nominally 375 ns to settle before PH1.
The separate PH1 mode register prevents the PH0 state change from selecting
fetch controls while the previous PH2 decoder outputs are still turning off.
End and HALT are sampled on PH3 while CW1's function outputs remain asserted.

Fetch address enables PC1's address output. Fetch opcode enables the memory
data output, selects that data at the instruction-register mux and increments
PC1 on PH3. Execution starts at ROM t-state zero. During execution, an end or
HALT control returns to fetch address and clears t-state; otherwise t-state
increments. Unassigned microcode still has no defined fail-stop policy.

U6 is an HCT574 clocked on every PH3 through U7. A NAND feedback mux holds the
opcode outside fetch opcode, avoiding a gated instruction-register clock.
Its power-up contents can be unknown; reset/validity and fetch mode prevent
those contents from enabling execution before a real opcode has been captured.

## HALT, resume and step

U5 holds HALT after CW1's PH2 window closes. The request to C1 is `RUN AND
NOT HALTED`; C1 finishes the current cycle and stops with PH2 and PH3 low.
Keeping RUN high does not clear HALT.

RESUME asynchronously clears U5. It is an idle-only, debounced input requiring
a recovery guard before the next PH3 edge. It does not reset the sequencer or
PC. The tests use a 300 ns pulse while C1 is stopped. A physical front-panel
implementation must establish pulse width, recovery/removal and debounce.

STEP connects directly to C1's existing pending-step input. It advances one
complete microcycle while HALT remains set. Holding STEP high must not repeat
the cycle. To resume continuous execution, assert RESUME with RUN high. A
single step is a microcycle, not a whole instruction.

System reset aborts C1 and clears mode, t-state, decision staging and HALT.
CW1 and PC1 inhibit their outputs during reset. Supply qualification and
receiver reset recovery/removal still require the system reset design.

## Connectors

| Connector | Pin mapping |
| --- | --- |
| J1 | 1: 5 V; 2: GND; 3–6: PH0–PH3; 7: reset_n; 8: RUN; 9: RESUME; 10: CW1 VALID; 11: TSTATE_reset; 12: CLOCK_halt; 13: CW1 PC_inc; 14: CW1 PC address enable_n; 15: CW1 MEM output_n |
| J2 | 1–2: supply; 3–10: DATA0–DATA7 |
| J3 | 1–2: supply; 3–6: t-state bits 0–3; 7–14: opcode bits 0–7 |
| J4 | 1–2: supply; 3: CW1 PH2; 4: C1 RUN request; 5: HALTED; 6: fetch-address window; 7: fetch-opcode window; 8: latched execute mode; 9: combined PC_inc; 10: combined PC address enable_n; 11: combined MEM output_n |

J3 drives the opcode/t-state positions on CW1 J2. Live C/O/Z/N enter CW1
directly. CW1's operand outputs/loads and remaining functions retain their
existing connections. SQ1 substitutes only the combined PC increment,
PC address enable and memory output enable.

## Evidence

`Verification/dm02/sequencer.py` reads the KiCad sheet and emits device instances
from its pins. The generator is separate. Native KiCad import agrees on 132
pin groups and 392 physical pins, including unconnected outputs; the structural
audit finds no missing supplies, floating inputs or package conflicts.

Six delay profiles execute 264 fetched instructions and 1,424 microcycles
each. The program includes:

* All 16 packed flag combinations, loaded through PUSH/POP F, and 128 conditional
  branches covering each condition both taken and not taken.
* ALU-generated signed overflow feeding a following conditional jump.
* A fourteen-t-state indirect word load, memory read/write and nested CALL/RET.
* Three HALTs, explicit resume, a held STEP while HALTED and PC wrap at FFFF.
* A reset during an active cycle, followed by thirteen held-button step requests:
  the initial invalid cycle and twelve checked fetch/execution cycles.

Every instruction's expected result is also checked against the independent
instruction-level contract. The HDL compares fetch mode, opcode, ROM t-state,
latched word, PC, bus values, flags, stack pointer, MAR and general registers.
The expected trace is used only by the checker; peripheral data comes from
the actual control pins and modeled state. Continuous selector-overlap checks
cover fetch-to-execute handover, and IR connector setup/hold are monitored.

Ten pin mutations remove or corrupt end sampling, counter clearing, mode
publication, IR data, the upper t-state bit, startup validity, fetch increment,
HALT retention and HALT request gating. Each must produce a functional failure
before the watchdog. Existing device monitors also check register/counter timing.

## Timing and electrical boundaries

`Verification/sequencer-parts.json` names the exact device candidates and
reuses the archived CW1/PC1 manufacturer timing sources. The conditional
PH3-decision-to-PH0 margin is 43.59 ns, and the t-state-publication-to-ROM
setup margin is 98.76 ns. The IR interface requires data stable 60 ns before
and 25 ns after raw PH3. These allocations leave 7 ns setup and 10.5 ns hold
margin through the mux and clock buffer.

Local loads include 5 pF routing and 20 pF external output allocation, except
PC_inc, which reserves 45 pF externally. Buffer branches limit IR mux-select
fanout. These allocations must be replaced by extracted and measured loads.
SQ1 adds another input to DATA; PC1's existing shared-bus load finding remains
open, including inactive-driver capacitance.

The behavioral MAR transfers an address 60 ns after its control asserts, before
same-word memory sampling. This is required by existing words that combine
PC-to-MAR transfer and MEM output/load. The first attempted 40 ns test-partner
delay sampled a released PC address bus at the maximum-delay corner: SQ1 and
PC1's enable path can take 40.5 ns from fetch-address assertion. The 60 ns
partner is an explicit test boundary, not a physical MAR implementation or
qualification. MAR capture and memory timing need their own schematic-derived
path analysis.

The partner's data settles in 150 ns; memory is a flat writable array. Its
FFFF opcode is a counter-wrap probe, not a claim that the physical IO region
contains program ROM. Physical memory decode, IO, ALU/flag timing and global
arbitration are outside this evidence. HALT timing assumes bounded propagation
through C1's synchronizer; metastability MTBF, input slew, jitter, supply and
front-panel qualification remain open.

# Timed general registers RG1

`Circuits/KiCad/Registers-StackPointer/candidates/General-Registers.sch` implements
B, C, H and L. Each byte uses two resettable AC175 registers, two AHCT157
feedback muxes and an AHCT244 DATA output. PH3 captures selected inputs; reset
clears all four registers and inhibits every output even if an output command
remains asserted.

One always-enabled AHCT244 buffers incoming DATA for all four register banks.
Each buffered bit drives four 10 pF mux inputs plus a 5 pF routing allocation.
The resulting 45 pF internal budget fits the retained 50 pF timing-table load.
RG1 adds one 10 pF input per shared DATA bit, rather than four mux inputs.

The PH3 input drives one clock-buffer input. Its output feeds four buffered
branches, one per byte; each branch clocks two AC175 packages. Clock-tree
maximum skew is included in the 40 ns incoming DATA hold contract. The DATA
setup contract is also 40 ns: input buffer, mux, register setup and routing
allowance total 33.5 ns. These leave conditional margins of 9 ns hold and
6.5 ns setup. Reset distribution and the combined C1 fanout need qualification.

## Connections and execution

J1 pins 1–4 are 5 V, GND, PH3 and active-low reset. Pins 5–8 are active-low
B/C/H/L load commands; pins 9–12 are the matching output commands. J2 pins
1–2 are supply and pins 3–10 are DATA0–7. CW1 operands 2–5 select B/C/H/L.

The fetched bench's `HARD_REGISTERS=1` configuration uses RG1's storage and
outputs directly. Together with AL1, all A/B/C/H/L and C/O/Z/N state comes from
pin-derived timed circuitry. MAR, stack, memory and IO remain behavioral
partners, so MOD-08 remains open.

`Verification/dm02/register_hardware.py` runs twelve profiles:

* Three standalone profiles each cover 2,048 byte-sweep loads, 4,096 transfers
  between all source/destination pairs, including self-transfers, and four
  additional reset-preparation loads. The reset checks hold raw commands active
  while asserting reset. Every operation checks all four stored bytes.
* Six continuous fetched profiles use the existing 264-instruction,
  1,424-cycle program with branches, nested calls, HALT/resume, STEP and PC wrap.
* Three all-opcode profiles each fetch 227 target opcodes with two flag patterns:
  454 cases, 4,992 instructions and 23,002 cycles. The instruction oracle and
  microcycle traces are the same independent checks used for AL1.

Fetched RG1 runs monitor the 40 ns DATA setup and hold contract at the connector
for every B/C/H/L load, in addition to the device-level timing monitors.

Eight pin mutations cover input routing, load selection, clock routing, hold
feedback, high data bits, output selection, missing reset and reset/output
inhibition. Native KiCad migration compares 152 pin groups / 506 pins. Device
parameters and manufacturer excerpts are retained with the stage evidence.

## Combined DATA load

`build/register-hardware/bus-load.json` follows the connected DATA pins on
AL1, PC1, SQ1 and RG1. It sums each receiver's retained maximum input-capacitance
entry exactly once, without adding the individual boards' external-load
allocations:

| Candidate | DATA0–3 input budget | DATA4–7 input budget | Output pins per bit |
| --- | ---: | ---: | ---: |
| AL1 | 30 pF | 20 pF | 3 |
| PC1 | 20 pF | 20 pF | 2 |
| SQ1 | 10 pF | 10 pF | 0 |
| RG1 | 10 pF | 10 pF | 4 |
| Total | 70 pF | 60 pF | 9 |

These are worst-case input budgets, not measured minimum capacitances. Routing,
inactive output capacitance and the MAR/stack/memory/IO receivers are additional.
All eight input budgets exceed the 50 pF condition used by the selected bus
drivers' timing tables. The digital delay profiles therefore provide conditional
functional evidence; they cannot close the electrical timing gates.

The load audit records exact candidate/reference/pin endpoints so a buffered or
segmented bus redesign can be checked against the same accounting. The next
integration work includes MAR's early address transfer and stack/memory/IO
timing. A PH3-only MAR capture would miss same-word memory reads: the current
60 ns behavioral transfer is an unresolved physical implementation requirement.

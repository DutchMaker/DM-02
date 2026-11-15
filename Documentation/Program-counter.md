# Program-counter candidate PC1

The candidate is in `Circuits/KiCad/Registers-StackPointer/candidates/Program-Counter.sch`.
`Verification/designs/pc_candidate.py --write` regenerates the drawing; verification
reads the resulting schematic and derives connections from its physical pins.
It remains separate from the active register/stack sheet.

## Circuit and interface

Four CD74HCT161M96 counters store the 16-bit PC. Each counter's CET input is
high, so TC reports that nibble's terminal count independently of PC_inc.
Two AND gates form the lower-two and lower-three nibble prefix carries.
U11 captures those prefixes and the lowest nibble's TC on PH3's falling edge.
The following rising edge counts through CEP, gated by PC_inc. The lowest
nibble uses PC_inc directly.

Staging keeps the carry enables stable around the count edge without assuming
a guaranteed minimum HCT161 propagation delay. U9 buffers the counter clock
and the separate inverted staging-clock branch. All four counter clocks share
one buffer output. Clock distribution and routing skew still need a PCB check.

Low- and high-byte parallel loads are independently active-low. Load wins
within the selected byte; an increment can still carry into the other byte
from the old terminal count. This preserves the Logisim reference's
`45FF + low-load(67) + increment -> 4667` behaviour. JMP/CALL microcode avoids
that redundant increment.

U5/U6 drive either PC byte onto DATA. U7/U8 drive the full address onto A0–15.
The address enable is independent of the byte enables. U14 inhibits all these
drivers during reset; U10 supplies its active-high reset input. Reset clears
the counters and carry staging asynchronously.

| Connector | Pins | Signals |
| --- | --- | --- |
| J1 | 1–2 | 5 V, GND |
| J1 | 3–5 | PH3, active-low reset, increment |
| J1 | 6–10 | Active-low low-load, high-load, low-output, high-output, address-output |
| J2 | 1–2, 3–10 | 5 V, GND, DATA0–7 |
| J3 | 1–2, 3–18 | 5 V, GND, A0–15 |

## Verification

`Verification/dm02/pc_hardware.py` produces six profiles: ideal and maximum
device delays with an ideal connector clock, then zero, maximum and two mixed
delay assignments driven by the C1 phase output. Each profile exercises:

* All 65,536 increment states, including wraparound.
* 12,288 independently calculated load/control vectors: six boundary PCs,
  every data byte and every increment/byte-load combination.
* 3,632 compiled opcode/flag sequences, totalling 16,992 executed microinstructions.
  The host supplies settled controller inputs and non-PC bus values; PC data
  and address outputs are checked before capture, and PC state after capture.
* Hold, independent byte/address outputs, bus release, opposing byte drivers,
  reset priority and reset inhibition of outputs.
* In C1 profiles, stopped-clock hold and two single steps, including STEP held
  high long enough to detect an unwanted repeated increment.

The fixture uses a 40 ns break-before-make interval and applies controls well
inside the low phase. Those intervals describe the stimulus contract; a
physical controller must generate and meet them. Setup, hold, reset recovery,
counter clock-low duration and reset pulse monitors use explicit procedural
checks. Nine deliberately mistimed inputs must fail with their specific
diagnostics. Seven schematic mutations cover carry routing, same-edge staging,
load/data/address mapping, byte output selection and reset output inhibition.

Native KiCad symbol import independently checks the candidate's pin groups.
The generated native schematic, netlist, fixture files, HDL and simulation
logs are retained under `Verification/build/pc-hardware/` and included in the
dashboard's evidence hashes.

## Timing and loading limits

The HCT161 limits use the 4.5 V, 50 pF, −55 to 125 °C column. Clock-to-Q is
59 ns, clock-to-TC 63 ns and clear propagation 75 ns. The model conservatively
uses 75 ns for both output paths in its maximum-delay profile. Minimum delays
are zero. The carry-stage and gate limits come from the retained TI excerpts.

The budget uses C1's conditional minimum output pulse, buffer/inverter bounds
and a 10 ns PC routing allowance. It separately checks carry preparation,
carry-to-counter setup, opposite-edge enable hold and output disable spacing.
These path inequalities are conditional on their input slew and load limits.

**The allocated DATA load exceeds the timing model's test conditions.** Each
data bit connects to two counter inputs, bounded at 10 pF each, plus a 50 pF
external connector allocation. That already totals 70 pF. The disabled second
bus driver's output capacitance adds more; TI specifies only a typical Co.
The load audit retains this finding rather than reducing the allocation to
make it pass. Bus propagation and OE results at 50 pF are sensitivity evidence,
and the overall PC evidence remains limited. The backplane design must establish
a supported capacitance bound or change the driver/segmentation architecture.

PC-to-MAR capture on the same edge needs a connected hold-time analysis.
Input slew, receiver recovery/removal, full-machine output arbitration,
power-up sequencing and physical controller control-word latching remain open.
The C1 oscillator/duty/frequency sweep is a separate clock test; these PC runs
use nominal 8 MHz, 50% oscillator duty.

## Parts and source records

`Verification/pc-parts.json` records exact logic candidates and model values.
U1–U4 and U11 use SOIC-16 footprints; U12/U13 use SOIC-14. The remaining logic
uses the named DIP footprints, and every IC has a drawn 100 nF decoupler.
TI's retrieved addenda list CD74HCT161E and SN74AHCT08N as NRND, so the candidate
uses the active CD74HCT161M96 and SN74AHCT08DR variants. Passive MPNs, stock and
assembly/footprint release review are outstanding.

Manufacturer excerpts, PDF hashes and excerpt hashes are retained in
`Verification/vendor/pc/`. AC175, AHCT04 and AHCT244 excerpts are shared with
`Verification/vendor/clock/`. This provenance records the values used by the
model; it does not establish measured board performance.

# Control-word candidate CW1

CW1 implements the microcode ROM, 16-bit word latch and field decoders in
`Circuits/KiCad/Controller/candidates/Control-Word.sch`. Its decoded outputs
drive the PC1 candidate in a C1-clocked simulation. Opcode, t-state, flags and
non-PC bus values are supplied by the test host. Fetch logic, the physical
t-state sequencer and HALT arbitration are outside this slice. The separate
[SQ1 candidate](./Sequencer.md) now implements those functions and tests fetched
execution with C1/CW1/PC1 and behavioral peripheral partners.

## Clock and blanking contract

The four phase signals below are the connector signals of the C1 candidate.
Within a repeating 1 µs cycle, take PH2's rising edge as time zero:

| Nominal time | Event |
| ---: | --- |
| −125 ns | PH1 rises; the two HCT574s capture the next ROM word |
| 0 ns | PH2 rises; the decoder window opens |
| 375 ns | PH3 rises; PC1 captures increment/load controls |
| 500 ns | PH2 falls; decoded controls return inactive |
| 875 ns | PH1 rises; capture the following word while outputs are inhibited |

Blanking prevents word-bit skew and decoder propagation from briefly selecting
the wrong bus driver during a word change. U11 combines the reset-cleared VALID
bit, system reset and PH2; U12 inverts that result for the common decoder inhibit.
The word clock is buffered separately. The validity register shares this clock
and captures a constant one after reset. The word registers themselves have
no reset input, so their power-up contents are unknown and must remain masked.

The first C1 cycle after reset can precede a PH1 capture. Its controls remain
inactive. A future sequencer must account for that initial invalid word.
TSTATE_reset and CLOCK_halt are phase-windowed function outputs, so the
sequencer must sample or retain them while PH2 is high. Sampling only after
PH2 has fallen would lose them.

ROM address inputs must settle at least 150 ns before PH1 and remain stable
for 20 ns after it. This is an interface requirement on the unfinished
sequencer and flag sources. The source-based budget includes 70 ns ROM access,
25 ns latch setup, 5 ns hold, clock buffering and routing allowance.

## ROMs, decode and pin contracts

Two AT27C512R-70PU 64K×8 OTP devices implement the architectural 64K×16 ROM.
U1 holds the low byte and U2 the high byte of each little-endian compiler word.
Both CE and OE/VPP are grounded for read operation. Verification splits the
actual compiled ROM and checks that interleaving the two banks reproduces every
byte. `build/controller/fixtures/low.bin` and `high.bin` are the bank images;
programmer/adapter validation remains open.

U3/U4 are SN74HCT574N edge-triggered registers. Four CD74HCT154M96 decoders
implement the two operand fields and two possible function fields:

* Data words enable operand-out and operand-load decoding.
* Function words enable function slot A from bits 14–11.
* Slot B uses bits 4–1 and is suppressed for data words with ALU-format bit 6 set.
* NAND gates merge the active-low function slots into active-high function controls.
* ALU operation bits 5–1 remain available directly from the word latch; ALU_ENABLE
  is qualified by data format, bit 6 and the active decoder window.

Zero operands and unused operand 15 have no connected output. Only functions
1–12 are exported. These wiring choices do not define invalid-opcode fail-stop
behaviour; the compiler's unused ROM words remain zero-filled.

| Connector | Pin mapping |
| --- | --- |
| J1 | 1: 5 V; 2: GND; 3: PH1; 4: PH2; 5: active-low reset; 6: VALID |
| J2 | 1–2: supply; 3–6: C/O/Z/N; 7–10: t-state bits 0–3; 11–18: opcode bits 0–7 |
| J3 | 1–2: supply; 3–16: active-low operand outputs 1–14 |
| J4 | 1–2: supply; 3–16: active-low operand loads 1–14 |
| J5 | 1–2: supply; 3–14: active-high functions 1–12 |
| J6 | 1–2: supply; 3–7: ALU operation bits 0–4; 8: active-low PC address output; 9: ALU_ENABLE |

For PC1, operands 11/12 are the high/low bytes, function 5 is increment and
function 6 enables the PC-to-address path. The low/high data and address outputs
are checked independently before PH3; PC state is checked after capture.

## Verification and remaining limits

`Verification/dm02/controller_hardware.py` derives device connections from
KiCad pins. The drawing helper is not imported by the simulator. Native KiCad
symbol import independently checks the migrated pin groups, and the structural
audit checks power, spare gates and floating inputs.

Two synthetic-ROM profiles visit all 65,536 addresses and all 65,536 possible
word values. They check decoding, word storage, blanking, reset inhibition,
ALU-format suppression and output-selector overlap. An address permutation
exercises high and low address bits throughout the sweep. Each cycle changes
all ROM address bits after capture, including the live flag bits; the latched
word and active outputs must remain unchanged.

Three further profiles replay 3,632 compiled opcode/flag sequences through
CW1 and PC1, totalling 16,992 microinstructions each. C1 supplies the phases;
zero, maximum and mixed device delays are used. The host selects each real
ROM address from the compiled-control trace and supplies other modules' bus
values. It seeds PC through connector load cycles at instruction boundaries.
This checks the control path into the PC while retaining explicit boundaries
around the unfinished machine.

Nine schematic fault injections cover latch phase, a live-flag address pin,
ROM byte routing, load selection, function suppression/merging, blanking,
validity reset and ROM output enable. Four timed stimuli must trigger specific
latch setup, hold, high-pulse and low-pulse diagnostics.

The calculated latch-to-enable margin is 19.79 ns under C1's conditional
edge-spread bound. The separate ROM hold-interface margin is 5.5 ns. Internal
and connector capacitance allocations are checked against the timing-table
loads, with a 45 pF external allocation for PC_inc and 25 pF for other outputs,
plus 5 pF local routing. These are design constraints, not measured loads.
ROM input capacitance is specified at 25 °C only; its external address drivers
need full-envelope qualification.

The ROM model drives unknown data during access and uses a conservative zero
contamination bound, even though the selected ROM specifies 7 ns output hold.
Device minimum delays are otherwise treated as zero. Input slew, supply/reset
behaviour, PCB parasitics and global bus arbitration remain unqualified.
PC1's allocated data-bus load still exceeds its 50 pF timing condition. Connecting
CW1 does not resolve that load or PC-to-MAR same-edge hold.

Exact candidate parts and timing values are in `Verification/controller-parts.json`.
Manufacturer excerpts and source hashes are retained in `Verification/vendor/controller/`,
with shared gate/register sources under `vendor/clock/` and `vendor/pc/`.
The HCT574 timing table explicitly specifies rising-clock setup/hold; the
retrieved AHCT574 table instead labels LE falling-edge timing despite its
edge-triggered functional description, so CW1 uses the HCT part's documented limits.

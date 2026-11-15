# Timed ALU candidate AL1

`Circuits/KiCad/ALU/candidates/Timed-ALU.sch` implements A, the ALU operand and
operation registers, ROM lookup, result isolation, stored flags and A/ALU/F bus
outputs. The C1/SQ1/CW1/PC1 fetched test uses these pins directly; its A and flags
are no longer behavioral variables.

AL1 is a separate candidate. It uses the existing M27C322 architecture for timing
analysis, with the exact legacy part M27C322-100F1. ST's archived datasheet marks
this ROM obsolete. A replacement circuit, programmer validation and sourcing
decision are required before release.

## Result isolation and flag capture

The baseline shares PH3 between A and flag storage. Loading A from the ALU can
change the ROM address while flags are being captured. AL1 inserts two HCT574
registers on PH1, half a cycle before the following PH3:

1. PH3 captures a new operand and operation in U6/U7.
2. The ROM settles from its registered A/B/function address.
3. PH1 captures the result and its C/O/Z/N bits in U8/U9.
4. PH2 enables the selected output through CW1.
5. PH3 can load A and flags together from that fixed result.

A changing A register cannot alter the captured result until the next PH1.
The raw ROM model deliberately assumes zero contamination delay and drives
unknown data during access. A mutation that feeds a raw ROM flag around the
snapshot registers must fail.

A uses two resettable AC175 registers with AHCT157 feedback muxes. B and the
five operation bits use HCT377 clock enables. A and C/O/Z/N reset to zero;
B/function/result have unknown power-up contents and initialize through a
normal operand capture before ALU output is requested.

Flags use one resettable AC175 and two AHCT157 muxes. Hold/command data feeds
the first mux, the captured ALU flags override it while ALU output is selected,
and an F load overrides both. C/Z set/clear commands take effect synchronously
on PH3. Packed F exposes C/O/Z/N in bits 0–3 and drives bits 4–7 low. F loads
discard the upper nibble. Clear wins if a contradictory set/clear pair is
asserted; compiled instructions do not request that combination.

SN74AHCT157N replaces the initially evaluated HCT157 mux. Its retained 12 ns
bound leaves more time for incoming memory data than the HCT part's 44 ns bound.
The AC clock branches use a common root buffer with separately buffered A,
operand and flag branches. Every bus output is inhibited by system reset.

## Interfaces

| Connector | Pin mapping |
| --- | --- |
| J1 | 1: 5 V; 2: GND; 3: PH1; 4: PH3; 5: reset_n; 6: A_load_n; 7: ALU_load_n; 8: F_load_n; 9: A_out_n; 10: ALU_out_n; 11: F_out_n; 12–15: SET_C, SET_Z, CLEAR_C, CLEAR_Z |
| J2 | 1–2: supply; 3–10: DATA0–DATA7 |
| J3 | 1–2: supply; 3–7: operation bits 0–4; 8–11: C/O/Z/N |

CW1 operand numbers 1, 6 and 7 control A, ALU and F. Functions 10, 9, 12 and 11
provide the respective flag commands. AL1 J3 flags drive CW1's live flag ROM
address bits. Other register, memory, MAR, stack and IO interfaces remain
separate work.

## Verification

`Verification/dm02/alu_hardware.py` generates HDL from KiCad pin nets. The drawing
generator is not imported by the simulator. Native KiCad migration agrees on
148 pin groups / 462 pins, and the structural audit has no findings.

The eleven profiles comprise:

* Two standalone sweeps, each with 8,192 operand/function vectors, 256 packed-F
  round trips and 64 synchronous flag commands. Every arithmetic vector checks
  simultaneous A and flag capture, followed by flag hold after A feeds back.
* Six continuous fetched programs, each with 264 instructions / 1,424 cycles,
  all 16 flag combinations, 128 conditional branches, ALU overflow, nested calls,
  reset, HALT/resume, held STEP and PC wrap.
* Three all-opcode profiles. Each initializes state through software and fetches
  every one of the 227 target opcodes with flags 0 and 15: 454 cases, 4,992 total
  instructions and 23,002 cycles. Expected state is checked independently at
  instruction level as well as at each microcycle.

The instruction trace is a checker input. It does not supply opcode, t-state,
A, flags or bus operands. Pin-derived C1/SQ1/CW1/PC1/AL1 drive those paths.
The remaining behavioral peripherals respond to actual decoded controls.
The additional [RG1 stage](./General-registers.md) replaces B/C/H/L with timed
pin-derived storage and audits the combined DATA receiver load.
Flat patterned memory and explicit stack/pointer fixtures are used in the
all-opcode suite; physical memory protection and IO behavior are excluded.

Nine wiring faults cover the snapshot clock/bypass, A feedback/reset, ROM
address, function input, flag ordering, upper F bits and output enable. Six
timing stimuli exercise HCT377 data setup/hold, enable setup/hold and clock
high/low pulse monitors. The startup-reset mutation initially escaped because
the first A load hid its unknown state; the test now checks reset state before
any load. Timeout diagnostics and source hashes are retained.

## Functional acceptance and remaining limits

MOD-03 asks whether compiled control execution agrees with the instruction
contract under reviewed phase and flag-capture semantics. The original 130,752
bounded cases are now supplemented by fetched execution of all 227 opcodes
through the circuit-derived controller, PC, A and flag paths. The accepted
contract uses PH1 control/result capture, PH3 receiver/flag capture and
pre-increment MAR address transfer.

The runner closes MOD-03 only when both this integration evidence and the
original control audit succeed, the regression harness passes and the run has
no tool/source/artifact errors. It records the supporting evidence under the
control check's `contract_validation`. The check's overall hardware status
stays limited. MOD-08 still requires complete schematic-derived timed peripheral
integration, and SYS-01 still requires a complete schematic-derived machine.
The acceptance requirement text and milestone definitions are unchanged.

Conditional timing margins include 257.25 ns from operand capture to result
snapshot, 28.79 ns from snapshot to the next output window and 277.05 ns from
stored flags to CW1's next ROM setup window. The incoming DATA contract reserves
40 ns setup and 40 ns hold, including mux, clock-branch and routing allowances.

Shared DATA is already 75 pF on the upper bits and 85 pF on the lower bits under
the allocated external load, before inactive-driver capacitance. This exceeds
the drivers' 50 pF timing-table load. Simulations at those table delays therefore
remain conditional. Internal allocations pass, but ROM input capacitance is
specified only at 25 °C; PCB parasitics, slew, supply/reset and global bus
handover require qualification. Exact parts and retained manufacturer sources
are listed in `Verification/alu-parts.json` and `Verification/vendor/alu/`.

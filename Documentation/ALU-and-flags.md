# The ALU and the Flags register

*This documentation is still in progress...*



### ALU

- Five bits select the ALU function.
- U5 captures operand A from DATA when `~A_load` is low at rising `CLOCK_PH3`.
- U6 and U7 capture operand B and the function when `~ALU_load` is low at that same clock edge.
- The ROM computes its result from these captured inputs. There is no separate result latch in this circuit.
- A later microstep asserts `~ALU_out` to drive the result onto DATA. Stored flags capture the ROM flags at rising `CLOCK_PH3` during that output microstep.

## Functions

| Function          | Microcode expression | Bits    |
| ----------------- | -------------------- | ------- |
| 0                 | ALU_ZERO             | `00000` |
| A                 | ALU_A                | `00001` |
| B                 | ALU_B                | `00010` |
| -A                | ALU_-A               | `00011` |
| -B                | ALU_-B               | `00100` |
| A+1               | ALU_A+1              | `00101` |
| B+1               | ALU_B+1              | `00110` |
| A-1               | ALU_A-1              | `00111` |
| B-1               | ALU_B-1              | `01000` |
| A+B               | ALU_A+B              | `01001` |
| A+B+1             | ALU_A+B+1            | `01010` |
| A-B               | ALU_A-B              | `01011` |
| A-B (special?)    | ALU_A-B_S            | `01100` |
| B-A               | ALU_B-A              | `01101` |
| A-B-1             | ALU_A-B-1            | `01110` |
| B-A-1             | ALU_B-A-1            | `01111` |
| A*B (low bits)    | ALU_A*B_L            | `10000` |
| A*B (high bits)   | ALU_A*B_H            | `10001` |
| A/B               | ALU_A/B              | `10010` |
| A%B               | ALU_A%B              | `10011` |
| A << B            | ALU_A<<B             | `10100` |
| A >> B logical    | ALU_A>>B_L           | `10101` |
| A >> B arithmetic | ALU_A>>B_A           | `10110` |
| A ROL B           | ALU_A_ROL_B          | `10111` |
| A ROR B           | ALU_A_ROR_B          | `11000` |
| A AND B           | ALU_A_AND_B          | `11001` |
| A OR B            | ALU_A_OR_B           | `11010` |
| A XOR B           | ALU_A_XOR_B          | `11011` |
| NOT A             | ALU_NOT_A            | `11100` |
| NOT B             | ALU_NOT_B            | `11101` |
| A+B (BCD)         | ALU_A+B_BCD          | `11110` |
| A-B (BCD)         | ALU_A-B_BCD          | `11111` |



### Flags

- Zero, Carry, Negative, Overflow
- Ability to output/load to/from data bus in order to put flags state on to stack

The circuit's packed F byte uses C, O, Z and N in bits 0, 1, 2 and 3;
bits 4–7 read as zero and are discarded on load. The ROM also produces a
divide-by-zero indicator in output bit 12, but the four-bit flag register does
not store it. The KiCad data-path check and the supplementary Logisim trace
verify this packing. The emulator now uses the same byte representation.
Byte-level emulator/control-ROM checks cover all 256 POP F input values,
PUSH F output bytes and stack-address wrapping; matching PUSH/POP round trips
alone would not detect a shared bit-order error.

All operand and flag storage uses the shared `CLOCK_PH3` net. The flag D inputs
select ROM flags while `~ALU_out` is active, DATA while `~F_load` is active,
or their previous Q values through U14 otherwise. These two load controls must
not be active together. C/Z set and clear controls are qualified by the high
phase; N/O asynchronous controls remain inactive. The old U4 tri-state clock
buffer is disabled and its unused inputs are terminated.

The supplementary Logisim circuit instead clocks flags on `ALU_out` while
enabling their ROM-data buffer with `ALU_load`. The extracted clock cone
reproduces a rising clock with no enabled flag-data source. The KiCad circuit
uses the common-clock/feedback arrangement above to remove that dependency.

Logical checks assume controls settle during the low clock phase and remain
stable through capture. Physical setup/hold, feedback-buffer handover,
asynchronous recovery/removal, reset sequencing and clock generation still
require timing qualification.

Arithmetic results wrap to eight bits. Carry records unsigned carry on addition
and borrow on subtraction; zero and negative describe the wrapped result.
Signed overflow means that the mathematical two's-complement result does not
fit in −128 through 127. Unary arithmetic depends only on its selected operand.

V is defined only for signed arithmetic (ALU opcodes 3–15). Every other ALU
operation clears V, including pass-through, multiplication, division, shifts,
rotates, logic and BCD. The ROM generator and emulator follow this contract;
the exhaustive oracle checks every output bit for all 2,097,152 addresses. See
[`Verification/README.md`](../Verification/README.md) for test scope.

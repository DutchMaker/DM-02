# The ALU and the Flags register

*This documentation is still in progress...*



### ALU

- 5 bits reserved for ALU function selection
- A is always outputting to ALU as operand A
- Any other register may output to ALU as operand B
- The ALU result is latched into a temporary register and may be put out on the bus, but not within the same microtick
- When an ALU function is applied to a data bus operation, the function is set at rising CLOCK1 and the result is stored at rising CLOCK2

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
| A-B (special?)    | ALU_A-Bs             | `01100` |
| B-A               | ALU_B-A              | `01101` |
| A-B-1             | ALU_A-B-1            | `01110` |
| B-A-1             | ALU_B-A-1            | `01111` |
| A*B (high bits)   | ALU_A*B_H            | `10000` |
| A*B (low bits)    | ALU_A*B_L            | `10001` |
| A/B               | ALU_A/B              | `10010` |
| A%B               | ALU_A%B              | `10011` |
| A << B            | ALU_A<<B             | `10100` |
| A >> B arithmetic | ALU_A>>B_A           | `10101` |
| A >> B logical    | ALU_A>>B_L           | `10110` |
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
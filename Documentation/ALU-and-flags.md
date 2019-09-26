# The ALU and the Flags register

*This documentation is still in progress...*



### ALU

- 5 bits reserved for ALU function selection
- A is always outputting to ALU as operand A
- Any other register may output to ALU as operand B
- The ALU result is latched into a temporary register and may be put out on the bus, but not within the same microtick
- When an ALU function is applied to a data bus operation, the function is set at rising CLOCK1 and the result is stored at rising CLOCK2

### Flags

- Zero, Carry, Negative, Overflow
- Ability to output/load to/from data bus in order to put flags state on to stack
# DM-02 Modules

*This documentation is still in progress...*



## Program Counter & Stack Pointer

These two functions share one PCB.

### Program Counter

Built around four 74HCT161 counters. Why different counters than the Stack Pointer? Because a RESET line is required. Also, it does not need to ability to decrement.





## ALU

Changes to the A(ccumulator) register immediately latched into the ALU (A operand).
When ALU_load is high, input for the B operand is loaded from the bus and the result is stored in the A register.
The result is then also latched into the ALU's A operand, within the same clock cycle.

```
# Example microcode for "ADD B"

FETCH: ...
0:     B_out
       ALU_load
       ALU_function=01001
1:     TSTATE_reset
```


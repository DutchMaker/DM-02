# DM-02 Modules

*This documentation is still in progress...*



## Program Counter & Stack Pointer

These two functions share one PCB.

### Program Counter

Built around four 74HCT161 counters. Why different counters than the Stack Pointer? Because a RESET line is required. Also, it does not need to ability to decrement.


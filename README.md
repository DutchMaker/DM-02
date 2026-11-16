# DM-02 8-Bit Computer

_Pronounced: "Dee-Em Zero Two"_

**An 8-bit computer built (almost) entirely out of TTL logic chips**  
This project started in September 2019 and is currently in progress.  
Please refer to the [documentation](./Documentation) for the project status.

The current hardware candidate is **CP1-R2: 192 DIP logic/memory packages**, down from 288. Its [active verification workflow](./Verification/CP1.md) covers all 227 opcodes and ROM boot through graphics output. Physical electrical qualification and PCB review are still open.

Remaining work is tracked in [Beads](./.beads/README.md), with dependencies and acceptance criteria through PCB fabrication and measured hardware qualification. Run `bd bootstrap --yes` on a fresh clone, then `bd ready` to find unblocked work.

**[Start by reading the introduction](./Documentation/)**

If you would like to see the computer in action, the best I can offer you now is the [DM-02 Emulator](https://dutchmaker.com/dm-02/emulator) while the electronic version is under development.

# SP1, MA1 and ME1 candidates

These candidates extend C1/SQ1/CW1/PC1/AL1/RG1 with a stack pointer,
memory address register, ROM, SRAM and registered IO connector. Their KiCad
sheets live under `Circuits/KiCad/Registers-StackPointer/candidates/` and
`Circuits/KiCad/Memory/candidates/`. The verification models use the sheets'
physical pin connections.

## Address timing

SP1 snapshots its 16-bit state on PH1. Four CD74ACT283E adders compute the
next value; AC175 storage captures it on PH3. Increment and decrement cancel
when both are asserted. A byte load overrides arithmetic in that byte.

MA1 snapshots PC and SP on PH1 over dedicated, continuously driven links.
PC1's address-enable input is tied active in this integration. The original
SQ1 address-control output remains checked by the harness.

An early mux path presents a selected snapshot while a transfer command is
active. PH3 stores the resulting address. This allows a control word to
transfer PC to MAR and read memory in the same cycle, while preserving the
pre-increment PC or SP value. PH3-only address capture cannot satisfy that
microcode contract.

`Verification/address-parts.json` retains the ACT283's 18.2 ns maximum at
4.5 V and 50 pF. The manufacturer pin-function table lists VCC incorrectly
as pin 14; its package drawing and the KiCad symbol use pin 16.

## Memory map and writes

| Address | Device or interface |
| --- | --- |
| `0000–3FFF` | AT27C512R-70PU ROM, upper address inputs grounded |
| `4000–FEFF` | AS6C1008-55PCN SRAM, A16 grounded |
| `FF00–FFFF` | External IO input and registered output |

ROM and SRAM have private data nets. Two mux stages select the read source;
one AHCT244 drives CPU DATA. Simultaneous read/write requests blank both
paths. A RAM-select gate protects ROM and IO addresses against SRAM writes.

The SRAM write window begins during PH2 and ends at PH3. CPU DATA remains
driven until PH2 falls. The write connector contract is 60 ns setup and
40 ns hold around PH3; the fetched bench checks both. Reads retain the
receiving board's setup/hold requirements.

IO data and low address byte are captured on PH3. The pending bit qualifies
a PH0 output strobe. The standalone bench checks 40 ns external setup and
hold, one strobe per request, address/data routing and reset inhibition.
External IO reads enter through a separate byte connector.

## Reproducible checks

```sh
python3 Verification/designs/address_candidate.py
python3 Verification/designs/memory_candidate.py
PYTHONPATH=Verification python3 -m unittest discover -s Verification/tests -p 'test_*hardware.py' -v
python3 Verification/run.py
```

The runner publishes `address-hardware/` and `memory-hardware/` evidence:
native KiCad comparisons, structural audits, archived manufacturer excerpts,
load budgets, timing paths and simulator logs.

SP1/MA1 full sweeps cover all 65,536 increments, decrements and early PC
transfers. ME1 full sweeps read every address, write/read all 48,896 SRAM
addresses, attempt writes to all 16,384 ROM addresses and exercise every IO
port. Twelve address-path mutations and twelve memory/IO mutations check
fault detection; four SRAM timing faults require their specific diagnostics.
Each integration has six continuous-program and three all-opcode profiles.
The opcode profiles execute 454 cases covering all 227 assigned opcodes.

`hardware-programs` extends the same bench to the compiled `hello_world` and
`emulator_demo` binaries. Every expected fetch/control cycle is checked, and
the host display receives only the IO connector's observed bytes. Acceptance
requires the exact text, all expected IO events, a matching 48,000-pixel
framebuffer and a stopped clock after HALT.

## Electrical limits

The complete connected DATA receiver budget is 100 pF on bits 0–3 and
90 pF on bits 4–7, before routing and fourteen output-pin capacitances.
These sums use retained maximum input-capacitance values; they are not
measured loads. Driver delays characterised at 50 pF remain conditional.

The SRAM private data nets have a 23 pF numeric allocation. Inactive AHCT
output capacitance is missing, and the SRAM's disable timing is specified
at 5 pF. Its capacitance entries apply at 25 °C. The load report therefore
retains an unqualified turnaround status even when the numeric sum is below
50 pF.

MA1-to-ME1 address budgets include receivers on both sheets and 5 pF per
board for traces. Connector and cable parasitics need physical validation.
Global clock/reset fanout, slew, supply integrity, reset during SRAM writes,
bus handover and PCB parasitics remain release dependencies.

Test fixtures initialise ROM and RAM while reset is asserted. A hardware
program loader, external display electronics and a replacement for AL1's
obsolete M27C322 are still required.

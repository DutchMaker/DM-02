# FR1 flash array and AL2 staged ALU

AL2 replaces AL1's obsolete M27C322 with eight SST39SF040-70-4I-NHE
devices. AL1 remains available as a separate legacy timing study.

The KiCad sources are `Circuits/KiCad/ALU/candidates/Flash-Array.sch` and
`Flash-ALU.sch`. `DM02-Flash.lib` uses the corrected PLCC32 assignments in
Microchip DS20005022F, May 2025, page 3. This choice is the industrial PLCC
part; the obsolete PDIP SST39SF040-70-4C-PHE is not a substitute.

## Address and byte mapping

The complete ALU image has 2,097,152 little-endian 16-bit words. Four banks
each contain two 524,288-byte flash images:

| Bank | Word addresses | Low/high device in AL2 | Images |
| --- | --- | --- | --- |
| 0 | `000000–07FFFF` | U101 / U102 | `bank0-low.bin`, `bank0-high.bin` |
| 1 | `080000–0FFFFF` | U103 / U104 | `bank1-low.bin`, `bank1-high.bin` |
| 2 | `100000–17FFFF` | U105 / U106 | `bank2-low.bin`, `bank2-high.bin` |
| 3 | `180000–1FFFFF` | U107 / U108 | `bank3-low.bin`, `bank3-high.bin` |

Local flash address is bits 18:0; bank select is bits 20:19. ALU address
bits 7:0 are B, 15:8 are A and 20:16 are the operation. FR1 numbers the
same flash devices U1 through U8.

CE and OE are tied low, and WE is tied high. Each flash has private output
nets. Two AHCT157 stages select the word bank. Two address fanout groups
each serve four flash inputs; buffered select branches each serve four mux
inputs. The simulator follows the schematic's actual pins.

AL2 keeps AL1's PH3 operand capture, PH1 result snapshot, PH3 A/flag
capture and synchronous C/Z commands. Shared DATA and clock/reset interfaces
retain their existing qualification gaps.

## Startup and programming

The flash requires at least 100 µs from valid supply to a read. AL2's test
fixture waits an additional 101 µs before normal reset release. A separate
monitor rejects early release; the flash model keeps results unknown until
its startup interval has elapsed. This is a test contract, not a physical
supervisor or oscillator-ready circuit.

The runner writes image manifests with sizes and SHA-256 hashes under
`Verification/build/flash-array/images/` and `Verification/build/alu-flash/images/`.
Every original word is reconstructed from persisted bank/lane bytes before
simulation. The build's `alu.bin` fixture has big-endian words for Verilog
`$fread`; it must not be programmed directly into these flash devices.

Batronix's USB Chip Programmer I support list names the exact PLCC part
and BA005 PLCC32-DIP32 adapter. Relevant pages and hashes are retained in
`Verification/vendor/flash/`. Support-list evidence does not prove physical
programming. For each device, erase, program its assigned file, read back
the entire device and compare the readback hash against the image manifest.
Keep bank, lane and schematic reference attached to the device throughout.

## Verification

```sh
python3 Verification/designs/flash_candidate.py --write
python3 Verification/designs/alu_candidate.py --flash --write
PYTHONPATH=Verification python3 -m unittest discover -s Verification/tests -p test_flash_hardware.py -v
python3 Verification/run.py --browser
```

The `flash-array` stage checks native KiCad connectivity, structural findings,
numeric loads, image reconstruction and 32,776 reads in each of three delay
profiles. Tests inject address, output, bank-select and write-protection faults,
plus bypassed startup inhibition.

The `alu-flash` stage has nine profiles: three standalone operand sweeps,
three continuous fetched programs and three all-opcode runs. Each full
standalone profile checks 8,192 operand vectors. Each opcode profile covers
227 opcodes in 454 cases. Both compiled demos then execute at maximum
device delays, with expected cycles and external IO checked through HALT.

The flash's 70 ns timing table uses a 100 pF output load; its maximum input
capacitance is 6 pF and I/O capacitance is 12 pF, specified at 25 °C.
Logic timing remains conditional on 50 pF tables. Physical supply behaviour,
full-temperature capacitance, shared DATA, SRAM turnaround, reset distribution,
clock slew/jitter, passive sourcing, footprints and independent review remain
release dependencies.

# CP1-SC1 first machine and CP1-IO1 expansion interface

Owner-approved direction, 16 November 2026: a stack/backplane computer with real text output, expandable buffered memory-mapped IO, local controls and a separate ESP32/LCD debugger. Machine-readable specification: [io-interface.json](io-interface.json). The circuit baseline remains **CP1-R2**, operated under [CP1-OC1](Operating-contract.md).

CP1-SC1 records the approved scope. CP1-IO1 selects the logical protocol below as engineering work. Connector geometry, electrical limits and circuitry require completion under `dm02-57n.4.1`; this specification is not a new accepted circuit revision.

## First physical demonstration

Program and read back the actual boot, control and ALU ROMs. From power-off, the computer must initialize its own RAM, run the diagnostic ROM and emit an exact expected text transcript through a real peripheral. Use a serial text transmitter to an external terminal for the initial implementation; choose its exact DIP devices, baud rate, electrical connector and readiness timeout in `.4.2`. The terminal receives text and supplies no execution services. The ESP32 debugger is separate equipment, not the text peripheral or an emulated memory/controller.

Provide local RESET, RUN/RESUME, HALT and one-microcycle STEP controls. Demonstrate boot and normal execution with the debugger disconnected, then attached; compare the transcript and diagnostic signatures. HALT/RESUME must preserve execution results. One STEP request while idle and READY must execute exactly one complete microcycle, following OC1. Error reporting must include a local indication when the text device itself fails. Define the diagnostic image, expected bytes/signatures, bounded timeouts and repetition count in `.5.3` and `.8.6` before physical acceptance.

The first machine requires text and expansion support. Physical graphics, keyboard and storage/program loading are later peripheral additions; retain the full archived instruction/graphics regression. Interrupt handling, DMA and hot plug are outside this first interface revision. Future reserved signals do not constitute implemented CPU features.

All computer and peripheral-card logic/memory remains DIP, with other fitted components through-hole. The owner's non-74xxx/SMD exception applies to the **external debugger**. Its initial functions are buffered observation and qualified reset/halt/resume/step requests. Direct 5 V connection to ESP32 GPIO is unsuitable: qualify level translation, thresholds, loading and isolation when either unit is unpowered. Debugger-disconnected operation is mandatory. Full-speed trace capture needs a hardware capture design with explicit overflow detection; firmware polling is not timing evidence.

## What R2 actually exposes

The boundary audit reads the hash-locked native KiCad netlists, rather than treating a generator's connector names as proof:

| R2 boundary | Actual function |
| --- | --- |
| BP1 J902 pins 4–11 | Registered write data, originating at ME1 U11 |
| BP1 J902 pins 12–19 | Registered **write** address, originating at ME1 U15 |
| BP1 J902 pin 3 | IO_STROBE for a pending write |
| BP1 J903 pins 3–10 | IO_INPUT byte returned to ME1 |

J903 has no read address or read qualifier. Reading `$FF03` after writing `$FF00` does not update J902's address latch. Using that latch for read decoding would select the wrong register. R2's host-supplied input byte therefore does not demonstrate an expandable addressed read interface.

ME1 J3 carries live ADDRESS; ME1 J1 carries MEM_n, LOAD_n10 and reset/phase inputs. The bridge needs a separately buffered live MAR read address and a qualified IO read condition. The logical condition is `ADDRESS[15:8] == 0xFF`, memory read active, memory write inactive, and valid reset/supply. A Boolean expression alone does not guarantee a glitch-free or sufficiently early signal. Routing these additional signals changes the design and requires affected verification before a new circuit revision is accepted.

## Logical connector contract

Use independent write-event and read paths. Each card receives W_ADDR[7:0], W_DATA[7:0], W_STROBE, R_ADDR[7:0], R_VALID and qualified RESET_n, plus power/returns. W_ADDR and W_DATA stay stable around the rising W_STROBE edge; exactly one decoded write is committed at that edge. Reset overrides all transactions. Never derive a write from changing live address decode alone.

Each card has a **private R_DATA[7:0] return** to a central multiplexer. The bridge selects the addressed card and drives ME1's single IO_INPUT byte. This adds return wiring but avoids connecting several card drivers to a shared tri-state return bus. It also makes an unallocated read return a defined zero. Inputs for empty slots require defined levels or explicit presence selection; floating connectors cannot implement this rule. Fanout buffering and central mux delay still need qualification.

Reads are side-effect-free. A future receive FIFO exposes its head and status through reads, then consumes the byte through an explicit command write. This avoids treating address-decode glitches or repeated polls as receive acknowledgements. R_VALID carries the qualified current read condition; it is not a CPU WAIT input. Clock generation and the CPU's instruction timing remain in the computer.

A pending registered write and a current CPU read may be visible together. Their addresses remain independent. The bridge/card implementation must define and verify coincident state changes, particularly status sampling while a serializer accepts a byte. The logical model serializes events and makes no metastability claim.

Physical pin numbers, connector family/orientation, slot count, stub length, current per slot and capacitive limits are not selected by this logical specification. `.1.2`, `.2.3`, `.3.2`, `.3.8` and `.4.1` own those decisions. Do not manufacture a connector from the signal-list order in the JSON.

## Address map

All offsets below are relative to `$FF00`; decoding includes the full 16-bit IO page.

| Address | Direction | Meaning |
| --- | --- | --- |
| `$FF00` | Write | Text byte, preserving the existing program convention |
| `$FF01` | Write | Reserved graphics data |
| `$FF02` | Write | Reserved graphics command |
| `$FF03` | Read | Text status: bit 7 PRESENT, bit 1 sticky OVERRUN, bit 0 READY |
| `$FF04` | Write | Text control: write bit 1 as one to clear OVERRUN; other bits ignored |
| `$FF05–$FF0F` | Reserved | No endpoint allocated |
| `$FF10–$FFFF` | Unallocated expansion | Allocate exact address/direction ownership when adding a card |

Reserved/unimplemented reads return `$00`; writes are ignored. Graphics addresses are reserved for their existing software ABI, not implemented by the text card. Addresses outside `$FF00–$FFFF` are not IO transactions; the reference model returns `None` for those reads to distinguish ordinary memory from an unmapped IO read.

One address/direction has one owner. A card may own noncontiguous offsets, as the text card does. Physical slot numbers do not automatically allocate addresses. Additions must update the map and prove isolation from existing endpoints.

## One-credit text handshake

1. Read `$FF03`. If PRESENT is zero, report an absent-device fault. Poll READY with a bounded timeout.
2. Once READY is one, write exactly one byte to `$FF00`. The sole CPU writer owns this credit until it writes or reset occurs. It cannot expire asynchronously.
3. The endpoint queues the byte and clears READY. When its serializer can accept the byte, it consumes the mailbox and returns the credit. The serializer must continue with CPU HALT, without requiring further CPU cycles.
4. A write while busy discards the **new** byte, retains the pending byte and sets OVERRUN. The diagnostic treats this as failure. Clearing OVERRUN at `$FF04` never consumes or replaces pending data.
5. Reset clears the mailbox and OVERRUN and suppresses transactions. Release alone does not grant a credit: the device must finish initialization. Restart may truncate a serial frame; the receiver discards that interrupted output and starts a new expected transcript.

READY means mailbox capacity, not that the final stop bit has reached the terminal. The physical demonstration checks the complete received transcript, including the final byte after CPU HALT. Status synchronization must never expose a false credit. A stale busy indication may delay software; a false ready indication may lose a byte. Define the clock-domain crossing or use a shared qualified clock in the endpoint design.

`Code/Assembler/programs/print_str/print_str.asm` currently writes without polling. Its source and the archived demos remain historical regression inputs. The hardware diagnostic/text routine must add this protocol under `.5.3`/`.4.2`; an unbounded stream cannot be made safe merely by adding a finite buffer. There is no implicit CPU wait-state mechanism in CP1-IO1.

## Verification and physical acceptance

`dm02.io_contract` checks the address map, exercises a logical mailbox/dispatch model and audits the native R2 connector/register pins. It rejects changed source hashes and detects the stale-write-address read error. The generated `build/cp1/io-contract-check.json` records the results; it is **protocol and boundary evidence**, not schematic-derived simulation of an implemented peripheral.

New timing budgets must include live MAR transfer → peripheral address/decode → status/return mux → ME1 → BF1 → destination, with the actual loads, edges and uncertainty. OC1 requires at least 10 ns setup reserve and positive hold/release/pulse margins. Similarly qualify write-address/data stability around W_STROBE, reset abort, power sequencing and all supported empty/populated slot configurations. There is no timing credit from the historical host IO model.

The first expansion validation must use the text endpoint plus a second independently addressed test endpoint/fixture, including absent-device, back-to-back address and opposing-data patterns. Verify isolation, returned values, safe reset and unpowered behaviour. Exact physical limits and tests remain in the owning Beads issues; scope selection and logical-model checks do not close fabrication or measured-machine gates.

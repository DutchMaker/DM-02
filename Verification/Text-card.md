# CP1-TX1 serial text-card candidate

TX1 implements the [IO1 text mailbox](IO-interface.md) with **37 DIP logic ICs**, a through-hole local oscillator, through-hole passives and a DIN96 card connector. It is a separate candidate. CP1-R2 remains the accepted digital computer; R2 + BR1 + TX1 would contain 270 DIP logic/memory packages before further supervisor or debugger-interface additions.

The native schematic is generated from `designs/text_candidate.py`. `dm02.text_card` independently reads KiCad's exported physical pin groups and emits discrete gate, multiplexer, counter and flip-flop models. The simulator receives neither the generator's Boolean equations nor a behavioral UART implementation.

## Mailbox and serial handoff

W_STROBE clocks the mailbox register, request toggle and overrun flip-flop. The full eight-bit W_ADDR decode selects `$00` or `$04`. Feedback multiplexers retain the mailbox on every other write. A text write with READY high captures W_DATA and toggles REQ; a busy text write preserves the mailbox and sets OVERRUN. Writing bit 1 at `$04` clears OVERRUN without changing the mailbox or REQ. Initialization suppresses acceptance and new overrun events.

The local baud domain has two request-synchronizer flip-flops. When the serializer is idle and synchronized REQ differs from ACK, it copies the mailbox into a separate transmit register and advances ACK on that baud edge. The mailbox can then accept another byte while transmission continues. ACK cannot advance again without another REQ transition. Once the mailbox is empty, its credit persists until the sole writer consumes it or reset occurs.

READY is the initialized, reset-qualified equality of REQ and ACK. ACK returns directly to the event-clocked write domain: there is no continuously running CPU-side clock on the card with which to clock a conventional acknowledgement synchronizer. The legitimate writer must first observe READY and then issue one write; the returned credit persists throughout this interval. This is a bundled-data, event-clocked candidate whose physical crossing behavior requires review. In particular, a forbidden busy write arbitrarily close to ACK release can violate the acceptance logic's timing. The digital profiles do not resolve metastability or establish an MTBF bound.

The 8-bit transmit register remains unchanged until the next frame. A four-bit counter selects start, eight LSB-first data bits and stop. The TX output is registered, with asynchronous preset to idle high. No CPU phase signal drives the serializer. Three baud-clocked initialization stages prevent credit release immediately after reset. Reset clears both stored bytes, request/acknowledgement, divider, state and overrun; it can truncate an active frame. The terminal must discard the interrupted transcript.

## Clock and terminal

The local oscillator is a separate **ACH-4.000MHZ-EK**, using its actual half-size DIP pinout: 1 NC, 4 ground, 5 output, 8 supply. It uses the same candidate ordering code as OC1. Its 10 ms maximum startup remains inside OC1's externally enforced, restartable 25 ms valid-supply guard. Simulations supply an already stable oscillator and do not qualify that supervisor.

Two counters divide by 208; a toggle flip-flop divides by another two. The nominal bit period is 104 μs, or **9615.3846 baud**, for a terminal configured to **9600 baud, 8 data bits, no parity, one stop bit**. Nominal baud error is +0.1603%; oscillator ±30 ppm gives approximately +0.1573% to +0.1633%. The receive fixture uses its own nominal 9600-baud sampling intervals. Physical receiver tolerance and cable edges still need measurement.

J2 is a two-pin 2.54 mm through-hole header: pin 1 ground, pin 2 5 V TTL TX through a 1 kΩ series resistor and an HCT244 buffer. It supplies no power. The receiving terminal interface must accept 5 V TTL levels. This is not an RS-232 voltage interface and is not a direct ESP32/3.3 V connection. The exact mated connector, receiver and cable remain part of the physical BOM/interface qualification. The series resistor is modeled as an ideal connection for logic tests; no cable RC or powered-off isolation is claimed.

J1 follows the slot-5 CN1 draft's 96 contacts. PRESENT_n is strapped to ground. R_DATA bits 2–6 are grounded; bits 7, 1 and 0 return PRESENT, OVERRUN and READY only at R_ADDR `$03` while R_VALID and reset are valid. The bridge's separate write/read addresses are preserved.

## Parts and conditional timing

`text-parts.json` selects exact TI CD74HCT E-suffix DIP devices and pins the manufacturer PDFs. The 74, 151, 157 and 161 sources were retrieved for this study. The 273 bounds and the combinational parts reuse the earlier pinned sources. Stock ownership and procurement availability have not been inferred from the owner's generic HCT inventory.

The first 35-DIP version passed the functional test but exceeded the load screen on six nets. The retained `iteration-1` directory includes its schematic, source snapshot, native netlist and results. Two added HCT244 packages distribute reset, oscillator/baud clocks and the request/acknowledgement/TAKE controls. The resulting 37-DIP circuit has no overages in the internal screen: summed device input-capacitance maxima plus a 5 pF planning allowance, against 50 pF for HCT outputs and 15 pF for the oscillator. This does not include the complete backplane/return/cable load or qualify edge rates.

The manufacturer's HCT delay rows assume 4.5 V, −40…85 °C, 50 pF and 6 ns input edges. OC1's supply/temperature lie inside that envelope, but cascaded HCT edges and the oscillator's specified edge bound do not establish the 6 ns test condition. The native path audit records conditional read-address, read-valid, write-address and write-data delay sums. These are screening figures, not guaranteed endpoint budgets.

The recorded sums are 159 ns from read address to READY return, 124 ns from R_VALID, 195 ns from write address to mailbox D, and 36 ns from write data to mailbox D. Adding the modeled 25 ns mailbox setup gives 220 ns and 61 ns respectively, before skew, routing, uncertainty and OC1's 10 ns reserve. Both standalone and CPU fixtures provide more stability than these conditional minima.

The models use each part's conservative maximum for both clock and asynchronous output changes; zero and alternating-zero/maximum profiles test functional sensitivity. The all-maximum profile checks digital setup, hold, clock-pulse and reset-release intervals. The first request synchronizer is explicitly excluded from setup/hold acceptance; its sampling is asynchronous by design. Sensitivity profiles retain observations but disable those timing assertions, so zero-delay passes do not imply positive hold margin. Reset pulse integrity, recovery/removal across all phases, metastability, analog slew and complete min/max timing remain open.

## Verification

The standalone fixture decodes all 256 byte values at the terminal pin using an independent 9600-baud receiver. It checks start/stop framing, all read addresses, ignored writes, persistent credit without CPU activity, busy-write preservation, sticky overrun, bit-1-only W1C, initialization, held-strobe reset release and reset abort with both an active frame and a queued byte. Write offsets vary across the local baud cycle. Alternating bits in byte `$55` also check the actual divided output period. The final queued byte must finish after all write activity has stopped.

Four deliberate mutations test mailbox overwrite on busy writes, early credit, reversed serial bit selection and substitution of the stale write address for live read decode. Failed runs are retained alongside passing profiles.

The composed CPU diagnostic uses all eleven locked R2 modules, native BR1 and native TX1. It verifies a separately addressed slot-6 fixture, polls `$FF03` with a maximum of 255 attempts per byte, rejects absent/overrun status, emits the literal five-byte transcript `TX1\r\n`, writes a success marker to slot 6 and executes HALT. An independent receiver checks the terminal pin, including the final stop bit after CPU HALT. Memory is preloaded for this diagnostic; autonomous ROM boot with BR1/TX1 remains separate work.

In the initial all-maximum composition, 45 I/O reads had at least 81.5 ns sampled setup and 425.5 ns sampled hold. HALT occurred at 3.863582 ms and the last sampled stop bit at 5.723901 ms. These observations cover this diagnostic and do not replace full-path timing qualification.

The final matrix passed all six standalone profiles (zero, maximum, two alternating-delay patterns and local-oscillator ±30 ppm) and detected all four mutations. Six CPU profiles passed: all-maximum, zero, two mixed profiles, +30 ppm CPU oscillator and absent text card. The five populated-card runs each checked five received bytes and 45 I/O captures. The fastest CPU sample had 81.476 ns setup; the smallest sampled hold among these runs was 250 ns. The absent-card run reached its diagnostic error marker without sending a text byte. The 255-poll timeout and overrun/absence branches are also checked in an independent architectural interpreter.

## Reproduction

Restore the dependencies in `Backup/README.md`. Generate and run into a new directory:

```sh
PYTHONPATH=Verification python3 -m designs.text_candidate
PYTHONPATH=Verification python3 -m dm02.text_card \
  --output Verification/build/text-new
```

The compiler rejects existing simulation directories. `build/cp1-text/run_study.py` defines the matrix and also refuses to overwrite its final directory. Preserve the release and both development iterations when making a revised candidate.

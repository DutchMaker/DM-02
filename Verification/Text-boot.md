# CP1-TB1 ROM-only serial startup

TB1 composes the locked R2 CPU, BR1 bridge and TX1 text-card models. The CPU starts at reset address zero, executes instructions from ROM, deposits a 160-byte application into poisoned SRAM at `$4000–$409F`, and jumps to that application. The RAM application polls READY, sends `TX1\r\n` and halts; the local serializer finishes independently.

This study changes the startup evidence from TX1's preloaded-memory diagnostic. It remains a simulation of the composed candidates. Physical ROM programming/readback, supply supervision, terminal operation and a promoted native production assembly remain open.

## ROM and RAM images

`dm02.text_boot` relocates the TX1 diagnostic's internal jumps to `$4000`, preserving its fixed I/O addresses. The 806-byte loader begins with `SP $FEF0`. It then executes one immediate load and one direct-address store for each application byte, followed by `JMP $4000`. This straight-line loader fits within the actual `$0000–$3FFF` decoded ROM window. The 64 KiB programming image fills unused locations with `$FF`.

The SRAM fixture contains only a deterministic address-dependent poison pattern. Four seeds exercise different power-on contents. Neither the application image nor CPU register state is injected into the DUT. `payload.hex` is loaded into an observer array solely for comparison. The ordinary R2 memory model is transformed only to select separate ROM and SRAM initialization files; its native read/write logic and device models are retained.

The architectural interpreter independently executes the actual ROM instruction bytes from PC zero. It verifies all 160 ordered address/data writes, the relocated payload hash, the `$4000` entry and stack pointer `$FEF0`. The loader executes 322 instructions. This verifies the chosen initialization sequence; it does not claim to initialize unused RAM or implement a general RAM self-test.

## Pin-derived execution checks

The supervisor-request fixture holds reset for 25 ms with stable CPU and text oscillators, then releases it through the existing C1 reset circuit. This represents OC1's minimum valid-supply guard. Actual supply validity, oscillator startup and supervisor behavior are assumed inputs, not simulated analog qualifications.

The boot observer watches the native SRAM model's completed write events. Every loader write must have the exact next address and byte. At application entry it requires exactly 160 completed writes and compares every reconstructed byte. A text-slot write strobe before that verified entry is a failure. The application performs no SRAM writes; any subsequent SRAM write is also rejected. The architectural oracle restricts loader writes to the payload address range; the native pre-entry strobe check covers the text slot specifically.

The inherited TX1 probe checks the separately addressed slot-6 fixture, sampled I/O setup/hold and the exact five-byte serial transcript. The terminal decoder observes only TX1's terminal output and uses its own 9600-baud intervals. Completion requires the last sampled stop bit to occur after CPU HALT.

Mutations change the first ROM-deposited byte, change its destination address, or jump directly to SRAM without running the loader. The expected payload remains unchanged so these failures cannot be hidden by regenerating the oracle from the corrupted image.

## Recorded results

All six startup profiles reconstructed the exact payload and decoded `54 58 31 0d 0a`. Each made 160 ordered SRAM writes and 43 I/O reads, including the slot-6 fixture read. The payload SHA-256 is `109193bdb678b1781dab87258b46f92e82e02b2a9461500566423d3e3f299c60`. The 65,536-byte ROM programming image SHA-256 is `ad3d1c67b407c9f3f0a0eee3a5a9ce01ea3d627298680a6b4ac59a182c7cabd2`.

| Profile | Poison seed | Sampled CPU setup ns | Sampled CPU hold ns | Final stop after HALT ms |
| --- | --- | --- | --- | --- |
| guarded-max | `$A5` | 81.5 | 425.5 | 1.898319 |
| seed-0 | `$00` | 81.5 | 425.5 | 1.898319 |
| seed-255 | `$FF` | 81.5 | 425.5 | 1.898319 |
| zero | `$5A` | 710 | 250 | 1.898208 |
| mixed2 | `$A5` | 373 | 367 | 1.898269 |
| mixed3 | `$A5` | 352 | 364.5 | 1.898230 |

The wrong-byte mutation fails at write index zero with `TB1 loader write data`. The wrong-address mutation attempts `$4001` instead of `$4000` and fails with `TB1 loader write address`. Skipping the loader fails with `TB1 incomplete reconstruction count=0`. All nine runs report zero device-model timing violations; zero-delay runs do not qualify physical hold timing.

The bounded replay regenerates ROM, poison, payload, loader listing, observer bench, memory initialization and native endpoint/bridge models. It verifies the saved logs and original R2 inputs against `text-boot-evidence.json`.

## Preserved development evidence

`initial-max` retains an elaboration failure caused by placing boot-monitor references before their signal declarations. `max` retains the second elaboration failure, where the completion probe referenced the boot flag before its declaration. The guarded version declares observer state at module scope before use and places monitor processes after the CPU/slot declarations. Neither failed attempt ran the simulator.

The Jev workflow skill was unavailable during this work; no advisory result is claimed. The acceptance checks are the recorded interpreter, native-model simulation, mutation and replay results.

## Reproduction

Restore the published R2, BR1 and TX1 dependencies from `Backup/README.md`, then use a new directory:

```sh
PYTHONPATH=Verification python3 -m dm02.text_boot \
  --output Verification/build/text-boot-new --seed 0xa5
```

`build/cp1-text-boot/run_study.py` defines the bounded matrix and reuses its completed maximum-delay baseline. Existing runs and matrix files are preserved.

# DM-02 verification

The default target is now **CP1**, the 192-package DIP design. Read [CP1 active verification](CP1.md) for source locations, locked-evidence replay, archive restoration and current milestone accounting. The original AL1/FD1 pipeline is available with `--target reference`.

The detailed sections below describe that preserved reference pipeline. Generated review drawings live in `build/`.

## Run it

The final regression suite has a 600-second timeout. A timeout or launch
failure is recorded as harness-error evidence with the available test log;
it does not leave the report marked as running.

Required: Python 3.10+, KiCad CLI 10, Icarus Verilog (`iverilog` and `vvp`), ngspice, Node.js, Perl and a .NET SDK/runtime capable of building the legacy netcoreapp2.2 compiler. Build `Code/Microcode/src/Mcc/Mcc.csproj` once with restore; verification uses `--no-restore` and runs the DLL with `--roll-forward Major`. The manufacturer-model analogue stage and its regression tests also require NumPy and SciPy (verified with 2.4.3 and 1.17.1). The pinned KiCad 5 symbol libraries and licence are included in `vendor/kicad5/`.

From the repository root:

```sh
python3 Verification/bootstrap.py
python3 Verification/prepare_analog.py
python3 Verification/run.py --target reference
python3 Verification/serve.py
```

Open **http://127.0.0.1:8020**. The server binds to localhost and serves read-only evidence. Use `--port 8021` if needed. Stop it with Ctrl-C.

`prepare_analog.py` downloads the hash-pinned TI HCT245 IBIS model and official
Apple-silicon IBISCHK 7.2.1 executable to `~/.cache/dm02/models`. Set
`DM02_MODEL_CACHE` for both preparation and verification to use another private
directory. This checker binary requires Apple silicon. The TI model's terms
restrict redistribution; the cache and generated circuits must stay outside
the served `Verification/` tree. Every run rechecks the original hashes,
executes IBISCHK and reconstructs the loaded-output experiment. A missing
cache blocks `analog`; changed inputs or failed tools produce an execution
error. Previous acceptance files cannot satisfy a new run.

`run.py` exits **1** for design failures or incomplete release gates, **2** for tool/harness errors, and writes `Verification/build/report.json`. For an automation job that accepts known design gaps, use `--allow-design-failures`; execution errors still exit 2. A successful evidence-collection command does not approve fabrication.

Run harness tests separately:

```sh
PYTHONPATH=Verification python3 -m unittest discover -s Verification/tests -v
```

Alternatively, run `python3 -m unittest discover -s tests -v` from `Verification/`.

The dashboard checks source and evidence SHA-256 hashes on refresh and every 20 seconds. Modified, added or deleted inputs mark results stale. Reports include timestamps, tool versions, requirement links, assumptions, logs and raw waveforms. A run-in-progress is displayed as incomplete. Input changes during a run produce an execution error.

## What each milestone delivers

### 1. Baseline and electrical inventory

* Requirements capture a provisional 1 MHz, 4.75–5.25 V, 0–50 °C prototype envelope.
* Seven legacy schematics are parsed using project libraries and pinned KiCad 5.1.6 symbols. Both symbol identity and displayed component value are retained.
* Review-only modern sheets use pin-numbered boxes at transformed pin endpoints. KiCad extracts their netlists independently. Physical references and multi-pin net groups are compared to geometric extraction.
* Six boards receive footprint, track and via counts plus reference-presence comparisons. This is not a pad-net, ERC or DRC check.
* `models.json` records candidate part numbers, model conditions and sourcing gaps. `risks.json` records the remaining work.

Migration now has two checks. The endpoint-box review compares connected pin groups. A second route, `dm02/native_migrate.py`, asks KiCad to import the original legacy symbol libraries and places those native symbols using KiCad rotation/mirror semantics. This independently checks Python's pin coordinates, aliases, units and hidden supplies. All 1,134 pin groups across the seven baseline sheets agree, including unconnected singleton groups. Tests cover all eight orthogonal transforms and demonstrate detection of a corrupted Python pin interpretation. Native review sheets and library-import provenance are in `build/native-schematics/`; the counted-clock candidate has the same check under `build/clock/native/`.

Both routes still share source placement/wire/scalar-label parsing. Bus graphics and entries are retained, but connectivity uses scalar labels. Vector/group labels, hierarchy and bus aliases fail closed. Original text annotations are not migrated. These are electrical review drawings, not approved fabrication files. Direct KiCad 10 netlist export of the legacy `.sch` was found to return an empty netlist; the harness rejects empty component sets and uses explicit modern review drawings.

`package-plan.json` assigns the ALU and Memory's 90 IC symbol instances to 32 packages. This includes supply/spare units, the added memory-buffer gate, the ALU result-output buffer and the flag-feedback buffer. The 49 formerly anonymous instances are annotated, including Memory gate-unit/pin remapping, and the 15 copied ALU value conflicts are corrected. HCT values state the selected logic family; manufacturer part numbers and speed grades remain separate choices. `dm02/packages.py` checks allocation against immutable instance stamps and verifies that unit changes preserve every pin endpoint and net label. Regression checks reconstruct anonymous unit-1 gates and reject duplicate units or changed pin geometry.

`dm02/electrical.py` inventories floating inputs, missing supply units, unplaced logic units, disconnected supply rails and direct LS-to-HC paths. It treats a labelled singleton input as unresolved. The four stack-counter receivers now specify HCT245 instead of HC245, and two unused HCT240 inputs are grounded. TI specifies HCT245 VIH=2.0 V over 4.5–5.5 V; HC245 instead requires 3.15 V at 4.5 V. This removes the identified receiver-family mismatch, while output loading and timing still need review. The custom NE555 discharge pin is corrected to open-collector output; SRAM A15/CE2 pins are corrected to inputs.

All 16 previously missing power units are placed, the 15 disconnected ALU supply pins are connected, and the previously unplaced spare gates on ALU, Memory, Registers and Power-Clock are terminated. Supply-short detection and pin-disconnection mutations cover these changes. The remaining 33 ALU clock/control inputs are now wired or terminated. The structural audit reports no findings across seven sheets within its stated scope.

The independent native-symbol check satisfies BASE-01's electrical review migration requirement. Exact purchasable parts, sourcing decisions and independent electrical review keep milestone 1 open. Milestone status is calculated from the acceptance requirements in `requirements.json`. Missing, limited or failing evidence cannot mark a milestone complete; the dashboard lists every gate.

The active power sheet's manual reset switch no longer shorts the MCP100 push-pull output to ground. Spare gates combine supervisor and button reset; a separate spare gate drives the indicator through 2.2 kΩ. `dm02/reset.py` extracts that logic cone and checks all four supervisor/button combinations, supply/pull-up/indicator routes and driver isolation. Mutations restore the short, bypass the indicator driver, reverse reset logic and restore the excessive indicator load. The retained MCP100 data sheet gives a 150–700 ms release delay but a 4.25–4.50 V trip range for the existing 450 grade. That does not qualify reset release against the 4.75 V machine envelope or oscillator startup during an arbitrary rail ramp; those remain open.

### 2. Representative-path method qualification

`hdl/pilot.sv` models a source register, an address-sensitive synthetic ROM (`address XOR A5`), a buffer and a destination register. The runner generates timing constants from `requirements.json`. Explicit procedural monitors check setup, hold, clock-high pulse, controller reset-release guard, active opposing drivers and captured data. Simulator `specify` checks are not relied upon.

Eight transfers run in each of eight scenarios: candidate phase, documented phase, and six injected faults. Qualification requires exact agreement between expected and observed violation classes plus all eight captures. Setup qualification includes a known-path propagation budget, because a destination can otherwise sample a stable *old* value without triggering a data-transition setup monitor. Reset is a synthetic controller capture-inhibit signal; the HCT574 itself has no reset pin. The pulse check covers high-pulse duration only. Output-enable sequencing, low-pulse limits and complete reset circuitry need system models.

| Term | Bound |
| --- | ---: |
| Source clock-to-output | 45 ns |
| ROM access | 100 ns |
| Buffer propagation | 28 ns |
| Destination setup | 25 ns |
| Clock uncertainty allowance | 10 ns |
| **Required separation** | **208 ns** |

The documented 120 ns phase leaves −88 ns; a candidate 300 ns leaves +92 ns under these assumptions. Neither stimulus qualifies the physical clock generator. Guaranteed minimum path delays, OE handover, fanout and clock skew are still needed for whole-machine timing closure.

The separate [C1 counted-clock candidate](../Documentation/Counted-clock.md) now implements an 8 MHz / 8 phase engine, opposite-edge staging, synchronized requests, complete-cycle stopping and a single-step pending latch in KiCad. `dm02/clock.py` generates pin-derived HDL, independently compares KiCad net groups and runs 90 delay/duty/frequency profiles, including startup and reset from every phase state. Its phase outputs drive the existing synthetic pilot. Actual idle phase levels are also checked against the Memory decoder with a write command held active: PH2/PH3 now park low to inhibit writes. Manufacturer excerpts and hashes are retained under `vendor/clock/`; exact logic and oscillator candidates are in `clock-parts.json`.

C1's nominal separation is 375 ns. The conditional lower bound is 343.26 ns, leaving 135.26 ns over the pilot requirement. The narrowest internal setup margin is 2.30 ns and depends on two 15 pF gate-output loads and a 2 ns routing/jitter allocation. Slew, jitter, PCB loads, metastability, debounce/HALT, the power supervisor and receiver reset inhibition still need qualification or implementation. Evidence is under `build/clock/`; C1 has not replaced the active RC clock, so the documented timing gate still fails and physical-clock qualification remains limited.

The `analog` gate reruns the bounded PILOT-03 experiment using TI's SN74HCT245N
model at its fully specified **5 V / 25 °C typical point**. B1/pin 18 drives
50 pF plus an opposing 1 kΩ fixture through its package R/L/C network. The
full extracted switching shape starts at 173 ns; the unchanged 300 ns capture
budget requires valid voltage throughout 265–315 ns. Thresholds are 2.0 V
high and 0.8 V low. The accepted standalone experiment had 65.389 ns minimum
margin; each normal run computes its own result.

Qualification includes official IBIS syntax checking, 12 DC solver comparisons,
eight manufacturer waveform reconstructions, four independent SciPy RLC
integrations, two timestep refinements and nine injected faults. The faults
cover overload, early capture, late launch and disabled drive on both edges,
plus incorrect die-capacitance conversion. Numerical tolerances are fixed at
10 mV and 0.1 ns. Computed traces and provenance are under
`build/analog/loaded/`; vendor model tables and derived circuits stay private.

The fast-column rising extraction is singular, and corner die capacitances
are missing. PILOT-05 retains full-envelope, physical load, clock/reset and
output-enable qualification. The 50 pF experiment does not qualify the larger
shared buses or the existing 1 nF-loaded Schmitt clock.

The retained `analog-rc` sensitivity study sweeps 30/100/200 Ω Thevenin drivers,
50/150/1000 pF loads and 3.84/4.75/5.25 V source highs. It checks high voltage
at 35 ns and low voltage at 750 ns against the same input thresholds. Its
nominal case must pass and its deliberate overload must fail. This linear RC
study remains limited evidence.

### 3. Module verification started

**Distributed flash machine and ROM boot:** the `distribution`, `backplane`
and `boot` stages run FD1/BP1/BL1 from normal repository sources. FD1 combines
AL2 with CD1 clock distribution, RD1 reset distribution and DF2 private DATA
routing at a **4 MHz oscillator target** (500 kHz complete microcycles).
The connector-slot name `AL1` denotes the AL2 circuit in this topology.

`designs/distribution_candidate.py` generates the candidate sheets under
`Circuits/KiCad/Distribution/candidates/`. The normal stage compares those
sources with freshly generated drawings and checks all 13 final sheets with
native KiCad. Four mux levels select fourteen continuously driven byte
sources; seven private receive branches use their own clock-edge timing
guards. Buffered CW selection has a physical FETCH1 override. Eight
continuous profiles and three all-opcode profiles exercise the machine;
nine wiring mutations and 28 boundary fixtures qualify fault detection.

The actual-pin audit joins 324 connector links and counts each IC input once.
Each link requires one driver, with 10 pF allocated to all traces and mating
connectors combined. BP1 preserves 81 headers and 884 pins, including the
PC1 J1 pin-10 ground strap. Its drawing is at
`Circuits/KiCad/Backplane/candidates/Backplane.sch`; native KiCad and four
connection mutations check the logical backplane.

The interval review retains 46 inherited/integrated paths. Conditional
4 MHz bounds pass; 8 MHz fails ROM delivery (−49.737 ns), SRAM delivery
(−34.737 ns) and external IO setup (−6.912 ns). This target uses C1's
tolerance assumptions. Exact oscillator selection, physical routing, reset
recovery/removal and private SRAM turnaround still require qualification.

BL1 builds a 64 KiB boot-ROM image with 50 bytes of loader code and 5,189
bytes of reverse RLE. Only the lower 16 KiB is decoded as ROM. The CPU uses
descending PUSH writes to reconstruct 16,542 bytes at `4000..809D`, initializes
workspace `FEF8..FEFA`, and jumps to `4000`. The SRAM model loads a separate
131,072-byte poison image. Every loader instruction is checked against the
architectural oracle; the hardware fixture reads SRAM to verify payload and
write counts without driving CPU state. The full boot trace expects
2,840,175 cycles, 43,829 IO events and all 48,000 pixels. It includes the
101 µs fixture wait for flash startup. The normal boot stage allows up to
7,200 seconds for simulation.

Results are under `build/distribution/`, `build/backplane/` and `build/boot/`.
These stages require successful prerequisites from the same run and remain
`limited` when their bounded checks pass. MOD-08 still needs physical
electrical qualification. Physical programming/readback and display
electronics remain open. The baseline timing failure remains a separate gate.

**Flash ALU replacement:** [FR1/AL2](../Documentation/Flash-ALU.md) replaces
the obsolete ROM with eight SST39SF040 PLCC devices and private output muxes.
`flash-array` verifies the eight programming images and pin-derived array;
`alu-flash` runs nine operand/fetched profiles and both complete demos. Reset
startup is fixture-enforced, and programmer support is documented separately
from physical programming/readback. AL1 remains a separate legacy candidate.

**Stack, MAR and memory/IO:** [SP1/MA1/ME1](../Documentation/Address-memory.md)
provide PH1 address snapshots, PH3 state capture, an early MAR bypass,
protected ROM/SRAM routing and registered IO output. `address-hardware` and
`memory-hardware` each run 13 profiles, including full-range standalone
sweeps and all 227 fetched opcodes. Their native KiCad comparisons,
manufacturer sources, timing budgets and load audits are published by the
runner. The complete DATA input budget is 90–100 pF before routing and
fourteen output-pin capacitances. SRAM turnaround, clock/reset distribution
and physical load qualification keep MOD-08 open.

`hardware-programs` runs both committed demos through all nine candidates
at the maximum-delay profile. Expected traces include opcode fetch and every
control cycle. ME1's external address/data/strobe pins supply the observed IO
stream; host rendering checks exact text and the 48,000-pixel framebuffer
against the source bitmap. The simulator allows up to 3,600 seconds per demo.
The large demo adds several minutes to a full run. Fixture memory loading
and the existing bootstrap jump remain explicit boundaries.

**ALU:** the Perl generator runs inside `build/alu/`. All eight ROM banks must have 524,288 bytes; every one of the 2,097,152 little-endian words is checked against a separate Python mathematical oracle. The oracle uses modulo-256 arithmetic, two-digit modulo-100 BCD, carry/borrow, signed two's-complement overflow for arithmetic, zero/negative/divide-by-zero flags, and the generator's special operation-12 zero inversion. Invalid BCD digits follow the generator's stated zero-digit policy. BCD carry/borrow and signed-arithmetic overflow defects have been corrected. V is zero outside signed arithmetic opcodes 3–15. Both `alu` and the retained `alu-core` evidence now check every bit; the regenerated ROM has zero data or flag mismatches. Controller instruction comparisons also include non-arithmetic V.

**ALU data and control paths:** `dm02/alu_circuit.py` generates HDL connections from physical KiCad pin nets for three 377 registers, the M27C322 ROM, a 244 flag-data selector, four 74 flip-flops, a 125 feedback buffer, glue gates and two 245 output buffers. It loads the complete generated ROM and checks 8,192 operand/function vectors against the independent oracle, 4,096 bus-flag round trips, 64 phase-qualified C/Z commands, bus release and two opposing-driver cases. Complementary external-address stimuli verify operand isolation after capture. Mutations restore the original address/operand and raw/stored-flag aliases, reverse buffer direction, swap address/flag-data lanes, break feedback, force a register enable active or reverse command-phase qualification.

The ROM's operand A nets are `ALU_A0..7`, separate from the `A0..15` address bus. Raw ROM flags are `ALU_FLAGS0..4`; stored flags remain `FLAGS0..3`. U13 drives results onto DATA only when `~ALU_out` is active. U9 packs C/O/Z/N into F bits 0–3 and grounds bits 4–7. The fifth ROM flag, divide-by-zero, is not stored. `dm02/logisim_alu.py` records the supplementary data-path connections using imported subcircuit appearances, with explicit splitter-mapping guards.

The Logisim clock-cone trace reproduces a rising flag clock on `ALU_out` while neither flag-data source is enabled. KiCad now selects raw flags on `ALU_out` and uses a common `CLOCK_PH3` clock for every ALU storage device. The 377 enable inputs select operand captures; U14 feeds each stored flag back to D while neither result nor bus loading is active. The old U4 tri-state clock buffer is disabled, with inputs terminated. C/Z asynchronous commands are masked outside the high phase. Logical checks require controls to settle during PH3 low and remain stable through capture; simultaneous raw/bus flag loads are invalid and produce observable contention.

The slice is driven through connector controls and an ideal PH3 clock. Physical clock skew, setup/hold, feedback/selector handover, asynchronous recovery/removal and reset sequencing remain unqualified. Evidence is under `build/alu/circuit/`; the bounded acceptance gate is MOD-09, while timed integration remains MOD-08.

**ALU microinstruction sequences:** `dm02/alu_sequences.py` replays compiled control words through the same KiCad-derived HDL. All 227 opcodes run across 16 incoming flag states and six boundary vectors: 21,792 cases, 101,952 microinstructions and 8,832 simultaneous A/flag captures. Fixture setup also uses connector load cycles. The test checks the bus before capture, flags after capture and ROM addresses after operand loading. The host supplies other register/memory values and expected bus/flags from the controller executor, which is separately checked against the instruction oracle. This ties the ALU circuit to the output-phase execution profile without claiming a physical controller or timed whole-machine model. Evidence is under `build/alu/sequences/`.

**Encodings:** all 32 ALU identifiers are compared between the mathematical contract, controller microcode and documentation. The documentation's reversed multiply halves and right-shift assignments have been corrected against the matching controller/generator definitions. All 227 emulator instruction definitions are compared with the microcode instruction table, including lengths and mnemonics. This is definition consistency, not complete execution coverage.

**Microcode images:** an independent Python expansion/encoder checks all 65,536 words in both C# compiler outputs and verifies the checked-in copies. The source defines 3,632 opcode/flag sequences containing 17,008 assigned words, with at most 14 t-states. The compiler now emits the formerly missing binary tail and final eight Logisim words. Regression cases cover dotted paths, EOF comments, invalid encodings, missing flag coverage, overlapping definitions and controls that cannot fit in a word. The remaining 48,528 words are zero-filled; invalid-opcode fail-stop behaviour is still undefined.

To regenerate the checked-in images after a reviewed source/compiler change:

```sh
dotnet build Code/Microcode/src/Mcc/Mcc.csproj
dotnet --roll-forward Major Code/Microcode/src/Mcc/bin/Debug/netcoreapp2.2/mcc.dll Code/Microcode/microcode.src
```

**Control execution:** the compiled ROM and generated ALU banks drive an untimed executor with independently expressed instruction expectations. All 227 opcodes run with all 16 incoming flag states and six boundary/state vectors under six profiles: counter functions before/after capture or PC updates from extracted Logisim counter logic, crossed with flags updated at ALU load/output. This gives 130,752 bounded cases, plus 36 staged nested CALL/RET checks. Each profile assumes a latched control word, live flags for the next ROM address, pre-increment PC/STK transfers to MAR, and flat writable memory with 16-bit wrapping. Physical decode, IO, bus hazards and opcode-fetch timing remain outside this model. Packed F now uses C/O/Z/N in bits 0–3 and zero in bits 4–7, matching the KiCad data-path check and guarded Logisim reference. This differs from the emulator's packed stack representation. POP/PUSH regression checks cover all 256 incoming bytes; the ROM's divide-by-zero bit is explicitly excluded from stored flags.

The earlier preservation-only oracle incorrectly rejected documented MOV and arithmetic scratch effects. The [assembly contract](../Documentation/Assembly-language.md#address-building-scratch-registers) now states exact effective-address and taken-branch effects, extending the existing convention to logical/comparison instructions and jumps. The emulator follows that contract. All six compiled-word profiles agree with it for the tested states. Output-phase flag capture matches the revised KiCad logical wiring; load-phase capture remains a sensitivity profile. The check stays **limited** because physical controller latching and timing are unqualified. `build/microcode/execution.json` records per-opcode counts and round trips; `execution-traces.json` includes an example of each mismatch-field pattern per opcode/profile when failures occur.

The emulator now shares the controller's stack ABI: CALL stores operand PC, RET adds two, and packed F stores C/O/Z/N in bits 0–3. `dm02/abi.py` compares 7,424 single-instruction fixtures against the actual JavaScript engine, including raw stack bytes, all call/return conditions, all POP F byte values and PC/SP wrap boundaries. Restoring the historical paired CALL/RET convention or paired F bit-order error makes this comparison fail, even though round trips alone could still pass. Evidence is under `build/microcode/abi/`. The comparison uses flat writable memory and excludes overlapping CALL code/stack storage and physical IO/timing.

**PC circuit and jumps:** `dm02/logisim_pc.py` extracts the 74161-Bus Boolean gate network and Program-Counter carry/load/clock connections from the supplementary Logisim design. All 4,096 nibble input/control combinations match independent 74161 priority equations; all 65,536 increment states wrap correctly. Flip-flop boundaries and data splitter bit ordering are explicit assumptions with geometry/wiring guards. A gate mutation verifies that the extractor observes changed logic. This is not a KiCad-derived PC or an electrical timing model.

The circuit gives load priority within each nibble, but terminal count still reflects the old output. Simultaneous PC_L_load and PC_inc can therefore increment PC_H when the old low byte is FF. The redundant PC_inc has been removed from JMP and CALL; inherited conditional sequences receive the same fix. A separate compiled-word audit checks all 65,536 targets for both instructions at the failing operand boundary, then all 18 jump/call opcodes at all 256 operand-PC low bytes and 16 flag states: 204,800 cases. Restoring the removed control reproduces the original fault in both mutation checks. Evidence is in `pc-circuit.json` and `control-flow.json` under `build/microcode/`.

**PC1 KiCad candidate:** the separate [program-counter circuit](../Documentation/Program-counter.md) uses four HCT161 counters, opposite-edge carry staging and reset-inhibited byte/address outputs. `dm02/pc_hardware.py` checks 65,536 increments, 12,288 load/control vectors and 16,992 compiled microinstructions in six delay/clock profiles, with C1 driving four profiles. Native KiCad pin-group comparison, seven wiring mutations and nine timing-fault checks accompany the simulations. The allocated DATA load is at least 70 pF versus the 50 pF timing condition; inactive-output capacitance is also unbounded. The dashboard therefore marks this evidence limited. Physical controller integration, global bus arbitration and MAR hold remain open. Evidence is under `build/pc-hardware/`.

**CW1 control-word candidate:** the [ROM/latch/decode slice](../Documentation/Control-word.md) adds two byte-wide OTP ROMs, a PH1 word latch, reset-cleared validity and a PH2 decoder window. Two profiles check every synthetic 16-bit word/address. Three C1-driven profiles replay 3,632 opcode/flag sequences and 16,992 microinstructions through the decoded controls into PC1. Hostile post-capture ROM-address changes must leave active controls unchanged. Nine pin mutations and four latch-timing faults qualify the checks. Fetch/t-state sequencing, live flag hookup, HALT arbitration and full-machine timing remain open, so the evidence is limited. ROM bank images, native KiCad comparison, timing allocations and logs are under `build/controller/`.

**SQ1 fetched execution:** the [fetch/sequencer candidate](../Documentation/Sequencer.md) drives C1, CW1 and PC1 through 264 fetched instructions / 1,424 cycles in six delay profiles. It stores IR, advances t-state, retains end/HALT before blanking and gates the C1 run request. Tests cover 128 conditional branches across all packed flags, ALU overflow, nested calls, a fourteen-state instruction, HALT/resume, held STEP, reset and PC wrap. Ten pin mutations must fail. ROM addresses come from hardware; behavioral peripherals produce bus values and live flags from actual decoded pins. Physical peripheral timing and DATA loading remain open. Evidence is under `build/sequencer/`.

**AL1 timed A/ALU/flags:** the [staged ALU candidate](../Documentation/Timed-ALU.md) adds PH1 result isolation, resettable A/flags, synchronous C/Z commands and reset-inhibited outputs. Eleven profiles cover 8,192 operand vectors, continuous fetched programs and all 227 fetched opcodes in 454 cases per instruction profile. Nine wiring and six timing faults qualify the tests. This supplies functional MOD-03 evidence under the documented phase contract; complete peripheral/electrical integration remains MOD-08 work. DATA loading exceeds the 50 pF timing condition, and the M27C322-100F1 is obsolete. Evidence is under `build/alu-hardware/`.

**RG1 timed B/C/H/L:** the [general register candidate](../Documentation/General-registers.md) replaces the four remaining behavioral general registers. Twelve profiles cover byte sweeps, every register-transfer pair and fetched execution of all 227 opcodes with physical-pin-derived A/B/C/H/L and flags. Eight wiring faults are detected. The combined AL1/PC1/SQ1/RG1 input-capacitance budget is 60–70 pF per DATA bit before routing, output capacitance and the remaining peripherals, already above the 50 pF driver timing condition. Evidence and exact receiver endpoints are under `build/register-hardware/`.

**Memory control:** `dm02/memory.py` extracts the KiCad Boolean gates and memory/transceiver pin nets. All 256 MAR high bytes are crossed with all 256 independent external-address high bytes, idle/read/write modes and both write-clock levels: 393,216 cases. A separate 55-route check validates all ROM/RAM address inputs and memory data-buffer lanes. The source fixes make decoding use the latched MAR, correct the transceiver direction, disable the memory buffer during IO, select SRAM through CE1 and qualify ROM/RAM output enable with reads. ROM and IO writes cannot write SRAM in the settled model. EPROM VPP is tied to +5 V for read operation, and the SRAM's isolated VCC net is joined to +5 V. `models.json` cites the memory pin/mode datasheets. Mutation tests restore each original decode/direction/write/isolation defect and swap physical address/data pins.

The memory model assumes settled MAR outputs and Boolean gates. It does not qualify asynchronous 74191 loading/ripple propagation, transient decode hazards, pulse widths or output-enable handover. Gate power and spare units are now placed and connected; the separate electrical audit checks their structural completeness. `build/memory/decoder.json` contains the extracted gate nets, route audit and mismatch examples.

**Compiled-control programs:** both committed demos execute through the control words, generated ALU ROM, extracted PC model and settled KiCad memory decoder. Starting at PC=0 exercises the binary bootstrap jumps; a RAM image receives the same three-byte ROM bootstrap as the browser loader. The runs execute 332,426 instructions / 1,617,957 microinstructions and check HALT, exact text and all 48,000 white/transparent pixel positions against the source raster. The memory adapter enforces ROM write protection and RAM/IO isolation using extracted chip/buffer control signals. The host IO adapter implements only the text and white-pixel commands used by these demos and rejects unsupported accesses. Fetch, word latching, settled MAR at each access, zero-initialized RAM and ALU-output flag capture are explicit assumptions. Display circuitry and physical memory timing remain unqualified. `build/microcode/programs.json` records binary hashes, opcode counts, final states, ignored ROM writes and the last 32 instruction entries.

**Registers:** an HDL slice is generated from extracted pin nets for U3/A, U5/B, U6/C, U9/H, U11/L and U14/IR. Every register captures all 256 byte values, drives its mapped output, and releases the shared bus where applicable. The slice uses illustrative 45 ns capture propagation and 50 ns OE settling, with generous stimulus intervals. It excludes decoded clocks, stack-pointer circuitry, other drivers and physical supply behaviour.

**Emulator:** the actual instruction engine runs in Node with deterministic RAM and a stubbed DOM. More than 1.3 million assertions cover every operand pair and incoming carry for ADD/ADC/SUB/SBC/CMP, logical and shift/rotate handlers, all INC/DEC register values, all 65 MOV encodings, address-building scratch effects, all jump/call conditions, packed flags, stack round trips and nested calls. MOV checks compare every memory byte and exercise pair transfers across FF/FFFF boundaries in the flat memory fixture. Fixes include byte wrapping, signed overflow, negative/zero flags, SBC register decoding, pre-increment POP, flag unpacking, byte-wide named-register NOT and large shift counts. New pair-transfer fixes capture both bytes for `MOV BC,(address)`, write through the pointer for `MOV (address),BC`, and capture the source pair for `MOV (HL),BC` / `MOV (BC),HL`. Conditional-return, physical memory/IO and complete fetch/address-boundary coverage remain incomplete. Non-arithmetic V=0 matches the ROM contract.

**Real browser:** `emulator-browser.cjs` runs both committed demos through the actual CPU, memory, IO and canvas in Chrome. It checks HALT, exact text, the bitmap terminator and all 48,000 canvas pixels against the source raster plus transparent remainder. The bitmap contains 16,382 pixels with a partial final row; a missing terminator previously let instruction bytes be interpreted as pixels. The source now includes an explicit `$FF` delimiter and both demo binary copies are regenerated.

To include browser evidence in the runner, install Playwright in your Node environment and run `python3 Verification/run.py --browser`. If Playwright is installed outside the normal module search path, set `NODE_PATH` to that installation's `node_modules` directory. Chrome is required. The browser test starts and stops its own loopback HTTP server.

To reproduce the graphics-demo binaries, run `dotnet build Code/Assembler/src/Asm/Asm.csproj`, then `python3 Verification/rebuild_demo.py`. That assembles in an isolated build directory and compares both committed copies. Add `--write` to regenerate them after a source change; the command records source/compiler/output hashes in `build/demo-build.json`.

## Reading results

* **pass**: the stated check passed within its declared scope.
* **fail**: observed output disagreed with its contract or timing bound.
* **limited**: an experiment completed but its model does not satisfy the hardware acceptance criterion.
* **blocked**: required design work or evidence is absent.
* **error**: a tool, parser or harness could not produce trustworthy evidence.

Fault rows are checker qualifications: a pass means the expected fault was caught. The release gate stays blocked until complete schematics, exact parts, module/system correctness, physical timing, layout review and bench qualification are available. No overall pass percentage is used to infer release readiness.

Generated files are ignored by Git. Preserve `build/` or download its report and evidence when archiving a run. The supplied dashboard is dependency-free; `dashboard-smoke.cjs` is an optional browser check requiring Playwright and Chrome.

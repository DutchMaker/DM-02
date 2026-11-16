# Native integrated candidate

`candidates/MD1/MD1.kicad_sch` adds two DIP buffers and two decoupling capacitors
to isolate the ME1 address loads from the raw MAR bus. The seventeen-sheet,
272-DIP candidate has fresh affected memory and ROM/text boot evidence.
See `Verification/MAR-distribution.md` for conditional load allocations and
physical qualification scope. CA1 and NA1 remain preserved below.

`candidates/CA1/CA1.kicad_sch` adds the CN1 CPU-card/backplane connector pairs.
It separates the four CPU net domains and verifies all 768 mating contacts
before and after analytical mating. Its sixteen native files remove NA1's
non-fitted boundary markers and add sixteen fitted candidate DIN96 connectors.
See `Verification/Connector-assembly.md`; physical/production acceptance remains
open. NA1 below is preserved as the preceding integration candidate.

Open `candidates/NA1/NA1.kicad_sch` in KiCad. Its fourteen child sheets combine
the R2 CPU with MQ1/BR1 and TX1. All fifteen native schematic files are tracked
source; symbols are embedded and component/library identities are unique across
the hierarchy.

CP1-NA1 is a connectivity candidate with 270 DIP logic/memory ICs. R2 remains the
accepted circuit. The 58 logical boundary markers are excluded from BOM and
board transfer; CPU DIN implementation and production schematic/PCB work remain
open. Connector values and footprints are inherited candidates.

See `Verification/Native-assembly.md` for evidence, limits and regeneration.
The generator is `Verification/dm02/native_assembly.py`. Regenerate into a new
study directory, compare the native exports and qualify affected changes before
updating this candidate. Preserve the locked inputs and earlier iterations.

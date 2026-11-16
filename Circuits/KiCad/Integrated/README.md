# Native integrated candidate

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

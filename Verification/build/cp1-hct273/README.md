# CP1-R2: documented HCT273 timing

This revision replaces the three SN74HCT273N registers with **CD74HCT273E**:
AL1 U2, ME1 U11 and ME1 U15. The package count stays at 192 DIP logic/memory ICs.

TI SCHS174D explicitly specifies 38 ns clock-to-Q and 40 ns clear-to-Q maxima
at 4.5 V, −40 to 85 °C and 50 pF. The model retains CP1's conservative 42 ns
delay envelope, 25 ns setup/reset-release separation, 25 ns clock pulse and
20 ns clear pulse. It adds the part's **3 ns data-hold check**.

`acceptance.json` is the acceptance receipt. Its absence means this revision
has not completed acceptance. `verification-state.json` records the full run;
the active CP1 lock changes only after acceptance and publication checks pass.

## Source and hardware checks

- `source-manifest.json` pins all 430 candidate inputs and exactly five changes:
  the generator, device selection, HDL timing model and AL1/ME1 schematics.
- `part-qualification.json` compares all 12 board netlists with accepted CP1,
  checks all 60 substituted device pins and the DIP-20 footprint, and records
  24 allocated output loads.
- Hold-monitor fixtures reject a 2 ns interval and accept the 3/4 ns boundaries.
  A disabled-monitor mutation is detected by the expected-rejection oracle.
- Native KiCad parity, physical pads, merged loads and backplane binding checks
  remain required. The initial native audit exceeded its outer 240-second
  execution budget; its partial exports are preserved under
  `failed-runs/native-240s/`. The completed retry used a 900-second budget.

## Reproduction

The release archive contains the complete candidate source and evidence tree.
After restoring it from the repository root, use:

```sh
python3 Verification/build/cp1-hct273/run.py --prepare
python3 Verification/build/cp1-hct273/audit.py --native
python3 Verification/build/cp1-hct273/physical.py
python3 Verification/build/cp1-hct273/component_review.py
python3 Verification/build/cp1-hct273/qualify_part.py
python3 Verification/build/cp1-hct273/freeze_sources.py
python3 Verification/build/cp1-hct273/verify.py
python3 Verification/build/cp1-hct273/interconnect.py
python3 Verification/build/cp1-hct273/update_workbook.py --validate
python3 Verification/build/cp1-hct273/finalize_revision.py
python3 Verification/build/cp1-hct273/publish_revision.py
```

The full verification includes a fresh ROM boot through graphics HALT. The
watchdog remains 11.3617 simulated seconds, covering two expected schedules
plus startup allowance. Wall-time budgets are derived from measured short
profiles. Simulator output is checked against independent instruction/program
oracles; timing and hold checks remain active in the full boot run.

The BOM workbook retains all 16 sheets, every existing formula and stock entry.
Only three instance values, the matching BOM identity/notes and guide links are
edited. LibreOffice recalculation must report 46 formulas and zero errors before
workbook validation.

## Physical boundary

The replacement resolves the selected 273's ambiguous delay-table label. Its
delay limits still require qualified output loading and input edges. HCT245 IO
capacitance/release loading, SRAM turnaround, HC377 full-supply compatibility,
reset/oscillator startup, independent electrical review, exact stock/sourcing,
programming/readback and PCB/bench work remain open. This is not a physical
qualification of the unchanged 1 MHz, 4.75–5.25 V, 0–50 °C operating envelope.

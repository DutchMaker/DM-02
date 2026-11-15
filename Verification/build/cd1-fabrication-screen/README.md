# CD1-P2 supplier-rule and CAM screen

This local experiment checks CD1-P2 against OSH Park's published two-layer
rules and compares offline manufacturing exports with native KiCad geometry.
The files named `SCREEN-NOT-FOR-FAB` are preview inputs. Electrical loading,
component fit, power distribution and assembly qualification remain open.

## Sources and interpretation

`sources/manifest.json` records eight supplier publications and eight copied
local inputs with retrieval times and SHA-256 hashes. `supplier-facts.json`
keeps 24 facts with their source and quoted evidence. The HTML tables and PDF
text are extracted alongside the originals; material PDF pages are rendered
in `document-pages/`.

The service page states a maximum 0.0508 mm drill-position tolerance. The
dedicated drill page states +/-0.0635 mm. Both statements are retained;
0.0635 mm is the local sensitivity input, pending supplier clarification.
The supplier explicitly says its 0.127 mm nominal annular-ring design minimum
already accounts for fabrication tolerances. This screen does not subtract
those tolerances and then compare the reduced ring against the same minimum.

For finished-hole size, the published +/-0.0635 mm gives 0.7365 mm minimum
for the 0.8 mm component holes and 0.9365 mm minimum for 1.0 mm holes. These
dimensions do not establish fit without exact component lead and socket data.

Published stackup figures are 1.524 +/-0.1524 mm core, 0.03556 mm copper with
no tolerance stated, and 0.01524 +/-0.00508 mm solder resist. The mil figures
are converted exactly; the supplier's rounded metric text remains in evidence.
Its service dielectric figure is 4.5 at 10 MHz. The linked KB6167F material
sheet gives typical 4.8 at 1 MHz and 4.6 at 1 GHz, with a specification number
of <=5.4 and typical values marked for reference. Those figures do not form
a complete frequency-dependent finished-board permittivity bound.

The linked PSR-4000BN sheet is dated March 2005 and names green/dark-green
mask. Its 4.5 dielectric constant is an internal 1 MHz result. The service is
purple, so coating formulation and applicability remain unresolved.

## Native screening copy

`screen.py` creates a separate P2 copy. Its pad positions, shapes, dimensions,
drills and nets, and all 185 tracks and nine vias, match P2. The original four
custom rules remain an exact prefix. Existing stricter clearances, track width,
annulus and drill minimums are retained; minimum connection width, via
diameter and text thickness are strengthened where needed. Global mask
expansion changes from zero to the supplier-recommended 0.0508 mm in this copy.
The minimum mask-web merging setting remains zero, as the KiCad guide recommends;
exported openings are measured separately.

Native KiCad 10.0.8 DRC reports zero configured violations and zero unconnected
items. Its five ignored checks are listed in `screen-drc.json`; schematic
parity is not part of that CLI invocation. The source P2's independently
verified pad/net assignments are preserved.

Four stored PCB mutations exercise narrow track/connection width, undersized
via diameter/annulus, undersized drill and thin silkscreen text. Every mutation
produces its expected native DRC diagnostic. Results and full faulty boards
are in `rule-fault-checks.json` and `rule-faults/`.

## Independent CAM checks

The offline preview has seven Gerber layers and separate plated/nonplated
Excellon files. Gerbonara 1.6.3 parses these exports. Comparisons check:

- 99 plated drill coordinates, diameters and counts; zero nonplated holes.
- Four outline centerline segments defining a 60 x 70 mm rectangle.
- All 185 track endpoints, widths, layer assignments and Gerber net attributes.
- 198 pad/via copper flashes across both layers: positions, dimensions and nets.
- 180 mask openings: pad positions and 0.0508 mm expansion on both sides.
- Both filled-ground polygon areas and full symmetric differences against
  P2's native exported polygons. Both symmetric differences are zero.

Flash bounding dimensions are checked; complete aperture shape equivalence is
not claimed. Mask-opening bounding boxes give a conservative minimum separation
of 0.7384 mm, above the 0.1016 mm process minimum. All nine vias remain tented.
The preview renderer reports missing paste layers because this board is entirely
through-hole; paste layers were intentionally absent from the requested export.

KiCad uses positive-down board Y coordinates; CAM uses negative Y for this
absolute origin. The checker explicitly maps (x,y) to (x,-y). Gerbers retain
six decimal places in mm; metric Excellon retains three. One via at
(54.3638,57.1162) mm becomes (54.364,57.116) mm, a 0.0002 mm error per axis.
The checker requires the exact quantized multiset and rejects collisions.
This file precision is separate from manufacturing tolerance.

Gerbonara's automatic drill plating inference is unreliable for these KiCad
X2 comment headers. The checker validates `TF.FileFunction` and filename
agreement, then supplies `plated` explicitly to `ExcellonFile.open`. The parser
also warns about KiCad's G90 placement after the header; verified absolute-mode
coordinates still match native geometry. Renderer warnings about an unused
macro parameter are retained in the audit record.

Nine parsed-record mutations and four actual serialized CAM mutations are
rejected. The latter alter a drill coordinate, plating header, outline endpoint
and mask aperture; they are reparsed from disk before comparison.

Offline parsing is distinct from the supplier's upload interpretation. The
supplier's KiCad guide currently names 9.x; this experiment uses 10.0.8.
Its generic drill-format guidance names inches/2:4, whereas this preview uses
explicit metric decimal output. Supplier preview acceptance remains open.

## Coating sensitivity

`coating.py` imports the archived, previously benchmarked field solver. Nine
cross-sections use supplier-anchored dimensions: service nominal values,
published core extremes, two material dielectric figures, and hypothetical
coating cases. The coating is a flat dielectric slab from substrate surface
to copper top plus the stated coat thickness. It fills the coplanar gaps.
This geometry does not assert the actual coating profile or its permittivity.

Every scenario uses a uniform 0.25 mm trace/gap, continuous same-layer grounds,
continuous lower ground and 0.03556 mm copper. No pads, barrels, branches or
mutual coupling are included. Multiplication by a root's total routed length
is an equivalent uniform-line comparison, neither a board extraction nor an
upper or lower capacitance bound. The 5 pF trace allocation is separate from
the device's 50 pF characterization condition.

The coating implementation is checked against the archived uncoated model
using coating er=1. A representative coated case uses three mesh sizes and
a 12-to-24 mm domain expansion. All discrete energy, charge and residual
checks remain active. Raw convergence results are in `coating-results.json`.
No numerical value is promoted into the normal timing model.

## Reproduction

From the repository root, use KiCad's bundled Python for native operations
and the geometry environment with the versions in `requirements.txt` for
CAM and field calculations:

```sh
python3 Verification/build/cd1-fabrication-screen/prepare.py
"$AUDIT_PYTHON" Verification/build/cd1-fabrication-screen/extract_sources.py
python3 Verification/build/cd1-fabrication-screen/facts.py
"$KICAD_PYTHON" Verification/build/cd1-fabrication-screen/screen.py
"$KICAD_PYTHON" Verification/build/cd1-fabrication-screen/check_rules.py
"$AUDIT_PYTHON" Verification/build/cd1-fabrication-screen/audit_cam.py
"$AUDIT_PYTHON" Verification/build/cd1-fabrication-screen/check_cam_files.py
"$AUDIT_PYTHON" Verification/build/cd1-fabrication-screen/coating.py
python3 Verification/build/cd1-fabrication-screen/publish.py
python3 Verification/build/cd1-fabrication-screen/verify_publication.py
NODE_PATH="$PLAYWRIGHT_NODE_PATH" node Verification/build/cd1-fabrication-screen/browser_check.cjs
```

Publication verifies all 223 existing layout/capacitance artifact hashes and
the copied inputs before building the page. No supplier has been selected,
contacted, sent files or paid. Milestones remain 3/5, 2/5 and 8/9.

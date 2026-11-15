# CD1-P2 ground stitching experiment

P2 adds eight ground-connected through vias to the published P1 routing.
All 185 routed segments, the original signal via and all 90 pad geometries
and nets are preserved. The board remains a routing experiment.

## Result and acceptance

All eight signal layer transitions acquire a nearer ground barrel. The worst
center-to-center distance falls from 10.160 to 2.050098 mm. Seven transitions
meet the original 2.00 mm target; U3 pin 4 does not. This is recorded as a
limited result. The 2.00 mm target is analyst-selected, not a datasheet or
signal-integrity requirement, and it was not relaxed after the search.

The search uses a 0.05 mm board-coordinate grid within 3 mm of each transition.
Each via center must be at least 0.45 mm inside existing filled ground on both
layers. Via copper diameter is 0.8 mm; drill is 0.4 mm. This is a bounded grid
search with earlier selections retained, not a global layout optimum.

Native DRC has no violations or unconnected items. Its five default-disabled
checks remain recorded. Exact native XML-to-PCB pad-net comparison is run;
KiCad's schematic-parity option is not run.

The geometry audit verifies all sixteen layer contacts, preserved routing
and pads, and identical ground-fill areas. Native point containment agrees
with GEOS at every exported comparison point. Ground tracks/pad copper are
not added to the filled-zone polygons, and neither ground-current paths nor
frequency-dependent impedance are extracted. The new barrels change the
electromagnetic environment and require a fresh physical loading review.

## Fault evidence

Three existing checks cover the open SQ1_PH0 clock, a 5 V-to-GND short at C1,
and a connector pin remap. The power-short checker accepts KiCad's
`shorting_items` or `tracks_crossing` diagnostics only if both supply nets
occur in that diagnostic's items. Native KiCad can choose either report for
the same short. Earlier exploratory logs retain the narrower check's failure.

Eight stitch-removal fixtures are saved and reloaded before their absence
is checked. A wrong-net fixture preserves a 5 V via assignment using the
free-via flag. The stored net and flag are checked before DRC; DRC reports
`via_dangling`, and the stitch contract rejects the wrong net.

The early wrong-net fixture was invalid because KiCad reassigned an ordinary
via to its surrounding ground copper during save. A no-error DRC result for
that restored ground via is not evidence that a real wrong-net fault escaped.
The probe files and early logs are retained for this diagnosis. They are
superseded by `generation-verified.log`, `change.json` and the final mutation
reports. The final mutation's UUIDs match the final candidate.

The exported-geometry checker separately rejects eight missing stitches,
a wrong net, a 0.1 mm displacement and a reduced via copper diameter. Every
missing stitch worsens at least one transition's nearest-ground distance.

## Reproduction

Run from the repository root. KiCad's bundled Python supplies `pcbnew`.
The geometry environment uses Shapely 2.1.2. No remote manufacturing service
is used.

```sh
python3 Verification/build/cd1-stitching/prepare.py
"$AUDIT_PYTHON" Verification/build/cd1-stitching/plan.py
"$KICAD_PYTHON" Verification/build/cd1-stitching/generate.py
"$KICAD_PYTHON" Verification/build/cd1-stitching/export.py
"$AUDIT_PYTHON" Verification/build/cd1-stitching/audit.py
python3 Verification/build/cd1-stitching/publish.py
python3 Verification/build/cd1-stitching/verify_publication.py
NODE_PATH="$PLAYWRIGHT_NODE_PATH" node Verification/build/cd1-stitching/browser_check.cjs
```

`sources/` holds the archived P1 board and helpers. Its hashes are checked
against the original inputs before publication. Generation assigns new via
UUIDs; a re-run can change file hashes while reproducing the same geometry.
Use a copied experiment directory when retaining a published snapshot.

The P0 and P0/P1 manifests remain intact. Normal functional acceptance,
oscillator/reset qualification, procurement and fabrication approval are
unchanged.

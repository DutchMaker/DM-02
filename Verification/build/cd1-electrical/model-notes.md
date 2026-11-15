# CD1-P0/P1 electrical-layout screen

## Reproduction

From the repository root, use KiCad's bundled Python for `refine.py` and
`export_geometry.py`. Use a separate Python environment with
`shapely==2.1.2` for `analyze.py` and `test_analysis.py`.

```sh
"$KICAD_PYTHON" Verification/build/cd1-electrical/refine.py
"$KICAD_PYTHON" Verification/build/cd1-electrical/export_geometry.py
"$KICAD_PYTHON" Verification/build/cd1-electrical/export_geometry.py --source Verification/build/cd1-electrical/candidate --out Verification/build/cd1-electrical/candidate --board CD1-P1-routed.kicad_pcb
"$AUDIT_PYTHON" Verification/build/cd1-electrical/analyze.py
"$AUDIT_PYTHON" Verification/build/cd1-electrical/analyze.py --directory Verification/build/cd1-electrical/candidate
"$AUDIT_PYTHON" Verification/build/cd1-electrical/test_analysis.py
python3 Verification/build/cd1-electrical/build_page.py
```

`refine.py` uses the preserved `../cd1-layout/check.py` for native XML
pad/net parity and the three existing DRC/connectivity mutations, then adds
the missing-branch-via mutation. Regeneration assigns a new KiCad UUID to
the added via; exact file hashes can change while the checked topology and
geometry remain the same. Re-running a published experiment regenerates its
outputs, so use a copy when preserving an existing evidence snapshot.

## Ground-fill geometry

For each straight signal track, intersect its centerline with the stored
filled ground-zone polygons on the other copper layer. Compute the length
of the difference and retain every resulting interval. There is no sampling
step in this length calculation. Native KiCad containment at a regular grid
and at signal-path points is a separate cross-check of the polygon conversion.

KiCad's fills use zero-width bridges to represent holes. GEOS `make_valid`
converts these outlines into polygons. Conversion must preserve area within
0.000001 mm² and match every native sample. The source PCB is not rewritten
by the exporter or audit.

The result excludes standalone ground tracks and pad copper outside zone
fills. It includes pad clearance regions. It neither reconstructs a return
current path nor calculates a ground-corridor width or return inductance.
Maximum gap length is reported per individual track segment, without merging
across track boundaries. Signal layer transitions count pad-center endpoints
and explicitly exported through vias. Ground-connected through-hole pads are
the available reference barrels on these two boards; ground vias are absent.

## Microstrip sensitivity

Reference: Qucs technical documentation, *Single microstrip line*, Schneider
equations 11.3 and 11.14, retrieved 2026-11-15. The complete source HTML is
archived as `microstrip-reference.html`; its LaTeX comments retain both
equations. This is a secondary technical reference, not a PCB supplier's
stackup specification.

For trace width W, dielectric height h, relative permittivity er and u=W/h:

```text
ee = (er+1)/2 + (er-1)/(2*sqrt(1+10/u))
Z0 = Zvac/sqrt(ee) * ln(8/u + u/4)/(2*pi)              when u <= 1
Z0 = Zvac/sqrt(ee) / (u + 2.42 - 0.44/u + (1-1/u)^6) when u > 1
Zvac = 376.730313668 ohm
v = 299792458/sqrt(ee) m/s
C' = 1/(Z0*v) F/m = 1e9/(Z0*v) pF/mm
t' = 1e9/v ps/mm
```

W is 0.25 mm, matching all routed signal tracks. Heights 1.53, 0.8, 0.4 and
0.2 mm and relative permittivities 4.0 and 4.8 are hypothetical scenarios.
The stored 1.6 mm board thickness alone cannot determine dielectric height.
No manufacturer laminate, finished copper thickness, solder mask or tolerance
has been qualified. In particular, a 0.2 mm plane spacing is an alternative
stackup scenario, not a property of the present two-layer board.

Each network result multiplies C' by its total routed track length, including
branches. Root nets use the existing 5 pF allocation from the archived
`distribution-parts.json`. These results assume a uniform infinite ground
plane, zero copper thickness and no other conductors. They are neither upper
nor lower bounds for the routed board. The added P1 via's capacitance is not
included. Pads, branches, bends, solder mask, same-layer copper, couplings,
connectors and device loading require an actual field/load model.

## Decoupling pin identity

The archived TI SN74AHCT244 pin table identifies VCC as pin 20 and GND as pin
10. Pins 1 and 19 are output enables even though the schematic ties them to
ground. The audit reports pad-center distances from each capacitor to pins
20 and 10; it does not substitute a nearby grounded logic input for the
device's actual supply-ground pin. These distances are not loop lengths or
inductance estimates.

## Acceptance

P1 preserves all 90 pad-net assignments and 185 unchanged track segments.
Configured native DRC finds no violations or unconnected items. The existing
three faults and removal of the new via are detected. The existing DRC report
still lists default-disabled checks; native schematic parity is not run.
The exact XML-to-PCB pad-net comparison is run.

No complete-machine timing, procurement, assembly or fabrication gate is
closed by this experiment. The normal completed functional archives remain
separate from this focused physical-layout evidence.

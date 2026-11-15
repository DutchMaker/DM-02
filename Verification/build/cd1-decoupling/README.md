# CD1-P3 decoupling placement experiment

P3 replaces the three generic 5 mm-pitch capacitors in the isolated P2 board
with nominal footprints for KEMET C315C104K5R5TA: 100 nF, ±10%, 50 V, X7R,
2.54 mm nominal lead pitch. The functional pad/net mapping remains identical
to the native CD1 XML. The normal schematics and timing models are unchanged.

## Placement result

The three new direct front-layer VCC feeds are 3.000, 3.000 and 3.905125 mm
long and 0.50 mm wide. P2's capacitor-to-VCC paths were each 4 mm at 0.25 mm.
All 185 original tracks and nine vias remain, including every signal route.
P3 adds three supply tracks and two 0.8 mm / 0.4 mm-drill supply vias, giving
188 tracks and eleven vias. The extra vias replace the interlayer supply
connections formerly provided by the old C1/C2 VCC component barrels.

C2 also lies on the retained backside supply backbone. Its wide front feed
is a parallel connection, and deleting it does not break DC connectivity.
That case is enforced by the explicit layout-intent check rather than DRC.

The first C3 position intersected a ground track and ME1_PH2. That rejected
board and its four DRC findings are retained in `rejected-first-placement/`.
Moving C3 upward by 2.5 mm removed those conflicts without changing signal
copper. Final configured native DRC has zero violations and zero unconnected
items. Five ignored checks remain listed in `drc.json`.

The copy uses the preceding supplier screen's stronger rules and 0.0508 mm
mask expansion. The custom footprint's fabrication outline uses the part's
3.81 × 2.54 mm maximum body projection, with 0.8 mm holes and 1.6 mm pads.
Native courtyard DRC passes for the nominal footprints. Socket bodies and
assembly access are not represented.

## Actual power pins and ground connectivity

TI's current SN74AHCT244 datasheet identifies VCC as pin 20 and GND as pin 10.
Pins 1 and 19 are enable inputs, despite their being tied to ground here.
The DIP footprint places its supply pins about 24.10 mm apart diagonally;
a single small capacitor cannot sit immediately beside both pins.

`analyze.py` records VCC-feed distance and capacitor-to-actual-GND-pin distance
separately. On both copper layers, each capacitor ground pad overlaps its
filled ground and shares a connected ground-copper component with the IC's
pin 10. The analysis uses filled polygons, ground tracks, ground vias and
inscribed pad circles. Filling drill centers for component-membership tests
does not infer an impedance; the surrounding copper annuli carry current.

10,170 P3 point-containment results are checked against native KiCad polygon
queries. The P2 comparison also rechecks its archived native samples.
Signal lengths and opposite-layer ground-fill centerline coverage are
unchanged. Capacitance, current distribution, return-loop inductance, rail
droop and clock jitter are not extracted by these geometric checks.

## Exact-part evidence and remaining fit conditions

Five manufacturer PDFs are archived with hashes, URLs and retrieval times:
the exact KEMET spec sheet, GoldMax X7R family sheet, TI SN74AHCT244 sheet,
TI's decoupling-layout training notes and a TI mechanical drawing. Rendered
capacitor, pinout, power-recommendation and mechanical pages are retained.

The capacitor's maximum lead diameter is 0.61 mm. The candidate supplier's
published finished-hole tolerance gives a 0.7365 mm minimum for a 0.8 mm hole,
leaving 0.1265 mm diametral clearance. The part's lead pitch is 2.54 ±0.78 mm.
Even with perfectly centered holes, the maximum unformed pitch error exceeds
the available clearance. Lead forming or another package needs assembly
qualification. Hole-position tolerances reduce the available fit margin
further; they are not silently assumed to cancel.

The capacitance rating is measured at 1 kHz and 1 Vrms. X7R temperature
classification, ±10% nominal tolerance and the sheet's aging figure do not
bound the installed capacitance under DC bias or qualify ESR/ESL. Manufacturer
simulation curves are labelled typical simulations, not specifications.

The TI `mpdi096` PDF retrieved from the N0020A search has N0020A text metadata
but visually labels the drawing NFH0020A, with N20A Rev G in its footer.
Its exact applicability to the selected SN74AHCT244N package is unresolved.
The pinout is established separately by the device datasheet. This experiment
does not claim full package or socket fit qualification.

## Checkers and CAM

Five saved native omissions remove each local feed and each replacement
backbone via. All five fail the explicit intent contract; four produce native
DRC connectivity failures. The C2 parallel-feed omission passes DRC as expected.
Three further geometry mutations test a capacitor net remap, narrowed feed
and moved original signal endpoint. All are rejected.

An initial fault runner hit a KiCad/SWIG lifetime failure when repeatedly
destroying and loading boards in one interpreter. Native mutations now run
in individual subprocesses. The failed log is retained, along with the final
passing evidence. This was a harness issue, not a DRC result.

`cam.py` exports seven Gerber layers and plated/nonplated Excellon files. It
uses an archived copy of the earlier independently fault-tested parser/checker
to verify 101 plated holes, 188 tracks, 202 copper flashes, 180 mask openings,
the four-edge outline and both ground-fill polygons. Both polygon symmetric
differences are zero. Drill coordinates use KiCad's 0.001 mm quantization;
Gerbers use 0.000001 mm. Flash position/dimensions are checked, not full aperture
shape equivalence. Files are offline previews, with no supplier upload.

## Reproduction

From the repository root:

```sh
python3 Verification/build/cd1-decoupling/prepare.py
"$AUDIT_PYTHON" Verification/build/cd1-decoupling/extract.py
"$KICAD_PYTHON" Verification/build/cd1-decoupling/generate.py
"$KICAD_PYTHON" Verification/build/cd1-decoupling/export_geometry.py
"$AUDIT_PYTHON" Verification/build/cd1-decoupling/analyze.py
"$KICAD_PYTHON" Verification/build/cd1-decoupling/check.py
"$AUDIT_PYTHON" Verification/build/cd1-decoupling/cam.py
"$AUDIT_PYTHON" Verification/build/cd1-decoupling/plot.py
python3 Verification/build/cd1-decoupling/publish.py
python3 Verification/build/cd1-decoupling/verify_publication.py
NODE_PATH="$PLAYWRIGHT_NODE_PATH" node Verification/build/cd1-decoupling/browser_check.cjs
```

Use KiCad's bundled Python for `KICAD_PYTHON`. `AUDIT_PYTHON` uses the versions
in `requirements.txt`. Rebuilding native boards assigns fresh UUIDs to added
items; subsequent geometry, fault and CAM stages must be rerun together.

This is a placement/connectivity candidate. Physical decoupling effectiveness,
lead forming, sockets, bulk capacitance, supply distribution and load bounds
remain open. Milestone acceptance is unchanged.

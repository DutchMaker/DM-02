# CD1 cross-section capacitance screen

This experiment adds a numerical electrostatic model of finite copper and
same-layer ground to the earlier thin isolated-microstrip sensitivity. It
uses the P2 root-network lengths as equivalent uniform-line lengths. It does
not extract the capacitance of the actual routed board.

## Numerical method

`field.py` solves div(epsilon grad V) = 0 on a graded rectangular nodal grid.
Every conductor edge and dielectric interface is an explicit grid coordinate.
The finite-volume network uses epsilon times dual-face length divided by
edge length as its per-unit-length conductance. Relative permittivity is
integrated arithmetically across a horizontal dual face and harmonically
along a vertical edge. The potential of the signal is 1 V; all ground
conductors are 0 V. Unknown nodal potentials are solved with SciPy's sparse
direct solver.

Signal charge is summed from the discrete fluxes. Capacitance is independently
reconstructed from the field energy, and those two values must agree. Free
node residual, charge balance and the maximum principle are checked. These
checks test the discrete solve; they do not by themselves bound spatial
discretization error.

Coordinates are in millimeters, consistently for face and edge lengths.
Their ratio is dimensionless, so epsilon0 supplies F/m of extrusion length.
Conversion from F/m to pF/mm multiplies by 1e9. Uniform scaling of all geometry
must preserve capacitance per unit length and is separately tested.

The numerical outer box is grounded. This approximates infinity only after
checking domain sensitivity. The production cases use x = -12 to +12 mm and
an upper wall at +12 mm. Backed cases have a physical ground plane at -1.53 mm.
The infinite-substrate benchmark instead has a lower numerical wall at
-12 mm. No solder coating is present.

## Independent comparisons and convergence

Two parallel-plate fixtures use insulated lateral walls:

- Uniform dielectric: C' = epsilon0 * er * width / height.
- Series dielectric layers: C' = epsilon0 * width / sum(height_i / er_i).

The CPW comparison is a zero-thickness strip and coplanar grounds over an
infinitely deep substrate. From Qucs technical documentation, equations
12.2 and 12.3:

```text
k = W / (W + 2*gap)
C' = 2 * epsilon0 * (1 + er) * K(k) / K(sqrt(1-k*k))
```

SciPy `ellipk` takes the parameter m=k², not the modulus k. The reference HTML
is archived as `cpw-reference.html` and retains its original equations in
LaTeX comments. It was retrieved from
https://qucs.sourceforge.net/tech/node86.html on 2026-11-15.

Air and er=4.8 cases use three successively finer graded meshes. The finest
thin-CPW comparison differs by 0.3031% from the analytical value. This is a
comparison for that benchmark, not a global error bound for every geometry.

The 35 µm, er=4.8 backed case also uses three meshes and three box extents.
The final mesh step changes C' by 0.2008%; the 6 to 12 mm box change is
0.0161%. Both 35 and 70 µm cases get an additional finer-mesh check; their
changes are below 0.065%. Separate 24 and 48 mm box checks examine the
isolated-line comparison. All raw numerical diagnostics are retained.

Six regression checks cover scale invariance, incomplete/nonpositive
dielectrics, empty ground intersections, an exact ground-gap fixture and
exclusion of ground on the opposite ray. The survey's first empty-intersection
attempt was corrected before publication. An initial layered-plate fixture
also exposed almost-duplicate floating-point grid coordinates; grid generation
now merges coordinates at 1e-12 mm resolution before solving.

## Hypothetical cross-sections

The trace width is 0.25 mm, matching P2 signal tracks. The 0.25 mm same-layer
ground gap, 1.53 mm dielectric height, substrate er values 4.0 and 4.8, and
copper thicknesses 0, 0.035 and 0.070 mm are model inputs. They are not a
qualified supplier stackup. Holding dielectric height fixed isolates the
copper-thickness effect; the hypothetical total board thickness consequently
need not equal the stored board's nominal 1.6 mm.

Every coplanar case has infinitely wide, continuous coplanar grounds and a
continuous lower ground plane, approximated by the tested finite domain.
The model is translation-invariant along the trace. It omits pads, via
barrels, bends, branches, ground discontinuities, coating, neighboring signal
and supply conductors, device impedance, and mutual/dynamic coupling.

Multiplying C' by a root's summed routed length produces an equivalent
uniform-line scenario. It is neither an upper nor lower bound for the PCB.
Its remaining 5 pF margin is only arithmetic under those assumptions.
The separate 50 pF device characterization condition must not be confused
with that trace allocation. Receiver input capacitance comes from the
archived PC parts specification; XML pin types provide receiver counts.

## Actual-layout survey

`survey.py` samples each root segment at no more than 0.2 mm spacing. Samples
within 0.5 mm of a track endpoint or 1.5 mm of any pad/via center are excluded
from the straight-section subset. Two perpendicular rays intersect the
actual same-layer ground fill, recording the first ground gap and contiguous
span. The comparison screen asks for a 0.249–0.300 mm gap and at least 0.5 mm
of ground on each side, plus ground fill under the opposite-layer center.

These are analyst-selected survey criteria, not field-solver boundary
conditions. Sample weights sum to the actual network track lengths, but a
matching sample does not prove a continuous coplanar corridor or validate
the uniform model there. The survey is intentionally not used to integrate
capacitance over the board.

## Reproduction

Use the existing geometry Python environment with the versions in
`requirements.txt`. From the repository root:

```sh
python3 Verification/build/cd1-capacitance/prepare.py
"$AUDIT_PYTHON" Verification/build/cd1-capacitance/experiment.py
"$AUDIT_PYTHON" Verification/build/cd1-capacitance/survey.py
"$AUDIT_PYTHON" Verification/build/cd1-capacitance/checks.py
"$AUDIT_PYTHON" Verification/build/cd1-capacitance/domain_check.py
"$AUDIT_PYTHON" Verification/build/cd1-capacitance/plots.py
python3 Verification/build/cd1-capacitance/publish.py
python3 Verification/build/cd1-capacitance/verify_publication.py
NODE_PATH="$PLAYWRIGHT_NODE_PATH" node Verification/build/cd1-capacitance/browser_check.cjs
```

The report remains conditional. It changes no schematic, PCB, timing model,
functional acceptance result or fabrication gate. The earlier publications
are checked by hash before this page is built.

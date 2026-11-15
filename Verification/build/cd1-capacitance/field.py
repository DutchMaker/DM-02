"""2-D electrostatic finite-volume solver on a graded rectangular grid.

All coordinates use one consistent length unit (here mm). Conductance per
unit extrusion length is epsilon * dual-face-length / edge-length, so the
coordinate scale cancels and capacitance is returned in F/m and pF/mm.
This solver is for translationally invariant cross-sections, not a 3-D PCB.
"""
import math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.special import ellipk

EPS0 = 8.8541878128e-12


def graded_axis(anchors, minimum=.0025, growth=1.15):
    """Include every conductor/dielectric interface exactly; grade inward."""
    anchors = sorted(set(anchors))
    points = set(anchors)
    for left, right in zip(anchors, anchors[1:]):
        half = (right-left)/2
        distance, step = 0., minimum
        while distance+step < half:
            distance += step
            points.update((left+distance, right-distance))
            step *= growth
        points.add((left+right)/2)
    return np.unique(np.round(np.array(sorted(points)), 12))


def integral(a, b, layers, inverse=False):
    """Integrate epsilon_r, or its reciprocal, across horizontal layers."""
    result = np.zeros_like(np.asarray(a, dtype=float))
    covered = np.zeros_like(result)
    for low, high, er in layers:
        assert er > 0
        length = np.maximum(0., np.minimum(b, high)-np.maximum(a, low))
        result += length / er if inverse else length * er
        covered += length
    assert np.allclose(covered, np.asarray(b)-np.asarray(a), rtol=1e-12, atol=1e-12)
    return result


def solve(x, y, layers, fixed, values, signal, keep_potential=False):
    """Solve div(epsilon grad V)=0 with Dirichlet conductor masks.

    Unspecified outer boundaries have zero normal flux. Cross-section callers
    explicitly ground their outer box, and test the box-size sensitivity.
    """
    nx, ny = len(x), len(y)
    assert fixed.shape == values.shape == signal.shape == (ny, nx)
    assert np.all(fixed[signal]) and np.all(values[signal] == 1.)
    assert np.all(values[fixed & ~signal] == 0.)
    assert np.any(signal) and np.any(fixed & ~signal)
    assert np.all(np.diff(x) > 0) and np.all(np.diff(y) > 0)
    xfaces = np.r_[x[0], (x[:-1]+x[1:])/2, x[-1]]
    yfaces = np.r_[y[0], (y[:-1]+y[1:])/2, y[-1]]
    xwidth = np.diff(xfaces)
    horizontal_er_height = integral(yfaces[:-1], yfaces[1:], layers)
    vertical_resistance_height = integral(y[:-1], y[1:], layers, inverse=True)
    ids = np.arange(nx*ny).reshape(ny, nx)
    u = np.r_[ids[:, :-1].ravel(), ids[:-1, :].ravel()]
    v = np.r_[ids[:, 1:].ravel(), ids[1:, :].ravel()]
    g = np.r_[(horizontal_er_height[:, None]/np.diff(x)[None, :]).ravel(),
              (xwidth[None, :]/vertical_resistance_height[:, None]).ravel()]
    laplacian = coo_matrix((np.r_[g, g, -g, -g],
                           (np.r_[u, v, u, v], np.r_[u, v, v, u])), shape=(nx*ny, nx*ny)).tocsr()
    free = np.flatnonzero(~fixed.ravel())
    known = np.flatnonzero(fixed.ravel())
    potential = values.ravel().copy()
    matrix = laplacian[free][:, free]
    rhs = -laplacian[free][:, known] @ potential[known]
    potential[free] = spsolve(matrix, rhs)
    residual = laplacian @ potential
    cap = EPS0 * residual[signal.ravel()].sum()
    energy_cap = EPS0 * np.sum(g*(potential[u]-potential[v])**2)
    ground_charge = EPS0 * residual[fixed.ravel() & ~signal.ravel()].sum()
    residual_relative = np.max(np.abs(residual[free])) / np.max(laplacian.diagonal())
    energy_relative = abs(energy_cap/cap-1)
    charge_balance_relative = abs((cap+ground_charge)/cap)
    assert cap > 0 and np.isfinite(cap)
    assert potential.min() >= -1e-10 and potential.max() <= 1+1e-10
    assert residual_relative < 1e-10 and energy_relative < 1e-8 and charge_balance_relative < 1e-8
    result = dict(capacitance_f_per_m=float(cap), capacitance_pf_per_mm=float(cap*1e9),
                  energy_capacitance_pf_per_mm=float(energy_cap*1e9),
                  energy_charge_relative_difference=float(energy_relative),
                  charge_balance_relative_error=float(charge_balance_relative),
                  scaled_free_residual=float(residual_relative),
                  nodes=nx*ny, unknowns=len(free), nx=nx, ny=ny)
    if keep_potential:
        return result, potential.reshape(ny, nx)
    return result


def cross_section(width=.25, gap=.25, height=1.53, er=4.8, thickness=.035,
                  coplanar=True, backed=True, box=6., minimum=.0025, growth=1.15, keep_potential=False):
    assert width > 0 and gap > 0 and height > 0 and er >= 1 and thickness >= 0
    assert box > max(height, width/2+gap, thickness)
    edge = width/2+gap
    x = graded_axis([-box, -edge, -width/2, 0., width/2, edge, box], minimum, growth)
    bottom = -height if backed else -box
    y = graded_axis([bottom, 0., thickness, box], minimum, growth)
    xx, yy = np.meshgrid(x, y)
    copper_height = (yy >= -1e-12) & (yy <= thickness+1e-12)
    signal = (np.abs(xx) <= width/2+1e-12) & copper_height
    ground = np.zeros_like(signal)
    if coplanar:
        ground |= (np.abs(xx) >= edge-1e-12) & copper_height
    # Grounded finite box. A backed line has a real ground boundary at -h;
    # other exterior walls are numerical truncations, varied in experiments.
    ground[[0, -1], :] = True
    ground[:, [0, -1]] = True
    fixed = ground | signal
    values = np.zeros(xx.shape)
    values[signal] = 1.
    layers = [(bottom, 0., er), (0., box, 1.)]
    solved = solve(x, y, layers, fixed, values, signal, keep_potential)
    if keep_potential:
        result, potential = solved
        return result, x, y, potential
    return solved


def infinite_thin_cpw(width, gap, er):
    """Qucs CPW eqs. 12.2/12.3; K takes modulus, scipy takes m=k^2."""
    k = width/(width+2*gap)
    return float(2*EPS0*(1+er)*ellipk(k*k)/ellipk(1-k*k)*1e9)


def plate_benchmark(layers):
    """Width 2 mm, separation 1 mm; insulated sides, exact series dielectric."""
    x = np.linspace(0., 2., 31)
    y = np.unique(np.round(np.r_[np.linspace(0., 1., 41), [v for a,b,_ in layers for v in (a,b)]], 12))
    fixed = np.zeros((len(y), len(x)), dtype=bool)
    fixed[[0,-1], :] = True
    signal = np.zeros_like(fixed)
    signal[-1, :] = True
    values = signal.astype(float)
    result = solve(x, y, layers, fixed, values, signal)
    exact = EPS0*2/sum((b-a)/er for a,b,er in layers)*1e9
    assert abs(result['capacitance_pf_per_mm']/exact-1) < 1e-10
    return dict(**result, analytical_pf_per_mm=exact,
                relative_error=abs(result['capacitance_pf_per_mm']/exact-1), layers=layers)

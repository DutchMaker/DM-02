"""Extra mesh checks near the allocation boundary and survey regressions."""
from pathlib import Path
import importlib.util
import json
from shapely.geometry import Polygon, box
from field import cross_section, integral
from survey import ground_ray

HERE = Path(__file__).resolve().parent


def main():
    numerical = json.loads((HERE / 'numerical-results.json').read_text())
    checks = []
    refinements = []
    for thickness, kind in ((.035, 'coplanar-35um'), (.070, 'coplanar-70um')):
        previous = next(r for r in numerical['scenarios'] if r['kind'] == kind and r['parameters']['er'] == 4.8)
        fine = cross_section(thickness=thickness, er=4.8, box=12., minimum=.000625, growth=1.08)
        difference = abs(fine['capacitance_pf_per_mm']/previous['capacitance_pf_per_mm']-1)
        assert difference < .003
        refinements.append(dict(kind=kind, parameters=dict(thickness=thickness, er=4.8, box=12., minimum=.000625, growth=1.08),
                                previous_pf_per_mm=previous['capacitance_pf_per_mm'], relative_change=difference, **fine))
        print(kind, 'extra fine', fine['capacitance_pf_per_mm'], 'pF/mm, relative change', difference, flush=True)
    a = cross_section(box=3., minimum=.005, growth=1.2)
    b = cross_section(width=.75, gap=.75, height=4.59, thickness=.105,
                      box=9., minimum=.015, growth=1.2)
    scale_error = abs(a['capacitance_pf_per_mm']/b['capacitance_pf_per_mm']-1)
    assert scale_error < 1e-8
    checks.append(dict(name='uniform geometric scale invariance', passed=True, relative_error=scale_error))
    for name, layers in [('dielectric gap', [(0.,.4,2.),(.6,1.,4.)]),
                         ('nonpositive dielectric', [(0.,1.,0.)])]:
        try:
            integral(0.,1.,layers)
        except AssertionError:
            checks.append(dict(name=name+' rejected', passed=True))
        else:
            raise AssertionError(name+' escaped dielectric validation')
    spec = importlib.util.spec_from_file_location('helper', HERE / 'sources/p1-audit.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert ground_ray([0,0], [1,0], Polygon(), .25, helper) is None
    checks.append(dict(name='empty ground ray', passed=True))
    result = ground_ray([0,0], [1,0], box(.375,-1,1.375,1), .25, helper)
    assert abs(result['gap_from_trace_edge_mm']-.25) < 1e-12
    assert abs(result['contiguous_ground_span_mm']-1.) < 1e-12
    checks.append(dict(name='analytical ground gap and span', passed=True))
    assert ground_ray([0,0], [-1,0], box(.375,-1,1.375,1), .25, helper) is None
    checks.append(dict(name='ground on opposite ray excluded', passed=True))
    (HERE / 'checks.json').write_text(json.dumps(dict(passed=True, tests=checks, extra_mesh_refinements=refinements), indent=2)+'\n')
    print(len(checks), 'regression checks and two extra mesh refinements pass', flush=True)


if __name__ == '__main__':
    main()

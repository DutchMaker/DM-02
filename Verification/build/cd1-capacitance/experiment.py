"""Benchmark and run hypothetical CD1 cross-sections; no PCB extraction."""
from pathlib import Path
import importlib.util
import json
import time
import numpy as np
import scipy
from field import cross_section, infinite_thin_cpw, plate_benchmark

HERE = Path(__file__).resolve().parent


def run(label, **parameters):
    start = time.perf_counter()
    result = cross_section(**parameters)
    row = dict(label=label, parameters=parameters, seconds=time.perf_counter()-start, **result)
    print(label, f'{result["capacitance_pf_per_mm"]:.8f} pF/mm; {result["nodes"]} nodes', flush=True)
    return row


def main():
    plates = [plate_benchmark([(0.,1.,4.)]), plate_benchmark([(0.,.6,2.),(.6,1.,4.)])]
    grids = [dict(minimum=.005, growth=1.18), dict(minimum=.0025, growth=1.12), dict(minimum=.00125, growth=1.08)]
    benchmarks = []
    for er in (1., 4.8):
        exact = infinite_thin_cpw(.25, .25, er)
        for index, mesh in enumerate(grids):
            result = run(f'thin-infinite-cpw-er{er}-mesh{index}', er=er, thickness=0., backed=False, box=12., **mesh)
            result.update(analytical_pf_per_mm=exact, relative_error=abs(result['capacitance_pf_per_mm']/exact-1))
            benchmarks.append(result)
        assert benchmarks[-1]['relative_error'] < .005
        assert benchmarks[-1]['relative_error'] < benchmarks[-2]['relative_error'] < benchmarks[-3]['relative_error']
    convergence = []
    for index, mesh in enumerate(grids):
        convergence.append(run(f'backed-cpw-35um-mesh{index}', er=4.8, thickness=.035, box=12., **mesh))
    mesh_change = abs(convergence[-1]['capacitance_pf_per_mm']/convergence[-2]['capacitance_pf_per_mm']-1)
    assert mesh_change < .005
    domains = [run(f'backed-cpw-35um-box{box}', er=4.8, thickness=.035, box=box, **grids[-1]) for box in (3.,6.)]
    domains.append(convergence[-1])
    domain_change = abs(domains[-1]['capacitance_pf_per_mm']/domains[-2]['capacitance_pf_per_mm']-1)
    assert domain_change < .005
    scenarios = []
    for er in (4., 4.8):
        for kind, copper, thickness in [('isolated-thin', False, 0.), ('coplanar-thin', True, 0.),
                                       ('coplanar-35um', True, .035), ('coplanar-70um', True, .070)]:
            if er == 4.8 and kind == 'coplanar-35um':
                row = dict(convergence[-1], label=f'{kind}-er{er}')
            else:
                row = run(f'{kind}-er{er}', er=er, thickness=thickness, coplanar=copper,
                          backed=True, box=12., **grids[-1])
            row['kind'] = kind
            scenarios.append(row)
    # Check the isolated-line limit against the prior, independent formula.
    spec = importlib.util.spec_from_file_location('previous_audit', HERE / 'sources/p1-audit.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    for row in scenarios:
        if row['kind'] != 'isolated-thin':
            continue
        reference = previous.microstrip(.25, 1.53, row['parameters']['er'])['capacitance_pf_per_mm']
        row['schneider_pf_per_mm'] = reference
        row['schneider_relative_difference'] = abs(row['capacitance_pf_per_mm']/reference-1)
        assert row['schneider_relative_difference'] < .03
    # Export one numerical field map for reproducible engineering plots.
    example, x, y, potential = cross_section(er=4.8, thickness=.035, box=12.,
                                            **grids[-1], keep_potential=True)
    np.savez_compressed(HERE / 'field-map.npz', x=x, y=y, potential=potential)
    result = dict(status='numerical checks pass; hypothetical 2-D cross-sections only',
                  numpy_version=np.__version__, scipy_version=scipy.__version__,
                  parallel_plate_benchmarks=plates, infinite_cpw_benchmarks=benchmarks,
                  finite_copper_mesh_convergence=convergence, finite_copper_domain_convergence=domains,
                  final_mesh_relative_change=mesh_change, final_domain_relative_change=domain_change,
                  scenarios=scenarios, example_field=example,
                  assumptions=dict(width_mm=.25, gap_mm=.25, substrate_height_mm=1.53,
                                   substrate_er=[4.,4.8], copper_thickness_mm=[0.,.035,.070],
                                   air_er=1., grounded_outer_box_half_width_mm=12.),
                  fabrication_ready=False)
    (HERE / 'numerical-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Numerical checks complete; mesh change', mesh_change, 'box change', domain_change, flush=True)


if __name__ == '__main__':
    main()

"""Publish checked cross-section sensitivities, without PCB qualification."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import html
import json

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    numerical, survey, checks, domains = [read(n) for n in ('numerical-results.json','survey.json','checks.json','domain-check.json')]
    assert checks['passed'] and domains['passed'] and all(r['passed'] for r in checks['tests'])
    assert len(numerical['scenarios']) == 8 and len(survey['roots']) == 6
    for row in read('sources/manifest.json')['files']:
        assert sha(HERE / 'sources' / row['file']) == sha(HERE.parents[2] / row['source']) == row['sha256']
    assert survey['board_sha256'] == sha(HERE / 'sources/CD1-P2-routed.kicad_pcb')
    preserved = []
    for name in ('cd1-layout','cd1-electrical','cd1-stitching'):
        folder = HERE.parent / name
        manifest = json.loads((folder/'manifest.json').read_text())
        for file, entry in manifest['files'].items():
            assert sha(folder/file) == entry['sha256'], file
        preserved.append(dict(directory=name, files=len(manifest['files'])))
    comparisons = []
    for model in numerical['scenarios']:
        for root in survey['roots']:
            trace = root['length_mm']*model['capacitance_pf_per_mm']
            comparisons.append(dict(scenario=model['label'], net=root['net'], equivalent_trace_pf=trace,
                                    trace_allocation_remaining_pf=root['original_trace_allocation_pf']-trace,
                                    declared_receiver_pf=root['receiver_capacitance_pf'],
                                    equivalent_total_load_pf=root['receiver_capacitance_pf']+trace,
                                    driver_condition_pf=root['driver_characterization_load_pf']))
    longest = max(survey['roots'],key=lambda r:r['length_mm'])
    selected = next(r for r in numerical['scenarios'] if r['kind']=='coplanar-35um' and r['parameters']['er']==4.8)
    isolated = next(r for r in numerical['scenarios'] if r['kind']=='isolated-thin' and r['parameters']['er']==4.8)
    thin_pf = isolated['capacitance_pf_per_mm']*longest['length_mm']
    finite_pf = selected['capacitance_pf_per_mm']*longest['length_mm']
    benchmark_error = max(r['relative_error'] for r in numerical['infinite_cpw_benchmarks'] if r['label'].endswith('mesh2'))
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(), status='conditional cross-section study; actual board capacitance unqualified',
                   board_sha256=survey['board_sha256'], longest_root=longest['net'], longest_root_length_mm=longest['length_mm'],
                   isolated_thin_equivalent_pf=thin_pf, coplanar_35um_equivalent_pf=finite_pf,
                   coplanar_35um_trace_allocation_remaining_pf=5-finite_pf,
                   finest_thin_cpw_benchmark_relative_error=benchmark_error,
                   representative_mesh_relative_change=numerical['final_mesh_relative_change'],
                   representative_box_relative_change=numerical['final_domain_relative_change'],
                   isolated_box_total_relative_change=domains['production_to_largest_relative_change'],
                   scenarios=8, root_networks=6, equivalent_load_rows=len(comparisons), survey_samples=len(survey['samples']),
                   extra_regression_checks=len(checks['tests']), extra_mesh_checks=len(checks['extra_mesh_refinements']),
                   comparisons=comparisons, preserved_publications=preserved,
                   source_reference=dict(url='https://qucs.sourceforge.net/tech/node86.html', equations=['12.2','12.3'],
                                         retrieved_at='2026-11-15', sha256=sha(HERE/'cpw-reference.html')),
                   fabrication_ready=False, actual_board_capacitance_qualified=False, acceptance_changed=False)
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    scenario_rows = ''.join(f'<tr><td>{html.escape(r["kind"])}</td><td>{r["parameters"]["er"]:.1f}</td>'
                            f'<td>{r["capacitance_pf_per_mm"]:.6f}</td><td>{r["capacitance_pf_per_mm"]*longest["length_mm"]:.3f}</td>'
                            f'<td>{5-r["capacitance_pf_per_mm"]*longest["length_mm"]:.3f}</td></tr>' for r in numerical['scenarios'])
    root_rows = ''.join(f'<tr><td>{r["net"]}</td><td>{r["length_mm"]:.3f}</td><td>{r["receiver_count"]}</td>'
                        f'<td>{r["length_mm"]*selected["capacitance_pf_per_mm"]:.3f}</td>'
                        f'<td>{r["receiver_capacitance_pf"]+r["length_mm"]*selected["capacitance_pf_per_mm"]:.3f}</td></tr>' for r in survey['roots'])
    survey_rows = ''.join(f'<tr><td>{r["net"]}</td><td>{r["length_mm"]:.3f}</td><td>{r["eligible_sample_weight_mm"]:.3f}</td>'
                          f'<td>{r["close_coplanar_and_opposite_sample_weight_mm"]:.3f}</td></tr>' for r in survey['roots'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · CD1 capacitance screen</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.notice{{color:#ffd082}}.pass{{color:#88e2b0}}figure{{margin:18px 0}}img{{display:block;width:100%;height:auto;background:#fff;border-radius:8px}}figcaption{{padding:8px 0}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}@media(max-width:650px){{section{{padding:14px}}th,td{{padding:6px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../cd1-stitching/">P2 ground stitches</a> · <a href="../cd1-electrical/">Earlier return-path and microstrip screen</a></nav>
<h1>CD1 capacitance screen</h1>
<p>A numerical cross-section model adds same-layer ground and finite copper thickness to the earlier isolated, zero-thickness trace model. For a uniform line as long as ROOT3_1, the assumed εr = 4.8, 35 µm copper case increases trace capacitance from {thin_pf:.3f} to {finite_pf:.3f} pF. That leaves {5-finite_pf:.3f} pF of the existing 5 pF trace allocation.</p>
<p class="pass">The solver matches two analytical parallel-plate fixtures and agrees with the thin coplanar reference within {100*benchmark_error:.4f}% at the finest comparison mesh. Mesh, boundary-size, energy and charge checks pass.</p>
<p class="notice">These are hypothetical uniform cross-sections. Actual P2 capacitance remains unqualified: pads, via barrels, coating, bends, branches, discontinuous ground and neighboring conductors are omitted. No timing or fabrication gate changes.</p>
<section><h2>Finite copper and adjacent ground</h2><figure><a href="field.svg"><img src="field.svg" alt="Numerical electrostatic potential around a hypothetical coplanar trace above a ground plane"></a><figcaption>Stored numerical potential field for the 35 µm, εr = 4.8 case. The display is cropped; the numerical domain is larger.</figcaption></figure>
<p>The model assumes a 0.25 mm trace, 0.25 mm gaps to continuous same-layer grounds, and a ground plane 1.53 mm below the substrate surface. Substrate permittivity and copper thickness are scenario inputs. The stored board thickness does not qualify those values.</p>
<table id="scenarios"><thead><tr><th>Cross-section</th><th>εr</th><th>C′ (pF/mm)</th><th>Equivalent longest root (pF)</th><th>5 pF remaining (pF)</th></tr></thead><tbody>{scenario_rows}</tbody></table>
<figure><a href="sensitivity.svg"><img src="sensitivity.svg" alt="Eight hypothetical capacitance scenarios for the 67.523 millimeter longest root, compared with a 5 picofarad allocation"></a><figcaption>Network length is used only for equivalent uniform-line comparisons.</figcaption></figure>
<p>The 70 µm, εr = 4.8 case leaves about 0.067 pF in this arithmetic comparison. All eight scenarios remain below 5 pF, but none supplies an upper bound for the actual board.</p></section>
<section><h2>Numerical verification</h2>
<ul><li>Uniform and series-dielectric parallel plates match their analytical capacitances to floating-point precision.</li>
<li>Six thin-CPW runs cover air and εr = 4.8 at three meshes. Error decreases with refinement to {100*benchmark_error:.4f}%.</li>
<li>The representative 35 µm case changes {100*numerical['final_mesh_relative_change']:.4f}% at the final production mesh step and {100*numerical['final_domain_relative_change']:.4f}% when the box expands from 6 to 12 mm.</li>
<li>Additional 35 and 70 µm refinements change results by less than 0.065%. The isolated-line comparison changes {100*domains['production_to_largest_relative_change']:.4f}% between 12 and 48 mm boxes.</li>
<li>Six regression checks cover dimensional scaling, dielectric validation and survey intersections.</li></ul>
<p>Charge, energy and matrix residual checks validate the discrete solve. Benchmark agreement and observed convergence do not establish a rigorous error bound for every geometry.</p>
<nav><a href="numerical-results.json">Numerical results</a> · <a href="checks.json">Extra refinements and regressions</a> · <a href="domain-check.json">Isolated-line boundary check</a> · <a href="field-map.npz">Numerical field array</a> · <a href="https://qucs.sourceforge.net/tech/node86.html">Analytical CPW reference</a> · <a href="cpw-reference.html" download>Archived reference HTML</a></nav></section>
<section><h2>Trace allocation versus receiver loading</h2><p>The 5 pF trace allocation is separate from the AHCT244's 50 pF characterization load. This table adds declared 10 pF receiver inputs to the uniform 35 µm, εr = 4.8 trace scenario. It does not replace the existing conditional timing model.</p>
<table id="roots"><thead><tr><th>Root</th><th>Length (mm)</th><th>Receivers</th><th>Equivalent trace (pF)</th><th>Equivalent total (pF)</th></tr></thead><tbody>{root_rows}</tbody></table>
<p>All listed equivalent totals are below 50 pF. Actual pad, via, coupling and stackup contributions still need qualification.</p></section>
<section><h2>How much of P2 resembles this cross-section?</h2><p>A survey of {len(survey['samples']):,} transverse sample locations records actual nearby ground fills. Samples near segment ends, pads or vias are excluded from the straight-section subset. Matching neighborhoods need near ground on both sides and opposite-layer ground at the signal center.</p>
<table id="survey"><thead><tr><th>Root</th><th>Full length (mm)</th><th>Straight-section sample weight (mm)</th><th>Matching-neighborhood weight (mm)</th></tr></thead><tbody>{survey_rows}</tbody></table>
<p>For ROOT3_1, matching samples represent 34.096 mm of its 67.523 mm routed length under this screen. These weights are sampled context, not certified continuous corridors. They are not used to integrate a PCB capacitance estimate.</p>
<nav><a href="survey.json">All survey points and root pin counts</a> · <a href="sources/source.xml">Native schematic netlist</a></nav></section>
<section><h2>Reproduction and next physical inputs</h2><p>A supplier stackup with dielectric and finished-copper limits is needed before these scenarios can become a physical loading review. A complete model must also include coating, pads, barrels, nearby conductors and three-dimensional discontinuities.</p>
<p>All 191 previously published layout artifact hashes remain valid. This study changes no circuit, routing or normal acceptance source.</p>
<nav><a href="README.md">Method, limitations and reproduction</a> · <a href="summary.json">48 equivalent-load comparisons</a> · <a href="field.py">Field solver</a> · <a href="experiment.py">Benchmarks and scenarios</a> · <a href="checks.py">Regression and refinement checks</a> · <a href="survey.py">Geometry survey</a> · <a href="requirements.txt">Dependencies</a> · <a href="sources/manifest.json">Input hashes</a> · <a href="manifest.json">Published hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main></html>'''
    (HERE / 'index.html').write_text(page)
    excluded = {'manifest.json','remote-validation.json','browser-check.json'}
    files = {str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
             if p.is_file() and (p.parent!=HERE or p.name not in excluded) and '__pycache__' not in p.parts
             and p.suffix not in ('.pyc','.png','.kicad_prl')}
    (HERE / 'manifest.json').write_text(json.dumps(dict(created_at=summary['created_at'],files=files),indent=2)+'\n')
    print(f'Published {len(files)} files, 8 scenarios, 48 equivalent loads; prior 191 artifact hashes preserved')


if __name__ == '__main__':
    main()

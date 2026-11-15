"""Render the verified CD1-P0/P1 comparison and its artifact manifest."""
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
    before, after = read('analysis.json'), read('candidate/analysis.json')
    change, validation, tests = read('candidate/change.json'), read('candidate/validation.json'), read('test-results.json')
    assert tests['passed'] and tests['tests'] == 12
    assert validation['passed'] and validation['drc_violations'] == validation['unconnected_items'] == 0
    assert all(row['detected'] for row in validation['faults'])
    assert change['missing_branch_via_detected'] and change['original_unchanged']
    assert change['original_sha256'] == before['board_sha256']
    assert change['candidate_sha256'] == after['board_sha256'] == validation['board_sha256']
    assert sha(HERE / 'candidate/CD1-P1-routed.kicad_pcb') == after['board_sha256']
    assert sha(HERE.parent / 'cd1-layout/CD1-P0-routed.kicad_pcb') == before['board_sha256']
    comparisons = []
    for name, row in before['net_geometry'].items():
        current = after['net_geometry'][name]
        assert current['uncovered_centerline_mm'] <= row['uncovered_centerline_mm'] + 1e-6
        comparisons.append(dict(net=name, before_length_mm=row['length_mm'], after_length_mm=current['length_mm'],
                                before_gap_mm=row['uncovered_centerline_mm'], after_gap_mm=current['uncovered_centerline_mm']))
    root = '/ROOT2_0'
    original, refined = before['net_geometry'][root], after['net_geometry'][root]
    assert abs(original['length_mm'] - refined['length_mm'] - change['removed_track_length_mm']) < 1e-6
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(), status='bounded geometry improvement verified',
                   original_board_sha256=before['board_sha256'], candidate_board_sha256=after['board_sha256'],
                   native_polygon_points=before['native_containment_checks']+after['native_containment_checks'],
                   focused_tests=tests['tests'], native_faults_detected=len(validation['faults'])+1,
                   total_signal_gap_before_mm=before['uncovered_centerline_mm'],
                   total_signal_gap_after_mm=after['uncovered_centerline_mm'], net_comparison=comparisons,
                   fabrication_ready=False, milestone_acceptance_changed=False,
                   model_reference=dict(url='https://qucs.sourceforge.net/tech/node75.html',
                                        retrieved_at='2026-11-15', equations=['11.3', '11.14'],
                                        archived_html_sha256=sha(HERE / 'microstrip-reference.html')),
                   remaining=['Qualify stackup, total capacitance, edge rates and return impedance.',
                              'Review 4.116 mm separation from the added signal via to the nearest ground barrel.',
                              'Review decoupling with the real ground pins and exact capacitors.',
                              'Qualify connectors, mounting, power distribution, oscillator and reset.'])
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    rows = ''.join(f'<tr><td>{html.escape(r["net"])}</td><td>{r["before_length_mm"]:.3f} → {r["after_length_mm"]:.3f}</td>'
                   f'<td>{r["before_gap_mm"]:.3f} → {r["after_gap_mm"]:.3f}</td></tr>' for r in comparisons)
    sensitivity = ''.join(f'<tr><td>{s["height_mm"]:.2f}</td><td>{s["relative_permittivity"]:.1f}</td>'
                          f'<td>{s["capacitance_pf_per_mm"]:.4f}</td><td>{max(r["hypothetical_trace_pf"] for r in s["root_nets"]):.3f}</td></tr>'
                          for s in after['sensitivity'])
    figures = ''.join(f'<figure><a href="{prefix}{layer}-return.svg"><img src="{prefix}{layer}-return.svg" '
                      f'alt="{version} {layer} signal routes over opposite-layer ground fill"></a>'
                      f'<figcaption>{version}: {layer} signals, opposite-layer GND fill.</figcaption></figure>'
                      for version, prefix in [('P0', ''), ('P1', 'candidate/')]
                      for layer in ('front', 'back'))
    scope = ''.join(f'<li>{html.escape(text)}</li>' for text in after['scope'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · CD1 return paths and P1 refinement</title>
<link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.notice{{color:#ffd082}}.pass{{color:#88e2b0}}.plots{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0;min-width:0}}img{{display:block;width:100%;height:auto;background:#fff;border-radius:8px}}figcaption{{padding:8px 0}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}@media(max-width:650px){{.plots{{grid-template-columns:1fr}}section{{padding:14px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../cd1-layout/">Original CD1-P0 routing trial</a> · <a href="../experiments/2026-11-15-integrated-complete/">Completed functional evidence</a></nav>
<h1>CD1 return paths and P1 refinement</h1>
<p>ROOT2_0 doubled back over itself on opposite copper layers. P1 replaces one 8.848 mm front-copper segment with a 0.8 mm through via at the branch junction. The other 185 track segments and all 90 pad-to-net assignments are preserved.</p>
<p class="pass">P1 passes configured native KiCad DRC with zero violations and zero unconnected items. Four injected faults are detected, including removal of the new branch via. Twelve audit tests pass.</p>
<p class="notice">P1 remains a routing experiment. The electrical model, exact parts and physical prototype still require qualification; milestone acceptance is unchanged.</p>
<section><h2>Measured improvement</h2>
<table id="comparison"><thead><tr><th>ROOT2_0</th><th>P0</th><th>P1</th></tr></thead><tbody>
<tr><td>Total routed length</td><td>{original['length_mm']:.3f} mm</td><td>{refined['length_mm']:.3f} mm</td></tr>
<tr><td>Centerline without opposite-layer GND fill</td><td>{original['uncovered_centerline_mm']:.3f} mm</td><td>{refined['uncovered_centerline_mm']:.3f} mm</td></tr>
<tr><td>Longest gap within one segment</td><td>{original['longest_segment_gap_mm']:.3f} mm</td><td>{refined['longest_segment_gap_mm']:.3f} mm</td></tr>
<tr><td>Board through vias</td><td>0</td><td>1</td></tr></tbody></table>
<p>Across all 26 signal nets, uncovered centerline falls from {before['uncovered_centerline_mm']:.3f} to {after['uncovered_centerline_mm']:.3f} mm. No other signal net's coverage worsens. The added via is 4.116 mm from the nearest ground-connected barrel, U3 pin 1. That is a measured separation; return impedance remains unknown.</p>
<nav><a href="candidate/CD1-P1-routed.kicad_pcb">P1 KiCad board</a> · <a href="candidate/CD1-P1-routed.kicad_dru">P1 rules</a> · <a href="candidate/change.json">Exact change record</a> · <a href="candidate/validation.json">P1 validation</a> · <a href="candidate/routed-drc.json">Native DRC</a> · <a href="candidate/mutations/missing-branch-via.json">Missing-via fault</a></nav></section>
<section><h2>Ground-fill projection</h2><p>Green shows filled ground copper on the opposite layer; blue shows signal centerlines. Red marks portions without opposite-layer GND fill. Both sides are viewed from the top. These plots retain signal-pad antipads and thermal clearances; ground tracks and pads outside filled zones are omitted.</p>
<div class="plots">{figures}</div>
<p>The audit clips routes against the stored KiCad fill polygons. GEOS converts KiCad's zero-width polygon bridges into area polygons without changing area. All {summary['native_polygon_points']:,} native point-containment comparisons agree. Continuous clipping detects even a 0.010 mm slot in the test fixture.</p>
<p>A green projection does not establish a continuous low-inductance return to the driver. Ground-corridor width, layer transitions and nearby signal coupling need further analysis.</p></section>
<section><h2>Stackup and trace loading</h2>
<p>The board declares 1.6 mm thickness but has no qualified manufacturer stackup. The table applies a zero-thickness, isolated microstrip formula to hypothetical dielectric heights and permittivities. Every row assumes a solid infinite ground plane. These values are sensitivity calculations, not extracted capacitance for P0 or P1.</p>
<table id="sensitivity"><thead><tr><th>Dielectric height (mm)</th><th>Relative permittivity</th><th>Trace pF/mm</th><th>Longest root trace (pF)</th></tr></thead><tbody>{sensitivity}</tbody></table>
<p>The existing local trace allocation is 5 pF. At 0.20 mm dielectric height, even this simplified model gives 5.951–7.009 pF for the 67.523 mm ROOT3_1 network. A closer plane therefore needs a renewed loading budget. The 1.53 mm scenarios leave numerical headroom, but omit copper thickness, solder mask, same-layer ground, pads, connectors and coupling; they cannot qualify the board.</p>
<nav><a href="model-notes.md">Equations, assumptions and reproduction</a> · <a href="https://qucs.sourceforge.net/tech/node75.html">Qucs technical reference, equations 11.3 and 11.14</a></nav></section>
<section><h2>Decoupling and layer changes</h2><p>Each 100 nF capacitor is 4.000 mm from its buffer's VCC pad center. Its ground pad is 29.677 mm from the buffer's actual ground pad, pin 10. Grounded enable pins 1 and 19 are not the chip's supply-ground pin. These are geometric distances; a routed power loop and its inductance have not been extracted.</p>
<p>P0 has eight signal pad-center layer transitions. P1 has seven plus the new via. Existing transitions are 5.080–10.160 mm from the nearest ground barrel. Exact capacitors, power routing and local return paths still need review.</p></section>
<section><h2>All signal nets</h2><table id="nets"><thead><tr><th>Net</th><th>Copper length P0 → P1 (mm)</th><th>Uncovered centerline P0 → P1 (mm)</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Evidence and reproduction</h2><p>The original board and its published evidence remain intact. This page contains separate P0 and P1 audits, the targeted refinement script and focused regression results.</p>
<nav><a href="summary.json">Comparison summary</a> · <a href="analysis.json">P0 audit</a> · <a href="candidate/analysis.json">P1 audit</a> · <a href="geometry.json">P0 native geometry</a> · <a href="candidate/geometry.json">P1 native geometry</a> · <a href="export_geometry.py">KiCad exporter</a> · <a href="analyze.py">Geometry and sensitivity audit</a> · <a href="refine.py">P1 refinement</a> · <a href="test_analysis.py">Audit tests</a> · <a href="test-results.json">12 test results</a> · <a href="manifest.json">Artifact hashes</a> · <a href="remote-validation.json">Remote hash checks</a></nav>
<details><summary>Exact audit scope</summary><ul>{scope}</ul></details></section></main></html>'''
    (HERE / 'index.html').write_text(page)
    excluded = {'manifest.json', 'remote-validation.json', 'browser-check.json'}
    files = {str(path.relative_to(HERE)): dict(bytes=path.stat().st_size, sha256=sha(path))
             for path in sorted(HERE.rglob('*')) if path.is_file() and path.name not in excluded
             and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.png', '.kicad_prl')}
    (HERE / 'manifest.json').write_text(json.dumps(dict(created_at=summary['created_at'], files=files), indent=2)+'\n')
    print(f'Published {len(files)} files, {len(comparisons)} net rows, eight sensitivity scenarios')


if __name__ == '__main__':
    main()

"""Publish source-backed process, CAM and coating evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import html
import json

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
def esc(value):return html.escape(str(value))


def main():
    facts,screen,cam,coating,rf,cf=[read(name) for name in ('supplier-facts.json','screen.json','cam-audit.json',
        'coating-results.json','rule-fault-checks.json','cam-file-fault-checks.json')]
    assert cam['passed'] and coating['passed'] and rf['passed'] and cf['passed']
    assert screen['drc_violations']==screen['unconnected_items']==screen['drc_exit']==0
    board=HERE/'CD1-P2-SCREEN-NOT-FOR-FAB.kicad_pcb'
    assert sha(board)==screen['screen_sha256']==read('native-cam-geometry.json')['board_sha256']
    manifest=read('sources/manifest.json')
    for row in manifest['remote']+manifest['local']:
        assert sha(HERE/'sources'/row['file'])==row['sha256'],row['file']
        if 'source' in row:assert sha(HERE.parents[2]/row['source'])==row['sha256'],row['source']
    preserved=[]
    for folder in ('cd1-layout','cd1-electrical','cd1-stitching','cd1-capacitance'):
        old=HERE.parent/folder
        files=json.loads((old/'manifest.json').read_text())['files']
        for name,row in files.items():assert sha(old/name)==row['sha256'],(folder,name)
        preserved.append(dict(directory=folder,files_verified=len(files)))
    roots=read('sources/survey.json')['roots']
    equivalents=[dict(scenario=s['name'],root=r['net'],equivalent_trace_pf=s['capacitance_pf_per_mm']*r['length_mm'],
        equivalent_total_pf=s['capacitance_pf_per_mm']*r['length_mm']+r['receiver_capacitance_pf'])
        for s in coating['scenarios'] for r in roots]
    exceeded=[s for s in coating['scenarios'] if s['allocation_remaining_pf']<0]
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),
        status='Configured DRC and CAM parity pass; hypothetical coating scenarios exceed trace allocation',
        source_sha256=screen['source_sha256'],screen_sha256=screen['screen_sha256'],supplier_publications=8,sourced_facts=24,
        drc_violations=0,unconnected_items=0,drills=99,tracks=185,outline_mm=[60,70],mask_openings=180,
        native_rule_fault_checks=len(rf['checks']),parsed_record_fault_checks=len(cam['parsed_record_fault_checks']),
        serialized_cam_fault_checks=len(cf['checks']),sensitivity_scenarios=len(coating['scenarios']),
        longest_root_scenarios_over_5pf=len(exceeded),equivalent_loads=equivalents,
        maximum_equivalent_receiver_inclusive_pf=max(r['equivalent_total_pf'] for r in equivalents),
        preserved_publications=preserved,acceptance_changed=False,fabrication_ready=False,
        actual_board_capacitance_qualified=False,supplier_selected=False,uploaded=False,ordered=False)
    summary['dashboard_index_sha256']=sha(HERE.parents[1]/'dashboard/index.html')
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    nominal=next(s for s in coating['scenarios'] if s['name']=='service nominal, uncoated')
    coated=next(s for s in coating['scenarios'] if s['name']=='hypothetical flat coating 0.01524 mm')
    factrows=''.join(f'<tr><td>{esc(r["name"])}</td><td>{esc(r["value"])}</td><td>{esc(r["kind"])}</td>'
        f'<td><a href="sources/{esc(r["source"])}">{esc(r["source"])}</a></td></tr>' for r in facts['facts'])
    rulerows=''.join(f'<tr><td>{esc(r["setting"])}</td><td>{r["before"]:.4f}</td><td>{r["after"]:.4f}</td></tr>' for r in screen['rule_changes'])
    holerows=''.join(f'<tr><td>{r["nominal_mm"]:.3f}</td><td>{r["count"]}</td><td>{r["published_finished_min_mm"]:.4f}</td><td>{r["published_finished_max_mm"]:.4f}</td></tr>' for r in cam['drill_size_groups'])
    modelrows=''.join(f'<tr><td>{esc(r["name"])}</td><td>{r["capacitance_pf_per_mm"]:.6f}</td><td>{r["longest_root_equivalent_pf"]:.3f}</td><td class="{"notice" if r["allocation_remaining_pf"]<0 else "pass"}">{r["allocation_remaining_pf"]:.3f}</td></tr>' for r in coating['scenarios'])
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · CD1 fabrication screen</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1120px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.notice{{color:#ffd082}}.pass{{color:#88e2b0}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #304156;overflow-wrap:anywhere}}figure{{margin:15px 0}}img{{display:block;width:100%;height:auto;border-radius:8px;background:#fff}}.views{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}figcaption{{padding:8px 0}}code{{overflow-wrap:anywhere}}@media(max-width:700px){{.views{{grid-template-columns:1fr}}section{{padding:13px}}td,th{{padding:6px;font-size:13px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../cd1-stitching/">P2 routing</a> · <a href="../cd1-capacitance/">Earlier capacitance benchmarks</a></nav>
<h1>CD1 fabrication screen</h1>
<p class="pass">The supplier-rule copy passes configured KiCad DRC. Independent CAM parsing matches 99 plated holes, 185 tracks, both filled-ground polygons and the 60 × 70 mm outline.</p>
<p class="notice">Coating remains a loading concern. A hypothetical flat coating raises the longest-root equivalent from {nominal['longest_root_equivalent_pf']:.3f} to {coated['longest_root_equivalent_pf']:.3f} pF using service-nominal substrate values. The existing trace allocation is 5 pF. Actual purple coating and full-board capacitance remain unqualified.</p>
<p>Scope: local OSH Park two-layer screening candidate. Preview files are labelled <strong>NOT FOR FABRICATION</strong>. Milestones remain 3/5, 2/5 and 8/9.</p>
<section><h2>Offline CAM previews</h2><div class="views"><figure><a href="top-cam.svg"><img src="top-cam.svg" alt="Top-side offline Gerber and drill preview of the CD1 screening copy"></a><figcaption>Top, rendered from Gerbers and Excellon.</figcaption></figure>
<figure><a href="bottom-cam.svg"><img src="bottom-cam.svg" alt="Bottom-side offline Gerber and drill preview of the CD1 screening copy"></a><figcaption>Bottom, viewed from underneath. Both images are local previews.</figcaption></figure></div>
<p>The separate screening copy adds 0.0508 mm global mask expansion. Its 90 pads, 185 tracks and nine vias preserve P2 geometry and net assignments. Both native ground-fill polygons have zero symmetric-difference area against the independently parsed Gerber regions.</p>
<ul><li>99 plated holes in three size groups; no nonplated holes.</li><li>198 copper pad/via flashes and 180 mask openings match positions and bounding dimensions across both sides.</li><li>Mask-opening bounding boxes give a minimum separation of {cam['minimum_mask_web_bbox_lower_bound_mm']:.4f} mm, above the supplier's 0.1016 mm web minimum.</li><li>Nine parsed-record faults and four serialized CAM faults are detected.</li></ul>
<p>Metric Excellon rounds one via centre by 0.0002 mm per axis. The check accounts for the exported 0.001 mm grid. Gerber comparisons retain 0.000001 mm. Plating flags are checked against KiCad's file-function headers before parsing.</p>
<nav><a href="cam-audit.json">CAM audit and parser warnings</a> · <a href="native-cam-geometry.json">Native reference geometry</a> · <a href="cam-file-fault-checks.json">Serialized CAM faults</a> · <a href="audit_cam.py">Independent checker</a> · <a href="drill-report.txt">KiCad drill report</a></nav></section>
<section><h2>Stricter native rules</h2><p>Zero configured violations and zero unconnected items. The original stricter custom rules remain in place; the screening copy strengthens connection-width, via-diameter and text constraints. Five ignored checks remain visible in the raw report.</p>
<table id="rules"><thead><tr><th>Project setting</th><th>Before (mm)</th><th>Screen (mm)</th></tr></thead><tbody>{rulerows}</tbody></table>
<p>Four physical mutations trigger the expected DRC diagnostics: narrow track/connection, undersized via/annulus, undersized drill and thin silkscreen text.</p>
<nav><a href="screen-drc.json">Native DRC report</a> · <a href="screen.json">Rule changes and export commands</a> · <a href="rule-fault-checks.json">Native fault checks</a> · <a href="screen.py">Screen generator</a></nav></section>
<section><h2>Published drill tolerances and component fit</h2><p>The two-layer service page gives 0.0508 mm maximum hole-position tolerance. The dedicated drill page gives ±0.0635 mm. This screen retains both statements and uses the larger figure for sensitivity; the supplier discrepancy remains unresolved.</p>
<table id="holes"><thead><tr><th>Nominal hole (mm)</th><th>Count</th><th>Published finished min (mm)</th><th>Published finished max (mm)</th></tr></thead><tbody>{holerows}</tbody></table>
<p>Exact lead/socket dimensions are still needed to establish assembly fit. The supplier says its 0.127 mm nominal annular-ring design minimum already includes fabrication tolerances; it is compared directly with CAD geometry.</p></section>
<section><h2>Coating and dielectric sensitivity</h2><p>The uncoated service-nominal case uses 1.524 mm core, εr = 4.5 and 0.03556 mm copper. The hypothetical coated cases fill the coplanar gaps with a flat dielectric slab extending above the copper by the named coating thickness. They use εr = 4.5 for that coating.</p>
<table id="scenarios"><thead><tr><th>Uniform cross-section scenario</th><th>C′ (pF/mm)</th><th>Longest-root equivalent (pF)</th><th>5 pF remaining (pF)</th></tr></thead><tbody>{modelrows}</tbody></table>
<p class="notice">{len(exceeded)} of nine scenarios exceed the 5 pF trace allocation for an equivalent 67.523 mm uniform line. These values neither extract nor bound actual P2 capacitance. Pads, barrels, neighboring conductors and three-dimensional discontinuities remain omitted.</p>
<p>The supplier links a green/dark-green PSR-4000BN datasheet, dated March 2005, for its purple service. Its internal 1 MHz dielectric test does not qualify the actual purple coating. Copper tolerance and coating profile are also unspecified.</p>
<p>The 5 pF trace allocation is separate from the device's 50 pF characterization condition. Across all 54 equivalent root/scenario comparisons, the largest receiver-inclusive value is {summary['maximum_equivalent_receiver_inclusive_pf']:.3f} pF. The normal conditional timing model is unchanged.</p>
<p>The representative coated case changes {100*coating['checks']['final_mesh_relative_change']:.4f}% at the final mesh refinement and {100*coating['checks']['box_relative_change']:.4f}% when the numerical box expands from 12 to 24 mm. Energy, charge, residual and unity-permittivity coating checks pass.</p>
<nav><a href="coating-results.json">Nine scenarios and convergence checks</a> · <a href="coating.py">Coating model</a> · <a href="summary.json">54 equivalent-load comparisons</a></nav></section>
<section><h2>Source-backed process facts</h2><p>Eight supplier publications are archived with retrieval times and hashes. Values below distinguish nominal inputs, design minimums and material test results.</p>
<table id="facts"><thead><tr><th>Fact</th><th>Value</th><th>Meaning</th><th>Archived source</th></tr></thead><tbody>{factrows}</tbody></table>
<p>The service's 4.5 dielectric figure is at 10 MHz. The linked laminate sheet gives typical 4.8 at 1 MHz and 4.6 at 1 GHz, with a specification figure of ≤5.4. This is incomplete frequency-dependent material evidence.</p>
<nav><a href="supplier-facts.json">Full facts, quotes and unresolved applicability</a> · <a href="sources/manifest.json">Source hashes</a></nav></section>
<section><h2>Reproduction and remaining gates</h2><p>All 223 earlier layout and capacitance artifact hashes remain valid. Exact component fit, clock loading, power/decoupling layout, connector mapping and physical qualification still block fabrication. P2's one unmet 2 mm return-via target also remains open.</p>
<p>The supplier guide names KiCad 9.x; local exports use 10.0.8. These offline checks do not establish supplier preview acceptance. No supplier has been selected or sent files.</p>
<nav><a href="README.md">Method and reproduction</a> · <a href="requirements.txt">Dependencies</a> · <a href="manifest.json">Published artifact hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','cam-plots.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.kicad_prl')
        and not (p.parent==HERE and p.name in excluded)}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=summary['created_at'],files=files),indent=2)+'\n')
    print('Published',len(files),'files;',len(exceeded),'of 9 longest-root scenarios exceed 5 pF; 223 prior hashes preserved')


if __name__=='__main__':main()

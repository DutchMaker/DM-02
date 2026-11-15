"""Publish the independently checked P3 placement/connectivity candidate."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import html
import json

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())


def main():
    generation,analysis,checks,cam=[read(n) for n in ('generation.json','analysis.json','checks.json','cam-audit.json')]
    digest=sha(HERE/'CD1-P3-decoupling.kicad_pcb')
    assert all(r['board_sha256']==digest for r in (generation,analysis,checks,cam))
    assert analysis['passed'] and checks['passed'] and cam['passed']
    assert generation['violations']==generation['unconnected']==generation['drc_exit']==0
    for row in read('sources/manifest.json')['remote']+read('sources/manifest.json')['local']:
        assert sha(HERE/'sources'/row['file'])==row['sha256']
        if 'source' in row:assert sha(HERE.parents[2]/row['source'])==row['sha256']
    preserved=[]
    for name in ('cd1-layout','cd1-electrical','cd1-stitching','cd1-capacitance','cd1-fabrication-screen'):
        folder=HERE.parent/name;files=json.loads((folder/'manifest.json').read_text())['files']
        for file,row in files.items():assert sha(folder/file)==row['sha256'],(name,file)
        preserved.append(dict(directory=name,files_verified=len(files)))
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),status='P3 geometry and connectivity pass; physical decoupling and assembly remain unqualified',
        board_sha256=digest,source_sha256=generation['source_sha256'],tracks=188,vias=11,pads=90,drills=101,
        original_tracks_preserved=185,original_vias_preserved=9,native_xml_pad_net_parity=True,
        direct_feed_lengths_mm=[r['after']['vcc_distance_mm'] for r in analysis['decoupling']],feed_width_mm=.5,
        native_containment_checks=analysis['native_containment_checks'],
        native_faults=len(checks['native_faults']),native_faults_drc_detected=sum(r['drc_detected'] for r in checks['native_faults']),
        geometry_faults=len(checks['geometry_faults']),signal_ground_coverage_change_mm=sum(r['change_mm'] for r in analysis['signal_ground_coverage']),
        preserved_publications=preserved,dashboard_index_sha256=sha(HERE.parents[1]/'dashboard/index.html'),
        capacitor='C315C104K5R5TA',full_unformed_lead_pitch_fit=False,physical_decoupling_qualified=False,
        acceptance_changed=False,fabrication_ready=False)
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    rows=''.join(f'<tr><td>{r["capacitor"]} / {r["ic"]}</td><td>{r["before"]["vcc_distance_mm"]:.3f}</td><td>{r["after"]["vcc_distance_mm"]:.3f}</td><td>{r["before"]["ground_pin_distance_mm"]:.3f} → {r["after"]["ground_pin_distance_mm"]:.3f}</td></tr>' for r in analysis['decoupling'])
    faults=''.join(f'<tr><td>{html.escape(r["fault"])}</td><td>Detected</td><td>{"Detected" if r["drc_detected"] else "Passes: parallel DC path"}</td></tr>' for r in checks['native_faults'])
    sources=''.join(f'<li><a href="sources/{r["file"]}">{html.escape(r["file"])}</a></li>' for r in read('sources/manifest.json')['remote'])
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · P3 decoupling placement</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}figure{{margin:16px 0}}img{{display:block;width:100%;height:auto;border-radius:8px;background:#fff}}figcaption{{padding:8px 0}}.views{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #304156;overflow-wrap:anywhere}}@media(max-width:700px){{.views{{grid-template-columns:1fr}}section{{padding:13px}}td,th{{padding:6px;font-size:13px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../cd1-stitching/">P2 source layout</a> · <a href="../cd1-fabrication-screen/">Supplier and coating screen</a></nav>
<h1>P3 decoupling placement</h1><p class="pass">The three capacitor feeds are now 3.000, 3.000 and 3.905 mm long at 0.50 mm width, versus 4 mm at 0.25 mm in P2. Configured native DRC passes; all original signal routing is preserved.</p>
<p class="notice">This is a placement/connectivity experiment. The exact capacitor's lead-pitch tolerance requires an assembly decision, and physical decoupling effectiveness remains unqualified. Milestones remain 3/5, 2/5 and 8/9.</p>
<section><h2>Shorter, wider local supply feeds</h2><figure><a href="feeds.svg"><img src="feeds.svg" alt="Three P3 layout details showing capacitor supply feeds and the actual IC power pins"></a><figcaption>Actual native front copper. The capacitor outlines use the manufacturer's maximum body projection at nominal lead placement.</figcaption></figure>
<table id="feeds"><thead><tr><th>Capacitor / IC</th><th>P2 VCC distance (mm)</th><th>P3 direct feed (mm)</th><th>Distance to actual GND pin, P2 → P3 (mm)</th></tr></thead><tbody>{rows}</tbody></table>
<p>VCC is pin 20; GND is pin 10. The DIP footprint places them about 24.10 mm apart. Grounded enable pins 1 and 19 are not supply-ground pins. The analysis checks each capacitor's ground contact into the fill and its shared copper component with pin 10 on both layers.</p>
<p>P3 preserves all 185 original tracks and nine vias. It adds three local supply tracks and two supply vias at the former C1/C2 VCC pad positions, where the capacitor barrels previously connected front and back supply tracks. Total: 188 tracks, eleven vias and 90 pads.</p>
<p>C2 also touches the retained backside supply backbone. Its front feed is a parallel connection. This affects how its fault test must be interpreted.</p>
<nav><a href="analysis.json">Geometry and fit analysis</a> · <a href="generation.json">Placement and copper changes</a> · <a href="geometry.json">Native geometry</a> · <a href="drc.json">Configured DRC report</a></nav></section>
<section><h2>Final board previews</h2><div class="views"><figure><a href="top-cam.svg"><img src="top-cam.svg" alt="Top-side Gerber and Excellon preview for CD1-P3"></a><figcaption>Top, offline preview. All three capacitors use the nominal 2.54 mm footprint.</figcaption></figure><figure><a href="bottom-cam.svg"><img src="bottom-cam.svg" alt="Bottom-side Gerber and Excellon preview for CD1-P3"></a><figcaption>Bottom, viewed from underneath. Colours are renderer defaults.</figcaption></figure></div>
<p>Independent CAM parsing matches 101 plated holes, 188 tracks, 202 copper flashes, 180 mask openings and the 60 × 70 mm outline. Both exported ground-fill polygons have zero symmetric-difference area against native geometry.</p>
<p>The native-to-polygon comparison checks 10,170 P3 points. Original signal lengths and opposite-layer ground-fill centreline coverage are unchanged. These checks do not extract capacitance, return impedance or loop inductance.</p>
<nav><a href="cam-audit.json">CAM parity and parser warnings</a> · <a href="cam.py">CAM exporter/checker</a> · <a href="export_geometry.py">Native geometry exporter</a></nav></section>
<section><h2>Fault checks and the parallel-feed case</h2><table id="faults"><thead><tr><th>Saved PCB fault</th><th>Explicit intent check</th><th>Native DRC</th></tr></thead><tbody>{faults}</tbody></table>
<p>Removing C2's wide front feed leaves its backside DC connection intact. The intent checker still rejects the omission. Three further geometry mutations reject a capacitor net remap, a narrowed feed and a moved original signal endpoint.</p>
<p>The first C3 placement crossed existing ground and ME1_PH2 copper. Moving C3 upward 2.5 mm removed those conflicts. The rejected board and report are retained.</p>
<nav><a href="checks.json">All eight fault results</a> · <a href="check.py">Fault runner</a> · <a href="rejected-first-placement/drc.json">Rejected first-placement DRC</a></nav></section>
<section><h2>Exact capacitor: nominal fit has conditions</h2><p>The candidate is KEMET C315C104K5R5TA: 100 nF, ±10%, 50 V, X7R. Its body maximum is 3.81 × 2.54 × 3.14 mm; lead pitch is 2.54 ±0.78 mm and maximum lead diameter is 0.61 mm.</p>
<p>With a 0.8 mm hole and the archived supplier's ±0.0635 mm finished-size tolerance, the minimum hole is 0.7365 mm. That leaves 0.1265 mm diametral clearance. Even before hole-position error, this cannot accommodate the full unformed lead-pitch tolerance.</p>
<p class="notice">Lead forming or another package needs qualification. The nominal footprint passes courtyard DRC, but socket bodies and assembly access remain unmodelled. Capacitance under DC bias, aging, ESR and ESL also remain open.</p>
<p>TI recommends a 0.1 µF bypass capacitor close to the power pin. Its device pinout establishes pins 20/10. A separately retrieved mechanical drawing has N0020A text metadata but visually reads NFH0020A/N20A Rev G; exact package applicability remains unresolved.</p>
<ul id="sources">{sources}</ul><nav><a href="sources/manifest.json">Source retrievals and hashes</a> · <a href="footprints/CD1-Experiment.pretty/C315C104K5R5TA.kicad_mod">Experimental capacitor footprint</a></nav></section>
<section><h2>Reproduction and remaining work</h2><p>All 366 previous published layout/capacitance/supplier artifact hashes remain valid. The normal functional report remains stale for ten sources, including the dashboard navigation update. Its completed archives and acceptance results remain intact.</p>
<p>Next physical gates include lead forming and sockets, bulk capacitance and supply distribution, dynamic decoupling, clock loading and bench measurements. P3 is labelled NOT FOR FABRICATION; no supplier upload or order has occurred.</p>
<nav><a href="README.md">Method and reproduction</a> · <a href="requirements.txt">Dependencies</a> · <a href="summary.json">Summary</a> · <a href="manifest.json">Published hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','feed-plot.png','cam-plots.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.kicad_prl') and not(p.parent==HERE and p.name in excluded)}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=summary['created_at'],files=files),indent=2)+'\n')
    print('Published',len(files),'files; all 366 earlier artifact hashes preserved')


if __name__=='__main__':main()

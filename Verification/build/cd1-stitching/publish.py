"""Publish the limited CD1-P2 ground-stitching result and evidence hashes."""
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
    analysis, change, validation = read('analysis.json'), read('change.json'), read('validation.json')
    assert analysis['passed_geometric_checks'] and analysis['targets_met'] == 7
    assert not analysis['fabrication_ready'] and validation['passed']
    assert analysis['board_sha256'] == change['candidate_sha256'] == validation['board_sha256'] == sha(HERE / 'CD1-P2-routed.kicad_pcb')
    assert change['wrong_net_mutation_persisted'] and change['wrong_net_stitch_drc_detected']
    assert all(r['detected'] for r in change['missing_stitch_mutations']+analysis['geometry_faults']+validation['faults'])
    source_rows = read('sources/manifest.json')['files']
    for row in source_rows:
        assert sha(HERE / 'sources' / row['file']) == row['sha256']
        assert sha(HERE.parents[2] / row['source']) == row['sha256']
    preserved = []
    for name in ('cd1-layout', 'cd1-electrical'):
        folder = HERE.parent / name
        manifest = json.loads((folder / 'manifest.json').read_text())
        for file, entry in manifest['files'].items():
            assert sha(folder / file) == entry['sha256'], file
        preserved.append(dict(directory=name, files_verified=len(manifest['files'])))
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(), status=analysis['status'],
                   board_sha256=analysis['board_sha256'], baseline_sha256=analysis['baseline_sha256'],
                   ground_vias_added=8, total_vias=9, tracks_preserved=185, pads_preserved=90,
                   targets_met=7, targets_total=8, target_mm=2., worst_reference_distance_mm=analysis['worst_after_mm'],
                   existing_fault_checks=3, stitch_intent_fault_checks=9, exported_geometry_fault_checks=11,
                   native_containment_checks=analysis['native_containment_checks'],
                   ground_via_layer_contacts=len(analysis['ground_via_contacts']),
                   preserved_publications=preserved, fabrication_ready=False, milestone_acceptance_changed=False)
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    rows = []
    for row in analysis['transitions']:
        label = row['id'] if len(row['id']) < 20 else 'ROOT2_0 signal via'
        state = 'Met' if row['target_met'] else 'Unmet'
        rows.append(f'<tr><td>{html.escape(label)}<br><small>{html.escape(row["net"])}</small></td><td>{row["before"]["distance_mm"]:.3f}</td><td>{row["after"]["distance_mm"]:.3f}</td><td>{state}</td></tr>')
    contacts = ''.join(f'<tr><td>{r["stitch"]}</td><td>{r["layer"]}</td><td>{r["center_to_fill_boundary_mm"]:.3f} mm</td></tr>' for r in analysis['ground_via_contacts'])
    scope = ''.join(f'<li>{html.escape(text)}</li>' for text in analysis['scope'])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · CD1-P2 ground stitching</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.notice{{color:#ffd082}}.pass{{color:#88e2b0}}.plots{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0;min-width:0}}img{{display:block;width:100%;height:auto;background:#fff;border-radius:8px}}figcaption{{padding:8px 0}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}@media(max-width:650px){{.plots{{grid-template-columns:1fr}}section{{padding:14px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../cd1-electrical/">P0/P1 return-path audit</a> · <a href="../experiments/2026-11-15-integrated-complete/">Completed functional evidence</a></nav>
<h1>CD1-P2 ground stitching</h1>
<p>Eight ground vias add local front-to-back ground connections beside CD1's eight signal layer transitions. The worst center-to-center distance from a signal transition to a ground barrel falls from 10.160 mm to 2.050 mm. All 185 signal/power/ground track segments, the existing signal via and all 90 pads are preserved.</p>
<p class="pass">Configured native KiCad DRC: zero violations and zero unconnected items. All eight ground vias contact filled ground on both copper layers. Signal routing and ground-fill projection are unchanged.</p>
<p class="notice">Limited result: seven of eight transitions meet the chosen 2.00 mm geometric target. U3 pin 4 remains at 2.050 mm. The target is an experimental placement criterion, not an electrical limit. Physical qualification and milestone acceptance remain open.</p>
<section><h2>Signal-to-ground-barrel distances</h2>
<table id="transitions"><thead><tr><th>Signal transition</th><th>P1 (mm)</th><th>P2 (mm)</th><th>2.00 mm target</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>The search uses a 0.05 mm grid and requires a 0.45 mm radius of existing filled ground on both sides around each proposed via center. New vias have 0.8 mm copper diameter and 0.4 mm drill. The last placement is the closest found within this bounded search; a different route or clearance screen could produce another result.</p>
<nav><a href="CD1-P2-routed.kicad_pcb">P2 KiCad board</a> · <a href="CD1-P2-routed.kicad_dru">Design rules</a> · <a href="source.kicad_sch">Source schematic</a> · <a href="plan.json">Placement plan</a> · <a href="change.json">Preserved geometry and fault results</a> · <a href="analysis.json">Measured comparison</a></nav></section>
<section><h2>Ground stitches and signal transitions</h2><p>Green shows ground fill on the displayed layer, blue shows signal tracks, and G1–G8 label the added ground vias. Dashed lines join signal transitions to their nearest ground barrels. The orange line marks the unmet 2.00 mm target. Both layers are viewed from the top.</p>
<div class="plots"><figure><a href="front-stitches.svg"><img src="front-stitches.svg" alt="P2 front copper ground stitching with eight labelled ground vias"></a><figcaption>Front copper and ground stitches.</figcaption></figure><figure><a href="back-stitches.svg"><img src="back-stitches.svg" alt="P2 back copper ground stitching with the U3 pin 4 target miss"></a><figcaption>Back copper, viewed through the board.</figcaption></figure></div>
<p>Filled-ground areas are geometrically identical to P1. P2 adds vertical connections through those areas. All {analysis['native_containment_checks']:,} native KiCad point comparisons agree with the polygon representation. This does not calculate return current, loop inductance or impedance.</p></section>
<section><h2>Fault checks</h2><p>The three existing checks detect an open clock net, a power short and a connector pin remap. Each of the eight new stitches is then removed in turn, saved and reloaded; the intent checker rejects every omission. The geometry checker independently detects all eight missing vias, a wrong net, a shifted position and a reduced copper diameter.</p>
<p>The persisted wrong-net stitch is rejected by both the intent checker and KiCad's <code>via_dangling</code> diagnostic. The test marks that mutated via as free: an ordinary via inherits its surrounding copper net when KiCad saves the board, which initially erased the intended fault. The final fixture explicitly verifies its saved 5 V assignment before DRC.</p>
<p>KiCad can describe the injected power short as either <code>shorting_items</code> or <code>tracks_crossing</code>. The checker accepts either only when the diagnostic identifies both 5 V and GND. The original published checker and its evidence are preserved.</p>
<nav><a href="validation.json">Native validation</a> · <a href="routed-drc.json">P2 DRC</a> · <a href="mutations/stitch-to-5v.json">Persisted wrong-net DRC</a> · <a href="mutations/power-short.json">Power-short DRC</a> · <a href="check_board.py">Native checker</a></nav></section>
<section><h2>Ground contact at each via</h2><p>Every new via center lies at least 0.45 mm inside the filled ground boundary on both layers. Its 0.4 mm copper radius therefore fits in that fill. These 16 geometric contact checks do not establish a frequency-dependent return path.</p>
<table id="contacts"><thead><tr><th>Stitch</th><th>Layer</th><th>Center to fill boundary</th></tr></thead><tbody>{contacts}</tbody></table></section>
<section><h2>Remaining physical work</h2><p>The added ground barrels change local capacitance and coupling. They do not close the loading, slew, clock-skew or EMI budgets. The eight additional 0.4 mm drills and 0.2 mm annuli also need review against the chosen fabrication process.</p>
<p>The stackup, power distribution, decoupling, exact passives/connectors, mounting, oscillator and reset remain open. In particular, the earlier 29.677 mm capacitor-to-device-ground pad distance is unchanged.</p></section>
<section><h2>Reproduction and preserved evidence</h2><p>All 47 P0 and 60 P0/P1 published artifact hashes still match. This experiment has its own source snapshot, board, measurements and publication manifest. No normal functional acceptance source was changed.</p>
<nav><a href="summary.json">Summary</a> · <a href="README.md">Method and reproduction</a> · <a href="sources/manifest.json">Archived input hashes</a> · <a href="prepare.py">Input snapshot</a> · <a href="plan.py">Placement search</a> · <a href="generate.py">Native board generation</a> · <a href="export.py">Native geometry export</a> · <a href="geometry.json">Exported geometry</a> · <a href="audit.py">Geometry audit</a> · <a href="manifest.json">Published hashes</a> · <a href="remote-validation.json">Remote verification</a></nav>
<details><summary>Exact audit scope</summary><ul>{scope}</ul></details></section></main></html>'''
    (HERE / 'index.html').write_text(page)
    excluded = {'manifest.json', 'remote-validation.json', 'browser-check.json'}
    files = {str(p.relative_to(HERE)): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(HERE.rglob('*'))
             if p.is_file() and (p.parent != HERE or p.name not in excluded)
             and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.png', '.kicad_prl')}
    (HERE / 'manifest.json').write_text(json.dumps(dict(created_at=summary['created_at'], files=files), indent=2)+'\n')
    print(f'Published {len(files)} files; 7/8 geometric targets; {sum(r["files_verified"] for r in preserved)} prior artifact hashes preserved')


if __name__ == '__main__':
    main()

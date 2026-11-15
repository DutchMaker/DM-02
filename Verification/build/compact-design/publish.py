"""Publish CP1 evidence without converting incomplete runs into acceptance."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv,hashlib,html,json,re,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(name):return json.loads((HERE/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def esc(x):return html.escape(str(x))

def main():
    s=importlib.util.spec_from_file_location('cp_sources',HERE/'source_manifest.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);sources=m.main()
    audit=read('audit.json');native=read('native-audit.json');physical=read('physical-review.json')
    state=read('verification-state.json');modules=read('module-check.json') if (HERE/'module-check.json').exists() else {}
    mar=read('mar-check.json') if (HERE/'mar-check.json').exists() else {}
    complete=bool(state.get('state')=='complete' and state.get('passed') is True and modules.get('passed') and modules.get('complete') and mar.get('passed') and mar.get('complete'))
    assert audit['all_ic_dip'] and audit['structure_passed'] and not audit['load_over_allocations']
    assert native['native_passed'] and physical['passed']
    for board,b in native['boards'].items():assert sha(HERE/'candidate/Circuits/KiCad/Compact/candidates'/f'{board}.sch')==b['source_sha256']
    assert read('workbook-validation.json')['sha256']==sha(HERE/'DM-02-compact-BOM.xlsx')
    previous=json.loads((HERE.parent/'experiments/2026-11-15-analog-retry-timeout/report.json').read_text())
    packages=read('packages.json');grouped=defaultdict(list)
    for p in packages:grouped[p['value'],p['footprint']].append(p['board']+':'+p['ref'])
    with (HERE/'candidate-BOM.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Part / value','Quantity','Footprint','References'])
        w.writerows([part,len(refs),fp,', '.join(refs)] for (part,fp),refs in sorted(grouped.items()))
    runs=state.get('runs',[])
    if not complete:
        # Show only finished result files whose current emitted model hashes still match.
        runs=[]
        for p in sorted((HERE/'candidate/Verification/build/compact').glob('c*/result.json')):
            x=json.loads(p.read_text())
            if not x.get('passed'):continue
            if not all(sha(p.parent/name)==h for name,h in x.get('model_hashes',{}).items()):continue
            if not all(sha(HERE/'candidate/Circuits/KiCad/Compact/candidates'/f'{name}.sch')==h for name,h in x.get('schematic_hashes',{}).items()):continue
            runs.append(x)
    counts=Counter(p['value'] for p in packages if p['ic'])
    boardcounts=Counter(p['board'] for p in packages if p['ic'])
    gaps=[]
    for x in runs:
        log=(HERE/x['log']).read_text()
        gaps += [float(v) for v in re.findall(r'minimum_disabled_ns=([0-9.]+)',log) if float(v)<1e9]
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),revision='CP1',
        state='digital-verification-complete' if complete else 'verification-in-progress',digital_verification_passed=complete,
        logic_memory_packages=audit['logic_memory_packages'],baseline_packages=288,saving=audit['saving'],
        reduction_fraction=audit['saving']/288,board_packages=dict(boardcounts),parts=dict(counts),
        all_logic_memory_dip=True,all_footprint_pads_through_hole=True,physical_packages=len(packages),
        native_boards=len(native['boards']),interconnect=read('interconnect-check.json'),
        clock_profiles=len(read('clock-check.json')['runs']),clock_profiles_passed=read('clock-check.json')['passed'],
        register_checks=read('register-check.json'),counter_full_rows_per_profile=131584,
        fault_checks=read('fault-check.json'),minimum_sampled_source_blank_ns=min(gaps) if gaps else None,
        completed_profiles=len(runs),runs=runs,module_checks=modules,mar_checks=mar,normal_sources_unchanged=sources['normal_sources_unchanged'],
        normal_milestones=previous['milestones'],normal_run_errors=[x['id'] for x in previous['checks'] if x['status']=='error'],
        milestone_scope='The unchanged normal requirements remain authoritative. CP1 is a separately verified staged redesign; its evidence is not silently promoted into the failed normal run.',
        physical_qualification=False,open_items=physical['open_items'],rom_programming_readback=False,
        timing_scope='Sampled digital timing and allocated loads at the conditional 4 MHz oscillator / 500 kHz microcycle target. Not a full-supply worst-case electrical guarantee.')
    write('summary.json',summary)
    byboard=''.join(f'<tr><td>{esc(k)}</td><td>{v}</td></tr>' for k,v in boardcounts.items())
    milestone_rows=''.join(f'<tr><td>{x["number"]}. {esc(x["title"])}</td><td>{x["passed"]}/{x["total"]}</td><td>{esc(", ".join(g["id"]+": "+g["status"] for g in x["gates"] if g["status"]!="pass"))}</td></tr>' for x in previous['milestones'][:3])
    openitems=''.join('<li>'+esc(x)+'</li>' for x in physical['open_items'])
    profiles=''.join(f'<tr><td>{esc(Path(x["log"]).parent.name)}</td><td>{x.get("passed")}</td><td><a href="{esc(x["log"])}">Log</a></td></tr>' for x in runs)
    status='Digital regression complete' if complete else 'ROM-booted graphics verification running'
    (HERE/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · CP1 compact DIP design</title><link rel="icon" href="data:,"><style>
:root{{color-scheme:dark}}body{{margin:24px auto;padding:0 16px;max-width:1100px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{width:100%;table-layout:fixed;border-collapse:collapse}}td,th{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}.note{{background:#253245;color:#ffd082;padding:16px}}h1{{line-height:1.2}}@media(max-width:650px){{table,tbody,tr,td{{display:block}}thead{{display:none}}td{{padding:8px 0}}td:first-child{{font-weight:bold}}}}</style>
<nav><a href="/">Dashboard</a> · <a href="../owned-inventory/">Owned inventory</a> · <a href="../dip-logic/">DL1 reference</a></nav>
<h1>192 ICs, down from 288</h1><p>CP1 saves 96 logic/memory packages (33⅓%). All logic and memories are DIP. Reset, fanout, counter and shared-bus support are included in the count.</p>
<p><a id="workbook" href="DM-02-compact-BOM.xlsx">Compact BOM and preserved inventory workbook</a> · <a href="candidate-BOM.csv">CSV BOM</a> · <a href="README.md">Circuit changes and reproduction</a></p>
<p id="state" class="note">{status}. Physical electrical qualification remains open. The target is a 4 MHz oscillator / 500 kHz microcycle; this is a staged candidate, not a fabrication release.</p>
<h2>Implemented reductions</h2><p>One M27C322 ALU ROM; one M27C1024 control ROM; owned W27C512 and UM61512 memories; enabled HC377 general registers; HCT191 SP/MAR counters; HCT273 snapshot consolidation; four buffered source groups and one shared DATA receiver. ACT175 count falls from 48 to 10, and 157 mux count from 84 to 29.</p>
<table><thead><tr><th>Board</th><th>Logic/memory ICs</th></tr></thead><tbody>{byboard}</tbody></table>
<h2>Verification</h2><p>Native KiCad connectivity matches on all {len(native['boards'])} boards. The simulated assembly matches 230 physical backplane net groups. All 497 package footprints have through-hole pads. No merged net exceeds its stated load allocation; those allocations still require physical qualification.</p>
<p>150 clock profiles; full 16-bit increment/decrement and every byte-load value; 4,096 register transfers per register profile; explicit counter timing and same-data bus-contention negative controls. The all-opcode profiles cover 227 opcodes in 454 cases each. See the completed profiles below and <a href="verification-state.json">serial-run state</a>.</p>
<p><a href="summary.json">Summary</a> · <a href="native-audit.json">Native parity</a> · <a href="interconnect-check.json">Backplane/HDL equivalence</a> · <a href="physical-review.json">Pins, pads and electrical boundary</a> · <a href="loads.json">Merged load allocations</a> · <a href="fault-check.json">Fault detections</a> · <a href="workbook-validation.json">Workbook checks</a></p>
<table><thead><tr><th>Completed profile</th><th>Passed</th><th>Evidence</th></tr></thead><tbody>{profiles}</tbody></table>
<h2>Milestones 1–3</h2><p>The latest normal run remains below. It timed out in the graphics demo, and boot was dependency-blocked. CP1 has separate evidence; these totals have not been inflated by transferring results between different designs.</p>
<table id="milestones"><thead><tr><th>Milestone</th><th>Accepted gates</th><th>Open gates</th></tr></thead><tbody>{milestone_rows}</tbody></table>
<p>Milestone 1 needs final sourcing and independent electrical review. Milestone 2 needs worst-case timing and physical clock/driver qualification. Milestone 3 needs error-free functional acceptance in the selected normal design and complete electrical integration.</p>
<h2>Remaining physical work</h2><ul>{openitems}</ul>
<h2>Sources and preservation</h2><p><a href="source-manifest.json">Candidate source hashes</a> · <a href="manifest.json">Publication hashes</a> · <a href="https://github.com/DutchMaker/DM-02">GitHub repository</a></p></html>''')
    # Only stable, deliberately published files. Large complete execution/native
    # artifacts are additionally preserved by the checksum-verified release.
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','verification.log','resume.log','module-check.log','mar-check.log'}
    selected=[p for p in HERE.iterdir() if p.is_file() and p.name not in excluded]
    selected += [HERE/'candidate'/name for name in sources['candidate_sources']]
    for directory in ('sources','footprints','programming-images'):
        selected += [p for p in (HERE/directory).rglob('*') if p.is_file()]
    for x in runs:
        selected.append(HERE/x['log']);selected.append((HERE/x['log']).parent/'result.json')
    for x in modules.get('runs',[])+mar.get('runs',[]):
        selected.append(HERE/x['log']);selected.append((HERE/x['log']).parent/'result.json')
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(selected))}
    write('manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),state=summary['state'],files=files))
    print('Published',len(files),'files;',summary['state'])
if __name__=='__main__':main()

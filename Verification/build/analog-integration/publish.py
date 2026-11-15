"""Publish tested normal-workflow analogue staging without changing a live run."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANDIDATE=HERE/'candidate'
sys.path.insert(0,str(CANDIDATE/'Verification'))
from dm02.analog_acceptance import evaluate
from dm02.loaded_output import input_hashes
from dm02.reporting import sources


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    tests=Path(sys.argv[1])
    log=tests.read_text()
    match=re.search(r'Ran (\d+) tests in .*\n\nOK\s*$',log)
    assert match and int(match[1])>=155,'Full staged regression suite has not passed'
    shutil.copyfile(tests,HERE/'tests.log')
    verification=CANDIDATE/'Verification'
    loaded=verification/'build/analog/loaded'
    acceptance=read(loaded/'acceptance.json')
    assert read(loaded/'state.json')['state']=='complete'
    assert acceptance['source_hashes']==input_hashes(),'Staged experiment inputs changed'
    requirements=read(verification/'requirements.json')
    checked=evaluate(read(verification/'analog-contract.json'),read(loaded/'experiment.json'),requirements)
    assert checked==acceptance['checks']
    evidence=read(verification/'build/analog/evidence.json')
    assert [(r['id'],r['status']) for r in evidence]==[('analog-rc','limited'),('analog','pass')]
    for row in evidence:
        for relative in row['artifacts']:
            assert (verification/'build'/relative).is_file(),relative
    baseline=read(ROOT/'Verification/build/report.json')['source_hashes']
    candidate=sources()
    assert all(p in candidate for p in baseline),'Staging deleted a normal input'
    changed={p:h for p,h in candidate.items() if baseline.get(p)!=h}
    assert changed and all(p.startswith('Verification/') for p in changed)
    assert candidate['Verification/requirements.json']==baseline['Verification/requirements.json']
    write(HERE/'source-manifest.json',dict(baseline=baseline,candidate=candidate,changed=changed))
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),status='validated-in-staging',
        normal_report_modified=False,tests=int(match[1]),changed_sources=len(changed),checks=checked,
        physical_clock_qualified=False,full_operating_envelope_qualified=False,
        model_sha256=acceptance['model_sha256'])
    write(HERE/'summary.json',summary)
    links=''.join(f'<li><a href="candidate/{html.escape(p,quote=True)}">{html.escape(p)}</a></li>' for p in changed)
    base='candidate/Verification/build/analog/loaded/'
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · analogue workflow integration</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:950px;margin:auto;padding:24px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}section{{padding:18px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}h1{{line-height:1.2}}</style>
<main><nav><a href="/">Full-system dashboard</a> · <a href="../pilot-transient/">Original accepted experiment</a> · <a href="../bom-inventory/">BOM and inventory</a></nav>
<h1>Analogue workflow integration</h1><p id="verdict" class="pass">The staged normal analogue workflow reproduced the accepted 5 V / 25 °C experiment: {checked['minimum_setup_margin_ns']:.3f} ns minimum margin, nine detected faults and {summary['tests']} passing regression tests.</p>
<p class="notice" id="scope">This checkpoint validates staging. The main dashboard will count the new gate after promotion and a fresh normal run.</p>
<section><h2>Fresh execution</h2><p>The stage rechecked the pinned TI model and official IBISCHK binary, ran syntax qualification and 12 DC comparisons, then reconstructed all eight manufacturer fixtures. Both 50 pF / 1 kΩ output transitions passed the unchanged 265–315 ns capture window. Four independent RLC integrations and two timestep refinements passed.</p>
<p>The normal stage emits <code>analog</code> for PILOT-03 and retains the limited RC sensitivity study as <code>analog-rc</code>. Missing model files block the gate. Changed hashes, invalid waveforms and failed tools produce execution errors. The nine new regression tests cover these failure paths and prevent relaxed stimuli or tolerances.</p>
<p>Full PVT, actual PCB/socket loading, OE handover and physical clock/reset qualification remain open under PILOT-05.</p>
<nav><a href="{base}acceptance.json">Acceptance</a> · <a href="{base}driver.json">Fresh syntax/DC audit</a> · <a href="{base}experiment.json">Transient results</a> · <a href="{base}simulation.log">Execution log</a> · <a href="{base}traces/rising-normal.csv">Rising trace</a> · <a href="{base}traces/falling-normal.csv">Falling trace</a> · <a href="tests.log">Full regression log</a></nav></section>
<section><h2>Integration sources</h2><p>{len(changed)} changed or added files, staged against {len(baseline)} original normal-run sources. The acceptance requirements are unchanged. Vendor tables and derived SPICE circuits remain in the private cache.</p><ul>{links}</ul></section>
<nav><a href="summary.json">Summary</a> · <a href="source-manifest.json">Source hashes</a> · <a href="manifest.json">Publication hashes</a> · <a href="remote-validation.json">Remote validation</a></nav></main></html>'''
    (HERE/'index.html').write_text(page)
    paths=[HERE/name for name in ('publish.py','promote.py','verify.py','browser_check.cjs','tests.log','source-manifest.json','summary.json','index.html')]
    paths.extend(CANDIDATE/p for p in changed)
    paths.extend(loaded.rglob('*'))
    paths.append(verification/'build/analog/evidence.json')
    paths.extend(verification/'build'/p for row in evidence if row['id']=='analog-rc' for p in row['artifacts'])
    # Only computed traces/logs and owned implementation are public here.
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths)) if p.is_file()}
    assert not any(Path(p).suffix=='.ibs' for p in files)
    assert not any(p.suffix=='.cir' for p in loaded.rglob('*'))
    # The original generic RC deck is owned sensitivity code, not a circuit
    # derived from licensed manufacturer tables.
    rc_decks={str((verification/'build'/p).relative_to(HERE)) for row in evidence
              if row['id']=='analog-rc' for p in row['artifacts'] if p.endswith('.cir')}
    assert {p for p in files if p.endswith('.cir')}<=rc_decks
    write(HERE/'manifest.json',dict(created_at=summary['created_at'],files=files))
    print('Validated',summary['tests'],'tests;',len(changed),'source changes;',len(files),'published files')


if __name__=='__main__':main()

"""Validate the staged ACH selection against normal clock and FD1 execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANDIDATE=HERE/'candidate'
sys.path.insert(0,str(CANDIDATE/'Verification'))
from dm02 import clock, distribution
from dm02.common import BUILD,write_json
from dm02.reporting import sources
from dm02.legacy import read_sheet,connectivity


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before=sources()
    baseline=json.loads((HERE/'baseline-sources.json').read_text())
    for relative,digest in baseline.items():assert sha(ROOT/relative)==digest,'Normal source changed: '+relative
    original=BUILD/'clock-integration/original-clock.sch';original.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch',original)
    remap={'1':'1','7':'4','8':'5','14':'8'}
    old={frozenset((r,remap[p] if r=='Y1' else p) for r,p in n['nodes']) for n in connectivity(read_sheet(original))}
    selected=clock.Clock()
    new={frozenset(tuple(n) for n in net['nodes']) for net in selected.nets}
    assert old==new,'Clock logic connectivity changed beyond oscillator pin mapping'
    clock_rows=clock.run();write_json(BUILD/'clock/evidence.json',clock_rows)
    assert [(r['id'],r['status']) for r in clock_rows]==[('clock-candidate','pass'),('physical-clock','limited')]
    fd1=distribution.run();write_json(BUILD/'distribution/evidence.json',fd1)
    assert fd1['status']=='limited',fd1
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','Verification/tests','-v'],
        cwd=CANDIDATE,capture_output=True,text=True,timeout=600)
    log=result.stdout+result.stderr;(HERE/'tests.log').write_text(log)
    match=re.search(r'Ran (\d+) tests in .*\n\nOK\s*$',log)
    assert result.returncode==0 and match and int(match[1])>=158,log
    assert sources()==before,'Staged sources changed during validation'
    for relative,digest in baseline.items():assert sha(ROOT/relative)==digest,'Normal source changed: '+relative
    changed={p:h for p,h in before.items() if baseline.get(p)!=h}
    assert not baseline.keys()-before.keys(),'Staging deleted normal inputs'
    assert before['Verification/requirements.json']==baseline['Verification/requirements.json']
    write_json(HERE/'source-manifest.json',dict(baseline=baseline,candidate=before,changed=changed))
    timing=json.loads((BUILD/'distribution/timing.json').read_text())
    assert timing['passed'] and len(timing['results'][1]['paths'])==46
    candidate=json.loads((BUILD/'clock/candidate.json').read_text())
    assert len(candidate['simulations'])==150 and candidate['native_migration']['status']=='pass'
    write_json(HERE/'summary.json',dict(created_at=datetime.now(timezone.utc).isoformat(),passed=True,
        status='validated-in-staging',normal_sources_modified=False,tests=int(match[1]),
        normalized_clock_net_groups=len(old),clock_profiles=150,clock_native=candidate['native_migration'],
        oscillator_contract=selected.oscillator_contract(),clock_timing=candidate['timing'],
        fd1=fd1,intervals=timing['results'],changed_sources=len(changed),
        physical_clock_qualified=False,fabrication_ready=False,
        bom_change=dict(reference='C1/Y1',previous_mpn='ECS-100AX-080',candidate_mpn='ACH-4.000MHZ-EK',
            previous_footprint='Oscillator:Oscillator_DIP-14',candidate_footprint='Oscillator:Oscillator_DIP-8',
            inventory_confirmed=False,published_workbook_modified=False)))
    print('Clock integration validated:',int(match[1]),'tests,150 clock profiles,FD1 execution and46 interval paths',flush=True)


if __name__=='__main__':main()

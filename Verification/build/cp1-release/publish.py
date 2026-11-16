"""Publish RR1 paths, activity experiments and an explicitly unmeasured plan."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import digest,write_json
from dm02.reporting import freshness
from dm02 import cp1,release_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-release/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve RR1 publication'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,study=release_evidence.load()
    mapping={'report.json':'Verification/build/report.json','release-notes.md':'Verification/Release-requirements.md',
        'tests.log':'Verification/build/tests.log','smoke.log':'Verification/build/cp1/smoke.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json','study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/release-evidence.json','Verification/tests/test_release_requirements.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    for name in ('sn74hct245.txt','um61512a.txt','sn74ahct244.txt','sn74ahct04.txt','sn74ahct08.txt','sn74ahct00.txt','sn74ahct32.txt','manifest.json'):
        mapping['sources/'+name]='Verification/build/cp1-link-loads/sources/'+name
    hashes={}
    for dest,source in mapping.items():
        original=ROOT/source;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(original);shutil.copyfile(original,target)
        assert digest(original)==digest(target)==before;hashes[source]=before
    write_json(HERE/'measurement-plan.json',study['measurement_plan'])
    text='''# DATA and SRAM release requirements

**CP1-RR1 traces driver ownership and OE/WE timing on MD1.** DATA has one final driver; SRAM's private bus has two. The native circuit is unchanged. CP1-R2 remains accepted.

The audit checks 8,192 reset/command/phase/address combinations and all physical control paths. Four short sensitivity profiles pass; five contention/capture faults and four native inventory/control mutations are detected. Four instrumented ROM/text boots reconstruct 160 bytes and finish TX1 CR LF after HALT.

**Physical loads, earliest invalid-data hold and loaded release remain unqualified.** A 48-driver measurement specification covers the OC1 supply/temperature grid. Every measured load/release field is still null.

- [Control paths, model audit and scope](release-notes.md)
- [Complete reproducible summary](summary.json)
- [Per-driver measurement procedure](measurement-plan.json)
- [UM61512A manufacturer excerpt](sources/um61512a.txt)
- [HCT245 manufacturer excerpt](sources/sn74hct245.txt)
- [AHCT244 manufacturer excerpt](sources/sn74ahct244.txt)
- [Short experiment matrix](iteration-2/short-matrix.json)
- [Boot experiment matrix](iteration-2/boot-matrix.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)

## Driver and fixture distinctions

| Link | IC-only allocation | Release obligation |
| --- | --- | --- |
| DATA0–3 / DATA4–7 | 100 / 90 pF | Sole final driver. Capture/hold and idle behaviour still require qualification; disable table is 50 pF, enable/data 150 pF. |
| SRAM RAM0–7 | 20 pF per active driver | SRAM must release before U4 drives, and U4 before SRAM drives. SRAM release fixture is 5 pF; read fixture 30 pF. |
| SOURCE3 | 30 pF per active driver | ME1 U9 competes with MA1 U20/U21. SRAM and U9 share OE; invalid data may propagate before U9 releases. |

Native maximum-path sums give conditional command blanks of 36.5 ns read-to-write, 48 ns write-to-read and 76.5 ns for U9 release. Add routing/skew, uncertainty and positive reserve. These sums use unqualified device/load assumptions and are not physical limits.

## Instrumented ROM/text boots

Each normal profile observes 167 changes of opposing SRAM-bus ownership in each direction. Gaps are between control requests, before the independent zero-activation and 10/13 ns release envelopes. They describe this workload, not every instruction or operating mode.

| Run | Read-to-write gap ns | Write-to-read gap ns | Expected result | Evidence |
| --- | --- | --- | --- | --- |
'''
    for name,result in study['boots'].items():
        gaps=result['opposing_turnovers'];a=gaps['read_to_write']['minimum_requested_gap_ns'];b=gaps['write_to_read']['minimum_requested_gap_ns']
        expected='Overlap detected' if name=='boot-late-release' else 'Boot and text pass'
        text+=f'| {name} | {a if a is not None else "—"} | {b if b is not None else "—"} | {expected} | [log](iteration-2/{name}/simulation.log) · [events](iteration-2/{name}/release-events.csv) |\n'
    text+='''
The additional always-enabled DATA-stage boot passes. This is a digital sensitivity experiment; the native OE circuit remains intact. A 5,000 ns SRAM-release envelope triggers overlap on the first write handover. The activity monitor detects simultaneous drive even when both drivers carry identical data.

## Short control experiments

| Run | Expected result | Evidence |
| --- | --- | --- |
'''
    short=json.loads((HERE/'iteration-2/short-matrix.json').read_text())
    for name,r in short.items():text+=f'| {name} | {r["expected"]} | [log](iteration-2/{name}/simulation.log) · [native-derived controls](iteration-2/{name}/controls.sv) |\n'
    text+='''
## Preservation and replay

`iteration-1` preserves the first short tests and boot compilation errors caused by monitor placement before declarations. `iteration-2` contains fifteen completed experiments and their exact simulation-source snapshots. `replay-draft-1` retains the initial audit before expanded address and SOURCE3 traces. The final summary regenerates those traces and counts opposing ownership changes once.

Restore MD1 and its earlier dependencies through `Backup/README.md`, then this study. Run `python3 Verification/run.py --allow-design-failures`. Physical measurement, reviewed release bounds, idle/floating-input behaviour and full timing acceptance remain in Beads.
'''
    (HERE/'index.md').write_text(text)
    (HERE/'release.css').write_text('table { display:block; max-width:100%; overflow-x:auto; }\n')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata','title=DM-02 DATA/SRAM release requirements',
        '--css','study.css','--css','release.css','-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        physical_qualification=False,promoted_into_R2=False,milestones_passed=[3,3,8]))
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and
        (p.parent!=HERE or p.name not in excluded)}
    write_json(HERE/'manifest.json',dict(files=files))


def verify():
    files=json.loads((HERE/'manifest.json').read_text())['files']
    def check(item):
        name,record=item;assert digest(HERE/name)==record['sha256'],name
        with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
            actual=hashlib.sha256(response.read()).hexdigest()
        assert actual==record['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,files.items()))
    write_json(HERE/'remote-validation.json',dict(passed=True,checked_hashes=len(checked),base_url=BASE))
    print('Verified',len(checked),'published hashes:',BASE)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if not a.verify_only:snapshot()
    verify()

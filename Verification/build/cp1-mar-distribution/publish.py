"""Publish MD1 native topology, conditional budgets and affected simulations."""
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
from dm02 import cp1,mar_distribution_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-mar-distribution/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['mar_distribution']['revision']=='CP1-MD1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,study=mar_distribution_evidence.load()
    mapping={'report.json':'Verification/build/report.json','mar-notes.md':'Verification/MAR-distribution.md',
        'smoke.log':'Verification/build/cp1/smoke.log','tests.log':'Verification/build/tests.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json','study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/mar-distribution-evidence.json','Verification/tests/test_mar_distribution.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js','Circuits/KiCad/Integrated/README.md']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# Buffered memory address candidate

**CP1-MD1 adds two DIP address buffers and two decoupling capacitors.** The raw MAR bus now drives 30 pF per bit in the conditional IC-only inventory. The new outputs drive 24 pF on bits 0–13 and 28 pF on bits 14–15. MQ1's live-address tap remains on raw MAR.

The 17-sheet native hierarchy has 610 fitted candidate records, 272 DIP logic/memory ICs and 7,368 physical pins. Separate input/output net checks pass; contracting the sixteen buffer transfers reproduces CA1's functional connections. Three native wiring faults are detected.

| Stage | IC-only subtotal | Socket/routing/probe allocation | Planning margin to 50 pF |
| --- | --- | --- | --- |
| Raw MAR, all 16 bits | 30 pF | 15 pF | 5 pF |
| Buffered memory, bits 0–13 | 24 pF | 15 pF | 11 pF |
| Buffered memory, bits 14–15 | 28 pF | 15 pF | 7 pF |

The allowance assigns 1 pF per attached socket pin, 6 pF to traces/vias/pads and 5 pF to a probe. These are design allocations. **Physical capacitances and loaded timing remain unqualified**, including the earlier conditional input-capacitance maxima. CP1-R2 remains accepted; MD1 is a separate candidate.

- [Topology, assumptions and scope](mar-notes.md)
- [Native hierarchy root](final/native/MD1.kicad_sch)
- [New buffer sheet](final/native/MB1.kicad_sch)
- [Every component and moved receiver](final/native/provenance.json)
- [Complete loads and all 32 stage budgets](final/loads.json)
- [Native-derived buffer/model bindings](final/bindings.json)
- [Native parity and mutations](final/summary.json)
- [Independent canonical export](final/canonical-comparison.json)
- [Affected simulation matrix](simulation-1/matrix.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)

## Memory and ROM/text checks

The complete memory exercise passes **131,073 reads, 48,897 writes, 16,384 protected-write checks and 256 IO cases**. The exhaustive transfer test passes all 65,536 address words; swapped-address and disabled-buffer variants fail.

Four ROM-startup profiles reconstruct the 160-byte SRAM payload and finish `TX1\\r\\n` after CPU HALT. Only the sixteen memory address input assignments change from the pinned TB1 models. Maximum added delay is 9.5 ns; zero and mixed delays are sensitivity cases. The swapped-address CPU case fails the loader's first write-address check.

| Run | Result | CPU IO setup ns | CPU IO hold ns | Evidence |
| --- | --- | --- | --- | --- |
'''
    for name,r in study['simulations']['results'].items():
        outcome='Pass' if r['passed'] else 'Fault detected'
        text+=f'| {name} | {outcome} | {r.get("cpu_io_setup_ns") or "—"} | {r.get("cpu_io_hold_ns") or "—"} | [log](simulation-1/{name}/simulation.log) |\n'
    text+='''
## Native buffer sheet

![Two AHCT244 buffers and local decoupling](final/render/MD1-MB1.svg)

| Module | Native source | Sheet view |
| --- | --- | --- |
'''
    from dm02.native_assembly import BOARDS
    for b in (*BOARDS,'MB1'):
        text+=f'| {b} | [schematic](final/native/{b}.kicad_sch) | [SVG](final/render/MD1-{b}.svg) |\n'
    text+='| CPU contacts | [schematic](final/native/CN1.kicad_sch) | [SVG](final/render/MD1-CPU%20contacts.svg) |\n'
    text+='''
## Preserved evidence

The first native iteration remains in `iteration-1`. Final load/model bindings and the checked-in-source export are in `final`; all nine simulation runs are in `simulation-1`. The first harness failure is preserved in `failed-regression-1`: two isolated-replay tests exposed five omitted original memory-fixture dependencies, now declared by the corrected lock. Restore LL1, CA1 and their earlier dependencies through `Backup/README.md` before bounded replay. Production readability/ERC, actual BOM/placement, full-envelope electrical qualification and measured operation remain open.
'''
    (HERE/'index.md').write_text(text)
    (HERE/'mar.css').write_text('img { max-width:100%; height:auto; } figure { margin:1.5rem 0; } table { display:block; max-width:100%; overflow-x:auto; }\n')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata','title=DM-02 buffered memory address candidate',
        '--css','study.css','--css','mar.css','-o',str(HERE/'index.html')],check=True)
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

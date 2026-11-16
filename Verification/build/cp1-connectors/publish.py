"""Preserve the MC1/CN1 study after a fresh bounded replay."""
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import digest,write_json
from dm02.reporting import freshness
from dm02 import cp1,connector_plan

BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-connectors/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve the publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh']
    assert report['revision']=='CP1-R2' and report['mechanical_contract']['revision']=='CP1-MC1'
    assert not [c for c in report['checks'] if c['status']=='error']
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    plan=json.loads((ROOT/'Verification/build/cp1/connector-plan.json').read_text())
    check=connector_plan.validate(plan)
    assert check['contacts_checked']==1242 and not plan['manufacturing_release']
    mapping={
        'report.json':'Verification/build/report.json',
        'pin-plan.json':'Verification/build/cp1/connector-plan.json',
        'check.json':'Verification/build/cp1/connector-check.json',
        'mechanical-contract.json':'Verification/mechanical-contract.json',
        'connector-notes.md':'Verification/Connector-plan.md',
        'mechanical-notes.md':'Verification/Mechanical-contract.md',
        'proposal-screen.json':'Verification/build/cp1-partition/screen.json',
        'smoke.log':'Verification/build/cp1/smoke.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'study.css':'Verification/build/cp1-readiness/study.css',
    }
    for name in ('Verification/dm02/connector_plan.py','Verification/dm02/cp1.py',
                 'Verification/tests/test_connector_plan.py','Verification/tests/test_cp1.py',
                 'Verification/dashboard/app.js','Verification/targets/cp1/lock.json'):
        mapping['sources/'+name]=name
    for name in plan['source_hashes']:
        mapping['native/'+name.removeprefix('cp1-hct273/')]='Verification/build/'+name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before
        hashes[name]=before
    (HERE/'pin-tables.md').write_text(connector_plan.render(plan))
    subprocess.run(['pandoc',str(HERE/'pin-tables.md'),'--standalone','--toc','--metadata',
        'title=DM-02 draft connector contact tables','--css','study.css','-o',str(HERE/'contacts.html')],check=True)
    (HERE/'index.md').write_text('''# Selected geometry and draft connector plan

**CP1-MC1** records owner approval of four 250 × 200 mm CPU cards and a 270 × 270 mm active backplane, eight positions at 30 mm pitch, four layers.

**CP1-CN1-draft** assigns 1,242 contacts. Native crossing counts are 71 control, 57 compute, 66 counters and 92 memory. The memory card adds 17 live-address/read signals and uses 109/112 signal positions.

Connector footprints, keying, current/loading/timing and physical circuitry remain unqualified. CP1-R2 remains the accepted digital revision.

- [Contact tables](contacts.html)
- [Machine-readable pin plan and native endpoints](pin-plan.json)
- [Allocation checks](check.json)
- [Mechanical contract](mechanical-contract.json)
- [Connector notes and manufacturer references](connector-notes.md)
- [Mechanical decision notes](mechanical-notes.md)
- [Manufacturer/footprint dimensional screen](footprint-screen.json)
- [Manufacturer Type C catalog extract](sources/type-c-extract.pdf)
- [Historical proposal screen](proposal-screen.json)
- [Replay report](report.json)
- [Harness log](smoke.log)
- [Equivalence evidence](equivalence.json)
''')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 mechanical contract and connector planning','--css','study.css','-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        milestones_passed=[3,3,8],physical_qualification=False,manufacturing_release=False))
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    write_json(HERE/'manifest.json',dict(files=files))


def verify():
    files=json.loads((HERE/'manifest.json').read_text())['files']
    def check(item):
        name,record=item
        assert digest(HERE/name)==record['sha256'],name
        with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
            actual=hashlib.sha256(response.read()).hexdigest()
        assert actual==record['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,files.items()))
    write_json(HERE/'remote-validation.json',dict(passed=True,checked_hashes=len(checked),base_url=BASE))
    print('Verified',len(checked),'published hashes:',BASE)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if not args.verify_only:snapshot()
    verify()

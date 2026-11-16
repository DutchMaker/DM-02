"""Snapshot the IO scope/protocol study without changing earlier publications."""
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
from dm02 import cp1,io_contract

BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-io/'


def snapshot():
    assert not (HERE/'snapshot.json').exists(),'Preserve existing snapshots; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh']
    assert report['revision']=='CP1-R2' and report['requirements']['scope_revision']=='CP1-SC1'
    assert report['io_contract']['revision']=='CP1-IO1'
    assert not [c for c in report['checks'] if c['status']=='error']
    assert next(c for c in report['checks'] if c['id']=='io-contract')['status']=='limited'
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    check=json.loads((ROOT/'Verification/build/cp1/io-contract-check.json').read_text())
    assert check['boundary']['passed'] and check['protocol']['passed']
    assert not check['physical_qualification'] and not check['boundary']['existing_read_address']
    mapping={
        'report.json':'Verification/build/report.json',
        'io-interface.json':'Verification/build/cp1/io-interface.json',
        'io-contract-check.json':'Verification/build/cp1/io-contract-check.json',
        'README.md':'Verification/IO-interface.md',
        'Operating-contract.md':'Verification/Operating-contract.md',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'equivalence.log':'Verification/build/cp1/equivalence.log',
        'smoke.log':'Verification/build/cp1/smoke.log',
        'study.css':'Verification/build/cp1-readiness/study.css',
    }
    for name in ('Verification/io-interface.json','Verification/dm02/io_contract.py','Verification/dm02/cp1.py',
                 'Verification/dashboard/app.js','Verification/tests/test_io_contract.py','Verification/tests/test_cp1.py',
                 'Verification/requirements.json','Verification/targets/cp1/lock.json'):
        mapping['sources/'+name]=name
    for board in ('ME1','BP1'):
        mapping['native/'+board+'.xml']='Verification/build/'+io_contract.NATIVE.format(board=board)
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==before==digest(target),name
        hashes[name]=before
    (HERE/'links.html').write_text('<h2>Evidence files</h2><ul>'+''.join(
        f'<li><a href="{name}">{name}</a></li>' for name in
        ('report.json','io-interface.json','io-contract-check.json','equivalence.json','smoke.log','native/ME1.xml','native/BP1.xml'))+'</ul>')
    subprocess.run(['pandoc',str(HERE/'README.md'),'--standalone','--toc','--metadata',
        'title=DM-02 first-machine scope and expandable IO','--css','study.css','--include-after-body',str(HERE/'links.html'),
        '-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,scope_revision='CP1-SC1',io_revision='CP1-IO1',
        design_revision='CP1-R2',physical_qualification=False,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        milestones_passed=[3,3,8],protocol=check['protocol'],native_pins_checked=len(check['boundary']['checked_pins']),
        scope='Approved first-machine scope and logical IO protocol. Physical bridge, pinout and endpoints pending.'))
    files={str(p.relative_to(HERE)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
        and p.name not in {'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}}
    write_json(HERE/'manifest.json',dict(files=files))


def verify():
    files=json.loads((HERE/'manifest.json').read_text())['files']
    def check(item):
        name,record=item
        assert digest(HERE/name)==record['sha256'],name
        with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
            observed=hashlib.sha256(response.read()).hexdigest()
        assert observed==record['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,files.items()))
    write_json(HERE/'remote-validation.json',dict(passed=True,checked_hashes=len(checked),base_url=BASE))
    print('Verified',len(checked),'published files:',BASE)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if not args.verify_only:snapshot()
    verify()

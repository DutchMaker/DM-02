"""Preserve and publish the accepted CP1-OC1 contract/report snapshot."""
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
from dm02 import cp1,operating_contract

BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-contract/'

def snapshot():
    assert not (HERE/'snapshot.json').exists(),'Preserve the published snapshot; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh']
    assert report['revision']=='CP1-R2' and report['operating_contract']['revision']=='CP1-OC1'
    assert not [c for c in report['checks'] if c['status']=='error']
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    contract=operating_contract.load()
    assert report['requirements']['revision']==contract['revision']
    assert report['requirements']['operating_envelope']['clock_hz']==500000
    assert report['requirements']['historical_baseline']['operating_envelope']['clock_hz']==1000000
    mapping={
        'report.json':'Verification/build/report.json',
        'operating-contract.json':'Verification/build/cp1/operating-contract.json',
        'qualification-matrix.json':'Verification/build/cp1/qualification-matrix.json',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'equivalence.log':'Verification/build/cp1/equivalence.log',
        'smoke.log':'Verification/build/cp1/smoke.log',
        'README.md':'Verification/Operating-contract.md',
        'CP1-readiness.md':'Verification/CP1-readiness.md',
        'study.css':'Verification/build/cp1-readiness/study.css',
    }
    for name in ('Verification/operating-contract.json','Verification/dm02/operating_contract.py',
                 'Verification/dm02/cp1.py','Verification/dashboard/app.js','Verification/tests/test_operating_contract.py',
                 'Verification/tests/test_cp1.py','Verification/requirements.json','Verification/targets/cp1/lock.json'):
        mapping['sources/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(target)==before==digest(source)
        hashes[name]=before
    matrix=json.loads((HERE/'qualification-matrix.json').read_text())
    assert len(matrix['physical'])==54 and len(matrix['digital'])==90
    assert all(r['status']=='not-run' for r in matrix['physical'])
    assert all(r['status']=='coverage-request-only' for r in matrix['digital'])
    (HERE/'links.html').write_text('<h2>Evidence files</h2><ul>'+''.join(
        f'<li><a href="{name}">{name}</a></li>' for name in
        ('report.json','operating-contract.json','qualification-matrix.json','equivalence.json','smoke.log'))+'</ul>')
    subprocess.run(['pandoc',str(HERE/'README.md'),'--standalone','--toc','--metadata',
        'title=DM-02 CP1-OC1 operating contract','--css','study.css','--include-after-body',str(HERE/'links.html'),
        '-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,contract_revision='CP1-OC1',design_revision='CP1-R2',
        physical_qualification=False,source_hashes=hashes,harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        milestones_passed=[3,3,8],physical_rows=54,digital_coverage_requests=90,
        scope='Operating-contract selection and fresh bounded replay. No new circuit or physical acceptance.'))
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

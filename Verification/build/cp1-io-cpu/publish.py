"""Publish the immutable CPU/bridge diagnostic, including negative results."""
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
from dm02 import cp1,io_cpu_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-io-cpu/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['io_cpu']['revision']=='CP1-BI1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,matrix=io_cpu_evidence.load()
    mapping={'report.json':'Verification/build/report.json',
        'integration-notes.md':'Verification/IO-CPU-integration.md',
        'smoke.log':'Verification/build/cp1/smoke.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/io-cpu-evidence.json',
        'Verification/dm02/cp1.py','Verification/tests/test_io_cpu.py','Verification/tests/test_cp1.py',
        'Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before
        hashes[name]=before
    text='''# CPU/bridge integration diagnostic

**CP1-BI1: 29 passing profiles, two endpoint-latency failures and three detected wiring faults.** Each passing run executed 334 microcycles and checked 14 echoed bytes through the complete CPU/BR1 path.

At 500 kHz microcycles, 160 ns endpoint response passed with 45.5 ns sampled setup; 200 ns failed setup reserve and 400 ns produced wrong captured data. The 400 ns fixture passed at diagnostic 250 kHz.

CP1-R2 remains the accepted digital computer. The test uses preloaded ROM/RAM and behavioral endpoints. Full min/max timing, real text circuitry and autonomous boot with BR1 remain open. Sampled intervals are not physical timing guarantees.

- [Method, scope and preserved development failures](integration-notes.md)
- [Complete matrix](matrix.json)
- [Bounded replay report](report.json)
- [Harness log](smoke.log)
- [R2 equivalence](equivalence.json)

## Every profile

| Profile | Result | Endpoint ns | Setup ns | Simulation log |
| --- | --- | --- | --- | --- |
'''
    for name,r in matrix['results'].items():
        text+=f'| {name} | {"pass" if r["passed"] else "expected failure"} | {r["endpoint_ns"]} | {r.get("observations",{}).get("min_setup_ns","—")} | [log](profiles/{name}/simulation.log) |\n'
    (HERE/'index.md').write_text(text)
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 CPU and IO bridge diagnostic','--css','study.css','-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        milestones_passed=[3,3,8],physical_qualification=False,promoted_into_R2=False))
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

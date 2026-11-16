"""Snapshot and remotely verify the separate CP1-BR1 candidate publication."""
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
from dm02 import cp1,io_bridge_evidence

BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-bridge/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve the publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh']
    assert report['revision']=='CP1-R2' and report['io_bridge']['revision']=='CP1-BR1'
    assert not [c for c in report['checks'] if c['status']=='error']
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,result=io_bridge_evidence.load()
    mapping={
        'report.json':'Verification/build/report.json',
        'bridge-notes.md':'Verification/IO-bridge.md',
        'smoke.log':'Verification/build/cp1/smoke.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'study.css':'Verification/build/cp1-readiness/study.css',
    }
    for name in list(lock['source_hashes'])+['Verification/bridge-evidence.json',
        'Verification/dm02/cp1.py','Verification/tests/test_io_bridge.py',
        'Verification/tests/test_cp1.py','Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before
        hashes[name]=before
    (HERE/'index.md').write_text('''# Four-slot I/O bridge candidate

**CP1-BR1** adds six memory-card and 35 active-backplane DIP packages. Native KiCad connectivity, structural checks and the internal 50 pF load screen pass.

Four delay profiles each passed **70,020 read cases and 256 writes**. Four injected faults were detected. The native audit binds 17 memory-card extensions and 384 peripheral contacts, preserving separate live-read and registered-write addresses and separate reset branches.

CP1-R2 remains the accepted digital computer. The candidate awaits full CPU integration, the real text endpoint and physical qualification. The conditional 379 ns internal return-path sum omits CPU/endpoint/routing terms; load, slew and minimum-delay timing remain open.

- [Circuit and qualification limits](bridge-notes.md)
- [Candidate results, load screen and conditional paths](summary.json)
- [Native R2/CN1 boundary bindings](boundary-audit.json)
- [MQ1 native schematic](native/MQ1/MQ1.kicad_sch)
- [BR1 native schematic](native/BR1/BR1.kicad_sch)
- [Maximum-delay profile log](profile-1/simulation.log)
- [Reset-release fault detection](mutations/reset-release-write/simulation.log)
- [Manufacturer pinout and timing extract](sources/mux-decoder-buffer-extract.pdf)
- [Preserved first load-overage iteration](iterations/01-load-overages/summary.json)
- [Preserved common-reset fixture iteration](iterations/02-common-reset-fixture/summary.json)
- [Bounded replay report](report.json)
- [Harness log](smoke.log)
- [R2 equivalence check](equivalence.json)
''')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 native-pin I/O bridge candidate','--css','study.css','-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        milestones_passed=[3,3,8],physical_qualification=False,integrated_into_R2=False))
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

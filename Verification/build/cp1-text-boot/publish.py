"""Publish the pinned TB1 ROM startup profiles and detected loader faults."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import re
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
from dm02 import cp1,text_boot_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-text-boot/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['text_boot']['revision']=='CP1-TB1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,matrix=text_boot_evidence.load()
    mapping={'report.json':'Verification/build/report.json','text-boot-notes.md':'Verification/Text-boot.md',
        'smoke.log':'Verification/build/cp1/smoke.log','tests.log':'Verification/build/tests.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json',
        'study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/text-boot-evidence.json','Verification/tests/test_text_boot.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# ROM-only serial startup

**CP1-TB1: six startup profiles passed; three injected loader faults detected.** Starting at reset PC zero, the CPU executes an 806-byte ROM loader, deposits 160 bytes into poisoned SRAM at `$4000` and runs the text diagnostic. Every passing run emits `TX1\\r\\n`, with the last stop-bit sample after CPU HALT.

The architectural oracle checks 322 instructions, 160 ordered writes, entry address, stack pointer and payload hash. A native SRAM observer checks every deposited byte before application entry. Four poison seeds and maximum/zero/mixed delay profiles passed.

The simulation assumes stable supply and oscillators, with a 25 ms reset-request guard. Physical ROM programming/readback, startup supervision, terminal/CDC qualification and native assembly promotion remain open. CP1-R2 remains the accepted digital circuit.

- [ROM image, method and scope](text-boot-notes.md)
- [Complete matrix](matrix.json)
- [ROM programming image](guarded-max/boot-rom.bin)
- [Loader listing](guarded-max/loader.lst)
- [Architectural oracle](guarded-max/oracle.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)
- [Fresh CPU smoke run](smoke.log)

## Startup profiles

| Profile | Poison seed | Sampled CPU setup ns | Sampled CPU hold ns | Evidence |
| --- | --- | --- | --- | --- |
'''
    for name,r in matrix['results'].items():
        if r['fault']:continue
        log=(HERE/name/'simulation.log').read_text()
        setup,hold=re.search(r'PASS TX1 CPU .*setup_ns=([\d.]+) hold_ns=([\d.]+)',log).groups()
        text+=f'| {name} | {r["seed"]:02X} | {setup} | {hold} | [log]({name}/simulation.log) |\n'
    text+='\n## Detected loader faults\n\n| Mutation | Failure check | Evidence |\n| --- | --- | --- |\n'
    for name,r in matrix['results'].items():
        if r['fault']:text+=f'| {r["fault"]} | {text_boot_evidence.REASONS[r["fault"]]} | [log]({name}/simulation.log) |\n'
    text+='\n## Development evidence\n\nThe [first](initial-max/compile.log) and [second](max/compile.log) elaboration failures are preserved. Both failed before simulation because observer declarations appeared after use.\n'
    (HERE/'index.md').write_text(text)
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 ROM-only serial startup','--css','study.css','-o',str(HERE/'index.html')],check=True)
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        physical_qualification=False,promoted_into_R2=False,milestones_passed=[3,3,8]))
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
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
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if not args.verify_only:snapshot()
    verify()

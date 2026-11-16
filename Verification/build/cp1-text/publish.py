"""Publish TX1 native candidate and its passing/negative simulation evidence."""
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
from dm02 import cp1,text_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-text/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['text_card']['revision']=='CP1-TX1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,matrix,audit=text_evidence.load()
    mapping={'report.json':'Verification/build/report.json','text-card-notes.md':'Verification/Text-card.md',
        'smoke.log':'Verification/build/cp1/smoke.log','equivalence.json':'Verification/build/cp1/equivalence.json',
        'study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/text-evidence.json','Verification/tests/test_text_card.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# Autonomous serial text-card candidate

**CP1-TX1: 37 DIP ICs, all 256 byte values decoded in six standalone profiles, four injected faults detected.** Six CPU/BR1 integration profiles passed. Five populated-card runs emitted `TX1\\r\\n`; the final stop bit arrived after CPU HALT. The sixth checked absent-device handling.

The local ACH-4.000MHZ-EK oscillator divides by 416 for a 9600-baud 8N1 terminal setting. J2 carries 5 V TTL TX and ground. The separate mailbox and transmit registers implement persistent READY, busy-write preservation and overrun W1C.

CP1-R2 remains the accepted digital computer. The CPU diagnostic uses preloaded memory. Physical terminal output, metastability/CDC, full timing and autonomous boot with BR1/TX1 remain open.

- [Circuit and qualification scope](text-card-notes.md)
- [Native KiCad schematic](iteration-2/native/TX1/TX1.kicad_sch)
- [Native pin parity](iteration-2/native/TX1/comparison.json)
- [Parts, loads, connector bindings and conditional paths](final/audit.json)
- [Complete matrix](final/matrix.json)
- [Bounded replay report](report.json)
- [Harness log](smoke.log)
- [Manufacturer source pin review](sources/pin-review.pdf)

## Standalone serial profiles

| Profile | Result | Bytes checked | Evidence |
| --- | --- | --- | --- |
'''
    for name,r in matrix['standalone'].items():
        text+=f'| {name} | {"pass" if r["passed"] else "detected mutation"} | {256 if r["passed"] else "—"} | [log](final/{name}/simulation.log) |\n'
    text+='\n## CPU integration\n\n| Profile | Sampled setup ns | Final stop after HALT | Evidence |\n| --- | --- | --- | --- |\n'
    for name,r in matrix['cpu'].items():
        o=r.get('observations',{})
        text+=f'| {name} | {o.get("setup_ns","absent card")} | {"yes" if o else "error marker checked"} | [log](final/{name}/simulation.log) |\n'
    text+='\n## Development evidence\n\n[First native version](iteration-1/audit.json) passed digital framing but had six load-screen overages. [Buffered version](iteration-2/audit.json) adds two HCT244 packages and passes that internal screen. Both versions and their simulations are preserved.\n'
    (HERE/'index.md').write_text(text)
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 autonomous serial text candidate','--css','study.css','-o',str(HERE/'index.html')],check=True)
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

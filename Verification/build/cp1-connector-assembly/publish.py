"""Publish CA1 CPU connector isolation and analytical mating evidence."""
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
from dm02 import cp1,connector_assembly_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-connector-assembly/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['connector_assembly']['revision']=='CP1-CA1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,summary=connector_assembly_evidence.load()
    mapping={'report.json':'Verification/build/report.json','connector-assembly-notes.md':'Verification/Connector-assembly.md',
        'smoke.log':'Verification/build/cp1/smoke.log','tests.log':'Verification/build/tests.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json','study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/connector-assembly-evidence.json','Verification/tests/test_connector_assembly.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js','Circuits/KiCad/Integrated/README.md']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# CPU-card connector assembly

**CP1-CA1: 16 DIN96 candidates, 768 mating contacts and four separate CPU net domains.** The native export checks 7,324 physical pins in 2,420 unmated groups. Applying only the declared mating pairs reproduces NA1's 5,788 functional pins in 1,755 groups exactly.

The connectors carry all 303 signal assignments, including 17 memory extensions, plus 32 supply and 256 ground contacts; 177 contact positions remain unused/reserved. CA1 removes 58 logical boundary markers. Its 606 candidate fitted component records retain 270 DIP logic/memory ICs.

Four mutations are detected. A deliberate shared-global-label bypass passes the fully mated comparison, but fails the separate-card check. The other mutations reverse contact rows, disconnect IO_READ_VALID, or alias a source-bus bit to DATA0.

CP1-R2 remains the accepted digital circuit. Exact connector mating/orientation, parasitic loading, physical timing, production redraw/ERC and PCB release remain open. This is static equivalence to NA1/TB1; it adds no new dynamic simulation claim.

- [Contact mapping, method and scope](connector-assembly-notes.md)
- [Top-level native schematic](final/native/CA1.kicad_sch)
- [CPU connector sheet](final/native/CN1.kicad_sch)
- [Complete comparisons and mutations](final/summary.json)
- [Every contact and component identity](final/native/provenance.json)
- [Canonical source export comparison](final/canonical-comparison.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)

## Connector sheet

![Eight CPU card/backplane connector pairs](final/render/CA1-CPU%20contacts.svg)

The checked-in source root is `Circuits/KiCad/Integrated/candidates/CA1/CA1.kicad_sch`. Open it with its fifteen sibling schematic files. The archive includes all files.

| Module | Native source | Sheet view |
| --- | --- | --- |
'''
    from dm02.native_assembly import BOARDS
    for b in BOARDS:text+=f'| {b} | [schematic](final/native/{b}.kicad_sch) | [SVG](final/render/CA1-{b}.svg) |\n'
    text+='\n## Detected mutations\n\n| Mutation | Unmated differences | Mated functional differences | Evidence |\n| --- | --- | --- | --- |\n'
    for name,r in summary['mutations'].items():
        text+=f'| {name} | {len(r["unmated_differences"])} | {len(r["mated_functional_differences"])} | [comparison](final/{name}/comparison.json) |\n'
    text+='\n## Preserved development evidence\n\nThe [first iteration](iteration-1/summary.json) passed both graphs but retained orphan labels/no-connect marks after deleting boundary symbols. The final candidate removes those graphics and updates child-sheet revision labels. Both versions are preserved.\n'
    (HERE/'index.md').write_text(text)
    (HERE/'assembly.css').write_text('figure { margin: 1.5rem 0; } img { max-width: 100%; height: auto; }\n')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 CPU connector assembly candidate','--css','study.css','--css','assembly.css','-o',str(HERE/'index.html')],check=True)
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

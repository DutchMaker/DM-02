"""Publish NA1 native hierarchy, component metadata and connection evidence."""
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
from dm02 import cp1,native_assembly_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-native-assembly/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['native_assembly']['revision']=='CP1-NA1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,summary,binding=native_assembly_evidence.load()
    mapping={'report.json':'Verification/build/report.json','native-assembly-notes.md':'Verification/Native-assembly.md',
        'smoke.log':'Verification/build/cp1/smoke.log','tests.log':'Verification/build/tests.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json','study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/native-assembly-evidence.json','Verification/tests/test_native_assembly.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js','Circuits/KiCad/Integrated/README.md']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# Native R2 / BR1 / TX1 assembly

**CP1-NA1: 270 DIP ICs, 6,491 physical pins and 1,762 net groups checked.** Independent KiCad export matches the composed graph and verifies component values, footprint references, pin names/types and fitted flags. Three wiring mutations are detected.

The fifteen checked-in schematic files form one hierarchy with unique component references and per-sheet symbol namespaces. Of 648 component records, 590 retain candidate fitted status and 58 are logical boundary markers excluded from BOM and board transfer. All 96 slot-5 contact assignments and 134 explicit TB1 boundary bindings are checked.

CP1-R2 remains the accepted digital circuit. CPU DIN implementation, production-source/PCB promotion, ERC closure and physical timing remain open. TB1's existing simulations are reused through static pin-graph and port-binding equivalence; this study claims no new dynamic simulation.

- [Native source, method and scope](native-assembly-notes.md)
- [Top-level native schematic](final/native/NA1.kicad_sch)
- [Complete comparison and mutation results](final/summary.json)
- [Component provenance and explicit joins](final/native/provenance.json)
- [TB1 boundary bindings](final/native/model-bindings.json)
- [Canonical source export comparison](final/canonical-comparison.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)

## Hierarchy views

![Native hierarchy overview](final/render/NA1.svg)

Open the root and its fourteen sibling schematic files together in KiCad. The release archive contains all of them; the checked-in source path is `Circuits/KiCad/Integrated/candidates/NA1/`.

| Module | Native source | Sheet view |
| --- | --- | --- |
'''
    from dm02.native_assembly import BOARDS
    for b in BOARDS:text+=f'| {b} | [schematic](final/native/{b}.kicad_sch) | [SVG](final/render/NA1-{b}.svg) |\n'
    text+='\n## Detected wiring mutations\n\n| Mutation | Result | Evidence |\n| --- | --- | --- |\n'
    for name,r in summary['mutations'].items():
        text+=f'| {name} | {len(r["differences"])} missing/extra pin groups | [comparison](final/{name}/comparison.json) |\n'
    text+='''
## Preserved development evidence

The first export passed pin connectivity but reused library IDs across sheets. The expanded [metadata recheck](iteration-1/metadata-recheck.json) rejects it because some exported pin definitions belong to another sheet's component. The second iteration corrected the library namespaces. The third added port-binding evidence; a subsequent [replay rejection](replay-rejection.md) led to deterministic JSON-native mutation records. All iterations remain archived.
'''
    (HERE/'index.md').write_text(text)
    (HERE/'assembly.css').write_text('figure { margin: 1.5rem 0; } img { max-width: 100%; height: auto; }\n')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata',
        'title=DM-02 native assembly candidate','--css','study.css','--css','assembly.css','-o',str(HERE/'index.html')],check=True)
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

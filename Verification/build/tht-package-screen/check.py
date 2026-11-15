"""Isolated nominal DIP package substitution screen for four documented parts.

No normal schematics, timing contracts or published BOM selections are changed.
This verifies part-code edits, package pad numbering and native net equivalence;
it is not a timing, insertion-tolerance, availability or physical qualification.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.legacy import read_sheet,connectivity,inventory
from dm02.native_migrate import validate
from dm02.sexpr import parse

CHOICES={
    'CD74HCT161M96':('CD74HCT161E','Package_DIP:DIP-16_W7.62mm','Verification/vendor/pc/cd74hct161.txt'),
    'CD74HCT377M96':('CD74HCT377E','Package_DIP:DIP-20_W7.62mm','Verification/vendor/alu/cd74hct377.txt'),
    'SN74AHCT00DR':('SN74AHCT00N','Package_DIP:DIP-14_W7.62mm','Verification/vendor/controller/sn74ahct00.txt'),
    'SN74AHCT08DR':('SN74AHCT08N','Package_DIP:DIP-14_W7.62mm','Verification/vendor/pc/sn74ahct08.txt')}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')


def check():
    inv=json.loads((ROOT/'Verification/build/assembly-repaired/inventory.json').read_text())
    libraries=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
    sources=[];changes=[];boards=[];footprints={}
    for old,(new,footprint,source) in CHOICES.items():
        text=(ROOT/source).read_text()
        matches=[line.strip() for line in text.splitlines() if re.match(r'^\s*'+re.escape(new)+r'\s+',line) and 'PDIP' in line]
        assert matches,(new,'missing archived manufacturer PDIP listing')
        dest=HERE/'sources'/Path(source).name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,dest)
        sources.append(dict(source=source,sha256=sha(dest),part=new,matching_lines=matches))
        library,name=footprint.split(':');path=libraries/(library+'.pretty')/(name+'.kicad_mod')
        saved=HERE/'footprints'/(library+'.pretty')/path.name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,saved)
        pads=[v for v in parse(saved.read_text()) if isinstance(v,list) and v and v[0]=='pad']
        assert all(p[2]=='thru_hole' for p in pads)
        footprints[footprint]=dict(sha256=sha(saved),numbered_pads=sorted(p[1] for p in pads),
            source=str(path),archived=str(saved.relative_to(HERE)),all_through_hole=True)
    for b in inv['boards']:
        selected=[r for r in inv['packages'] if r['board']==b['board'] and r['value'] in CHOICES]
        if not selected:continue
        source=ROOT/b['source'];assert sha(source)==inv['source_hashes'][b['source']]
        original=read_sheet(source);text=source.read_text();byref={r['reference']:r for r in selected}
        def edit(match):
            block=match.group(0);ref=re.search(r'^L \S+ (\S+)$',block,re.M)[1]
            if ref not in byref:return block
            row=byref[ref];new,footprint,_=CHOICES[row['value']]
            block,n=re.subn(r'^(F 1 )"'+re.escape(row['value'])+'"',lambda m:m[1]+'"'+new+'"',block,flags=re.M);assert n==1
            block,n=re.subn(r'^(F 2 )"'+re.escape(row['footprint'])+'"',lambda m:m[1]+'"'+footprint+'"',block,flags=re.M);assert n==1
            return block
        changed=re.sub(r'^\$Comp\n.*?^\$EndComp',edit,text,flags=re.M|re.S)
        folder=HERE/'circuits';folder.mkdir(exist_ok=True)
        target=folder/source.name;target.write_text(changed);candidate=read_sheet(target)
        groups=lambda s:{frozenset(tuple(n) for n in g['nodes']) for g in connectivity(s)}
        assert groups(original)==groups(candidate)
        prior={p['ref']:p for p in inventory(original)['packages']}
        actual={p['ref']:p for p in inventory(candidate)['packages']}
        assert set(prior)==set(actual)
        for ref,p in actual.items():
            old=prior[ref]
            if ref not in byref:assert p==old;continue
            new,footprint,_=CHOICES[old['value']]
            assert p['value']==new and p['footprint']==footprint and p['lib_id']==old['lib_id']
            pins={pin['number'] for c in candidate['components'] if c['ref']==ref for pin in c['pins']}
            assert pins==set(footprints[footprint]['numbered_pads']),(b['board'],ref,'pad map')
            changes.append(dict(board=b['board'],reference=ref,before=old['value'],after=new,
                before_footprint=old['footprint'],after_footprint=footprint,pads=len(pins)))
        native=validate(candidate,HERE/'native'/b['board']);assert native['status']=='pass',native
        boards.append(dict(board=b['board'],source=b['source'],source_sha256=sha(source),
            candidate=str(target.relative_to(HERE)),candidate_sha256=sha(target),changes=len(selected),native=native))
    counts=Counter(r['before'] for r in changes)
    assert counts=={'CD74HCT161M96':5,'CD74HCT377M96':2,'SN74AHCT00DR':16,'SN74AHCT08DR':16}
    assert len(changes)==39
    for b in boards:assert sha(ROOT/b['source'])==b['source_sha256']
    result=dict(passed=True,scope=__doc__.strip(),changed_packages=39,changed_types=4,
        boards=boards,changes=changes,footprints=footprints,sources=sources,
        remaining_smd_types={'CD74AC175M96':48,'CD74HCT154M96':4},
        unchanged_plcc_flash_packages=8,normal_sources_unchanged=True,
        timing_qualified=False,mechanical_tolerance_qualified=False,stock_confirmed=False,
        manufacturer_status_note='Status strings are from archived datasheets; not a live stock check.',
        procurement_ready=False)
    write('summary.json',result)
    print('DIP package screen:',len(changes),'physical packages across',len(boards),'sheets; native net equivalence and pad-number coverage pass')


if __name__=='__main__':check()

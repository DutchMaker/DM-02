"""Build DL1 and verify physical identities, pin functions and native net parity."""
from collections import Counter,defaultdict
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.legacy import read_sheet,connectivity,inventory
from dm02.native_migrate import validate
from dm02.reporting import sources
from dm02.sexpr import parse


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def groups(sheet):return {frozenset(tuple(n) for n in g['nodes']) for g in connectivity(sheet)}


def verify_export(tree,sheet):
    want={p['ref']:(p['value'],p['footprint']) for p in inventory(sheet)['packages']}
    got={p.attrib['ref']:(p.findtext('value'),p.findtext('footprint','')) for p in tree.findall('./components/comp')}
    assert got==want,'Exported identities differ'
    got={frozenset((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')) for net in tree.findall('./nets/net')}
    assert got==groups(sheet),'Exported pin groups differ'


def main():
    before=sources();config=json.loads((HERE/'choices.json').read_text());choices=config['choices']
    original_inventory=ROOT/'Verification/build/assembly-repaired/inventory.json'
    inv=json.loads(original_inventory.read_text())
    libraries=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
    footprints={};evidence=[];changes=[];boards=[];packages=[];roles=[];input_hashes={}
    for old,c in choices.items():
        source=ROOT/c['source'];text=source.read_text()
        matches=[line.strip() for line in text.splitlines() if re.search(r'(?<!\w)'+re.escape(c['part'])+r'\s+',line) and 'PDIP' in line]
        assert matches,(c['part'],'manufacturer PDIP listing missing')
        dest=HERE/'sources'/source.name
        if dest!=source:shutil.copyfile(source,dest)
        evidence.append(dict(part=c['part'],source=c['source'],sha256=sha(source),listing=matches))
        lib,name=c['footprint'].split(':');fp=libraries/(lib+'.pretty')/(name+'.kicad_mod')
        saved=HERE/'footprints'/(lib+'.pretty')/fp.name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fp,saved)
        pads=[x for x in parse(saved.read_text()) if isinstance(x,list) and x and x[0]=='pad']
        assert all(p[2]=='thru_hole' for p in pads)
        footprints[c['footprint']]=dict(sha256=sha(saved),pads=sorted(p[1] for p in pads),all_through_hole=True)
    expected175={'1':'~Mr','2':'Q0','3':'~Q0','4':'D0','5':'D1','6':'~Q1','7':'Q1','8':'GND',
        '9':'Cp','10':'Q2','11':'~Q2','12':'D2','13':'D3','14':'~Q3','15':'Q3','16':'VCC'}
    for b in inv['boards']:
        source=ROOT/b['source'];assert sha(source)==inv['source_hashes'][b['source']]
        input_hashes[b['source']]=sha(source)
        original=read_sheet(source);orig=inventory(original);byref={p['ref']:p for p in orig['packages']}
        for c in original['components']:
            p=ROOT/c['library_source'];input_hashes[c['library_source']]=sha(p)
        def edit(match):
            block=match.group(0);ref=re.search(r'^L \S+ (\S+)$',block,re.M)[1]
            p=byref.get(ref)
            if not p or p['value'] not in choices:return block
            choice=choices[p['value']]
            for field,old,new in [(1,p['value'],choice['part']),(2,p['footprint'],choice['footprint'])]:
                block,n=re.subn(r'^(F '+str(field)+r' )"'+re.escape(old)+'"',lambda m:m[1]+'"'+new+'"',block,flags=re.M)
                assert n==1
            return block
        text=re.sub(r'^\$Comp\n.*?^\$EndComp',edit,source.read_text(),flags=re.M|re.S)
        target=HERE/'circuits'/source.name;target.parent.mkdir(exist_ok=True);target.write_text(text)
        candidate=read_sheet(target);actual=inventory(candidate)
        assert not actual['issues'],actual['issues']
        assert groups(original)==groups(candidate)
        nets=connectivity(original);by_node={tuple(n):g for g in nets for n in g['nodes']}
        for p in actual['packages']:
            old=byref[p['ref']];choice=choices.get(old['value'])
            assert not p['footprint'].startswith('Package_SO:'),(b['board'],p)
            if choice:
                assert p['value']==choice['part'] and p['footprint']==choice['footprint']
                pins={pin['number'] for c in candidate['components'] if c['ref']==p['ref'] for pin in c['pins']}
                assert pins==set(footprints[p['footprint']]['pads'])
                changes.append(dict(board=b['board'],reference=p['ref'],before=old['value'],after=p['value'],footprint=p['footprint']))
            else:assert p==old
            packages.append(dict(board=b['board'],**p))
            if old['value']=='CD74AC175M96':
                pins={pin['number']:pin['name'] for c in candidate['components'] if c['ref']==p['ref'] for pin in c['pins']}
                assert pins==expected175,(b['board'],p['ref'],'ACT175 pin functions')
                net=lambda pin:by_node[(p['ref'],str(pin))]
                reset=net(1);clock=net(9)
                assert reset['labels'] and not set(reset['labels'])&{'VCC','+5V','GND'}
                used=[pin for pin in (3,6,11,14) if len(net(pin)['nodes'])>1 or net(pin)['labels']]
                roles.append(dict(board=b['board'],reference=p['ref'],clock=clock['labels'],reset=reset['labels'],complement_pins_used=used,
                    direct_574_substitution=False,reason='Asynchronous clear is connected; HCT574 has no clear input.'))
        native=validate(candidate,HERE/'native'/b['board']);assert native['status']=='pass',native
        tree=ET.parse(HERE/'native'/b['board']/(target.stem+'.xml')).getroot();verify_export(tree,candidate)
        boards.append(dict(board=b['board'],original=b['source'],original_sha256=sha(source),candidate=str(target.relative_to(HERE)),
            sha256=sha(target),native=native))
    assert Counter(c['before'] for c in changes)=={k:v['quantity'] for k,v in choices.items()}
    assert len(changes)==91 and len(roles)==48
    assert sum(bool(r['complement_pins_used']) for r in roles)==3
    # A 273-like consolidation needs identical clock AND physical reset leaf.
    packing=defaultdict(list)
    for r in roles:
        if not r['complement_pins_used']:packing[(r['board'],tuple(r['clock']),tuple(r['reset']))].append(r['reference'])
    pairs=[dict(board=k[0],clock=list(k[1]),reset=list(k[2]),references=refs[i:i+2]) for k,refs in packing.items() for i in range(0,len(refs)-1,2)]
    write('register-review.json',dict(positions=roles,same_clock_reset_pairs=pairs,
        scope='Connectivity screen for possible eight-bit resettable-register consolidation; requires rewiring, exact 273 part/timing/load review. HCT574 cannot preserve asynchronous reset.'))
    # Exercise the independent native-output comparison, including active-low reset and Q-bar pins.
    sheet=read_sheet(HERE/'circuits/Reset-C1.sch')
    original=ET.parse(HERE/'native/C1/Reset-C1.xml').getroot();faults=[]
    for fault in ('restore-soic-value','restore-soic-footprint','remove-reset-pin','swap-q-qbar'):
        bad=deepcopy(original);part=next(p for p in bad.findall('./components/comp') if p.attrib['ref']=='U1')
        if fault=='restore-soic-value':part.find('value').text='CD74AC175M96'
        elif fault=='restore-soic-footprint':part.find('footprint').text='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'
        else:
            nodes=[(net,n) for net in bad.findall('./nets/net') for n in net.findall('node') if n.attrib['ref']=='U1']
            if fault=='remove-reset-pin':
                net,node=next((net,n) for net,n in nodes if n.attrib['pin']=='1');net.remove(node)
            else:
                for _,n in nodes:
                    if n.attrib['pin'] in ('2','3'):n.attrib['pin']={'2':'3','3':'2'}[n.attrib['pin']]
        try:verify_export(bad,sheet)
        except AssertionError as e:faults.append(dict(fault=fault,detected=True,diagnostic=str(e)))
        else:raise AssertionError('Escaped mutation: '+fault)
    for source,digest in input_hashes.items():
        assert sha(ROOT/source)==digest
        dest=HERE/'sources/original'/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,dest)
    assert sources()==before
    write('packages.json',packages)
    write('summary.json',dict(passed=True,scope=config['scope'],changed_packages=len(changes),changed_types=len(choices),
        remaining_soic=0,remaining_non_dip_memory=sum(p['value']=='SST39SF040-70-4I-NHE' for p in packages),
        boards=boards,changes=changes,footprints=footprints,manufacturer_evidence=evidence,source_hashes=input_hashes,
        faults=faults,all_175_positions_require_reset=True,complement_output_positions=3,potential_273_pairs=len(pairs),
        normal_sources_unchanged=True,integrated_timing_qualified=False,physical_qualified=False,procurement_ready=False))
    print('DL1:',len(changes),'DIP substitutions;',len(boards),'native sheets; zero SOIC;',len(pairs),'possible 273 pairs;',len(faults),'faults rejected')


if __name__=='__main__':main()

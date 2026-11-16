"""CA1: CN1 CPU connectors with separate unmated native card-net domains."""
from collections import defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import connector_plan,native_assembly as na,native_assembly_evidence as nae
from .native_migrate import blocks
from .sexpr import parse,child,quote

STUDY=BUILD/'cp1-connector-assembly'
CANONICAL=ROOT/'Circuits/KiCad/Integrated/candidates/CA1'
FAULTS=('reversed-contact-row','missing-memory-read','source-bus-alias','global-bypass')
SOURCES=['Verification/dm02/connector_assembly.py','Verification/dm02/connector_plan.py',
    'Verification/dm02/native_assembly.py','Verification/dm02/native_migrate.py','Verification/dm02/sexpr.py',
    'Verification/native-assembly-evidence.json','Verification/mechanical-contract.json']
require=na.require


def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'dm02/CP1-CA1/'+name))


def groups_from_xml(tree):
    return {frozenset((p.get('ref'),p.get('pin')) for p in n.findall('node')) for n in tree.findall('./nets/net')}


def differences(wanted,actual):
    return [dict(kind='missing' if g in wanted else 'extra',pins=[list(p) for p in sorted(g)])
        for g in sorted(wanted^actual,key=lambda g:sorted(g))]


class Assembly:
    def __init__(self):
        self.base=na.Assembly();self.plan=connector_plan.generate();connector_plan.validate(self.plan)
        self.roles={b:role for role,boards in connector_plan.GROUPS.items() for b in boards}
        self.roles.update(MQ1='memory',BR1='active-backplane',TX1='text')
        self.components={c['reference']:dict(c,board=b,source_reference=r,role=self.roles[b])
            for (b,r),c in self.base.components.items() if c['fitted']}
        self.removed={c['reference'] for c in self.base.components.values() if not c['fitted']}
        self.contacts=[];self.connectors=[]
        self.expected=defaultdict(set)
        for pin,n in self.base.pins.items():
            ref=self.base.refs[pin[:2]]
            if ref not in self.removed:self.expected[self.label(pin[0],self.base.aliases[n])].add((ref,pin[2]))
        for card in self.plan['cpu_cards']:
            for number,conn in enumerate(card['connectors']):
                index=(card['position']-1)*2+number+1
                refs=('J'+str(15000+index),'J'+str(16000+index))
                for side,ref in zip(('card','backplane'),refs):
                    original=self.base.components[('TX1','J1') if side=='card' else ('BR1','J5')]
                    self.components[ref]=dict(original,reference=ref,board='CN1',source_reference=None,
                        role=card['role'] if side=='card' else 'active-backplane',side=side)
                    self.connectors.append(dict(reference=ref,role=card['role'],side=side,position=card['position'],
                        connector=conn['ref'],index=index))
                for p in conn['pins']:
                    signal=p['net'];alias=self.alias(card['role'],signal) if signal else None
                    labels=[self.label_role(role,alias) if alias else None for role in (card['role'],'active-backplane')]
                    record=dict(role=card['role'],position=card['position'],connector=conn['ref'],pin=p['pin'],
                        kind=p['kind'],signal=signal,card_reference=refs[0],backplane_reference=refs[1],
                        card_net=labels[0],backplane_net=labels[1])
                    self.contacts.append(record)
                    for ref,label in zip(refs,labels):self.expected[label or ('NC',ref,p['pin'])].add((ref,p['pin']))
        require(len(self.contacts)==768 and len(self.connectors)==16,'Incomplete CPU connector plan')

    def label_role(self,role,alias):
        # The existing NA1 text/backplane mating is retained. Only CPU domains split here.
        domain=role if role in connector_plan.GROUPS and role!='active-backplane' else 'backplane-text'
        return 'CA1_'+domain+'__'+alias

    def label(self,b,alias):return self.label_role(self.roles[b],alias)

    def alias(self,role,signal):
        if signal in ('5V','GND'):return self.base.aliases['C1',signal]
        if signal.startswith('LIVE_ADDRESS') or signal=='IO_READ_VALID':return self.base.aliases['MQ1',signal]
        endpoints=self.plan['native_boundary']['nets'][signal]
        node=next(e for e in endpoints if e['group']==role)
        return self.base.aliases[node['board'],node['local_net']]

    def baseline_groups(self):
        return {frozenset(p for p in g if p[0] not in self.removed) for g in self.base.expected()
            if any(p[0] not in self.removed for p in g)}

    def connector_sheet(self,fault=None):
        source=(nae.CANONICAL/'TX1.kicad_sch').read_text()
        lib=next(b for b in blocks(source) if b.startswith('(lib_symbols'))
        symbol=next(b for b in blocks(lib) if b.startswith('(symbol "NA1_TX1:J1"'))
        symbol=symbol.replace('"NA1_TX1:J1"','"CA1:DIN96"',1)
        symbol=re.sub(r'\(symbol "J1_(\d+_\d+)"',r'(symbol "DIN96_\1"',symbol)
        pins={}
        for unit in [x for x in parse(symbol) if isinstance(x,list) and x[0]=='symbol']:
            for pin in [x for x in unit if isinstance(x,list) and x[0]=='pin']:
                pins[child(pin,'number')[1]]=tuple(map(float,child(pin,'at')[1:3]))
        require(set(pins)==set(connector_plan.CONTACTS),'DIN symbol pin set changed')
        out=['(kicad_sch (version 20250114) (generator "dm02_ca1")',f'(uuid {uid("connector-root")})',
            '(paper "User" 1300 420)', '(title_block (title "CP1-CA1 CPU card/backplane contacts") (rev "CP1-CA1")',
            '(comment 1 "Logical contact-number mating; exact fit/orientation and physical qualification open"))',
            '(lib_symbols '+symbol+')']
        for conn in self.connectors:
            ref=conn['reference'];c=self.components[ref];i=conn['index']-1
            x=100+(i%4)*315+(130 if conn['side']=='backplane' else 0);y=40+(i//4)*180
            out.append(f'''(symbol (lib_id "CA1:DIN96") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})
 (property "Reference" "{ref}" (at {x} {y-7} 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{c['value']}" (at {x} {y-4} 0) (effects (font (size 1.27 1.27))))
 (property "Footprint" "{c['footprint']}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
 (property "CardRole" "{conn['role']} {conn['connector']} {conn['side']}" (at {x} {y+125} 0) (effects (font (size 1.27 1.27))))
 (instances (project "CA1" (path "/{uid('root')}/{uid('contacts')}" (reference "{ref}") (unit 1)))))''')
            rows={p['pin']:p for p in self.contacts if p['card_reference' if conn['side']=='card' else 'backplane_reference']==ref}
            for number,(px,py) in pins.items():
                selected=number
                if fault=='reversed-contact-row' and ref=='J15005' and number[0] in 'ac':
                    selected=('c' if number[0]=='a' else 'a')+number[1:]
                row=rows[selected];label=row['card_net' if conn['side']=='card' else 'backplane_net']
                if fault=='missing-memory-read' and conn['side']=='card' and row['signal']=='IO_READ_VALID':label=None
                if fault=='source-bus-alias' and conn['side']=='card' and conn['role']=='compute' and row['signal']=='BRANCH0_0':
                    label=self.label_role('compute',self.alias('compute','DATA0'))
                if label is None:out.append(f'(no_connect (at {x+px} {y-py}) (uuid {uid(ref+number)}))')
                else:out.append(f'(global_label {quote(label)} (shape bidirectional) (at {x+px} {y-py} 0) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid {uid(ref+number)}))')
        return '\n'.join(out+[')',''])

    def documents(self,fault=None):
        require(fault is None or fault in FAULTS,'Unknown CA1 mutation')
        docs={}
        for b in na.BOARDS:
            original=(nae.CANONICAL/(b+'.kicad_sch')).read_text()
            source_blocks=blocks(original)
            lib=next(p for p in source_blocks if p.startswith('(lib_symbols'))
            symbols={parse(p)[1]:parse(p) for p in blocks(lib) if p.startswith('(symbol ')}
            removed_points=set()
            for block in source_blocks:
                if not block.startswith('(symbol (lib_id '):continue
                node=parse(block);ref=next(p[2] for p in node if isinstance(p,list) and p[:2]==['property','Reference'])
                if ref not in self.removed:continue
                at=child(node,'at');require(float(at[3])==0 and child(node,'mirror') is None,'Unsupported boundary marker orientation')
                x,y=map(float,at[1:3]);symbol=symbols[child(node,'lib_id')[1]]
                for unit in [p for p in symbol if isinstance(p,list) and p[0]=='symbol']:
                    for pin in [p for p in unit if isinstance(p,list) and p[0]=='pin']:
                        px,py=map(float,child(pin,'at')[1:3]);removed_points.add((round(x+px,5),round(y-py,5)))
            out=[]
            for block in source_blocks:
                if block.startswith('(symbol (lib_id '):
                    ref=next(p[2] for p in parse(block) if isinstance(p,list) and p[:2]==['property','Reference'])
                    if ref in self.removed:continue
                if block.startswith(('(global_label ','(label ','(no_connect ')):
                    at=child(parse(block),'at');point=tuple(round(float(v),5) for v in at[1:3])
                    if point in removed_points:continue
                if block.startswith('(global_label '):
                    old=parse(block)[1];label=self.label(b,old)
                    block=re.sub(r'^\(global_label "(?:\\.|[^"\\])*"',lambda _: '(global_label '+quote(label),block)
                block=block.replace(na.uid('root'),uid('root')).replace('(project "NA1"','(project "CA1"')
                block=block.replace('CP1-NA1','CP1-CA1')
                out.append(block)
            docs[b+'.kicad_sch']='(kicad_sch\n'+'\n'.join(out)+'\n)\n'
        docs['CN1.kicad_sch']=self.connector_sheet(fault)
        root=(nae.CANONICAL/'NA1.kicad_sch').read_text().replace(na.uid('root'),uid('root')).replace('(project "NA1"','(project "CA1"')
        root=root.replace('R2 + BR1 + TX1 native connectivity candidate','CPU connector assembly candidate').replace('CP1-NA1','CP1-CA1')
        sheet=f'''(sheet (at 270 210) (size 100 25) (stroke (width 0) (type default)) (fill (color 0 0 0 0)) (uuid {uid('contacts')})
 (property "Sheetname" "CPU contacts" (at 270 209 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
 (property "Sheetfile" "CN1.kicad_sch" (at 270 236 0) (effects (font (size 1.27 1.27)) (justify left top)))
 (instances (project "CA1" (path "/{uid('root')}" (page "16")))))'''
        root=root.rsplit(')',1)[0]+sheet+'\n)\n';docs['CA1.kicad_sch']=root
        if fault=='global-bypass':
            docs={name:re.sub(r'CA1_(control|compute|counters|memory)__', 'CA1_backplane-text__',text) for name,text in docs.items()}
        return docs

    def compare(self,path):
        tree=ET.parse(path).getroot();actual=groups_from_xml(tree)
        expected={frozenset(g) for g in self.expected.values()}
        parts={p.get('ref'):p for p in tree.findall('./components/comp')}
        libraries={(p.get('lib'),p.get('part')):na.pin_signature(p) for p in tree.findall('./libparts/libpart')}
        identity=set(parts)==set(self.components)
        for ref,c in self.components.items():
            if ref not in parts:identity=False;continue
            p=parts[ref];key=tuple(p.find('libsource').get(k) for k in ('lib','part'))
            props={x.get('name') for x in p.findall('property')}
            identity &= ((p.findtext('value'),p.findtext('footprint') or '')==(c['value'],c['footprint']) and
                libraries.get(key)==c['pin_signature'] and not props&{'exclude_from_bom','exclude_from_board'})
        parent={p:p for g in actual for p in g}
        def root(p):
            while parent[p]!=p:p=parent[p]
            return p
        def join(a,b):
            x,y=root(a),root(b);parent[max(x,y)]=min(x,y)
        for g in actual:
            pins=sorted(g)
            for p in pins[1:]:join(pins[0],p)
        for row in self.contacts:
            a=(row['card_reference'],row['pin']);b=(row['backplane_reference'],row['pin'])
            require(a in parent and b in parent,'Missing CA1 physical contact')
            join(a,b)
        projected=defaultdict(set)
        connector_refs={c['reference'] for c in self.connectors}
        for p in parent:
            if p[0] not in connector_refs:projected[root(p)].add(p)
        projected={frozenset(g) for g in projected.values()}
        unmated=differences(expected,actual);mated=differences(self.baseline_groups(),projected)
        # Check each domain before mating; this rejects a hidden common-label bypass
        # even when its fully mated functional graph looks correct.
        return dict(passed=bool(identity) and not unmated and not mated,component_identity_match=bool(identity),
            unmated_differences=unmated,mated_functional_differences=mated,components=len(parts),dip_count=sum(r.startswith('U') for r in parts),
            fitted_cpu_connectors=16,contact_pairs=len(self.contacts),physical_contact_pins=len(self.contacts)*2,
            memory_extensions=17,removed_boundary_markers=len(self.removed),net_groups=len(actual),
            physical_pins=sum(map(len,actual)),functional_net_groups=len(projected),
            physical_qualification=False,promoted_into_R2=False,new_dynamic_simulation=False)

    def provenance(self):
        paths=list(nae.CANONICAL.glob('*.kicad_sch'))
        return dict(revision='CP1-CA1',source_hashes={n:digest(ROOT/n) for n in SOURCES},
            native_source_hashes={str(p.relative_to(ROOT)):digest(p) for p in paths},
            contacts=self.contacts,components=self.components,removed_boundary_markers=sorted(self.removed),
            scope='Separate CPU-card and backplane/text domains; analytical contact-number mating only. Exact connector fit/orientation, loads and physical operation remain open.')

    def generate(self,folder,fault=None):
        folder=Path(folder);require(not folder.exists(),'Preserve CA1 attempt');folder.mkdir(parents=True)
        for name,text in self.documents(fault).items():(folder/name).write_text(text)
        write_json(folder/'provenance.json',self.provenance())
        code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',folder/'CA1.xml',folder/'CA1.kicad_sch'])
        (folder/'export.log').write_text(log);require(code==0,'CA1 export failed: '+log)
        result=dict(self.compare(folder/'CA1.xml'),fault=fault);write_json(folder/'comparison.json',result)
        return result


def run(folder):
    nae.load();a=Assembly();folder=Path(folder);require(not folder.exists(),'Preserve CA1 study');folder.mkdir(parents=True)
    result=a.generate(folder/'native');require(result['passed'],'CA1 native parity failed')
    mutations={f:a.generate(folder/f,f) for f in FAULTS}
    require(all(not r['passed'] for r in mutations.values()),'Undetected CA1 mutation')
    write_json(folder/'summary.json',dict(revision='CP1-CA1',accepted_revision='CP1-R2',native=result,mutations=mutations,
        physical_qualification=False,promoted_into_R2=False,new_dynamic_simulation=False))
    print('CA1:',result,'detected mutations:',len(mutations))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();run(args.output)

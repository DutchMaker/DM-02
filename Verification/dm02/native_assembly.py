"""NA1 native hierarchy: pinned R2 + MQ1/BR1 + TX1 physical pin composition."""
from collections import Counter,defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import math
import re
import uuid
import xml.etree.ElementTree as ET
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import connector_plan,io_bridge,io_bridge_boundary,text_card,text_boot_evidence
from .native_migrate import blocks
from .sexpr import parse,child,quote

BOARDS=('C1','CW1','SQ1','PC1','AL1','RG1','SP1','MA1','ME1','BF1','DT1','MQ1','BR1','TX1')
STUDY=BUILD/'cp1-native-assembly'
require=io_bridge.require
SOURCES=['Verification/dm02/native_assembly.py','Verification/dm02/native_migrate.py',
    'Verification/dm02/sexpr.py','Verification/dm02/connector_plan.py',
    'Verification/dm02/io_bridge_boundary.py','Verification/targets/cp1/lock.json',
    'Verification/bridge-evidence.json','Verification/text-evidence.json','Verification/text-boot-evidence.json',
    'Circuits/KiCad/IO-Bridge/candidates/boundary.json','Circuits/KiCad/Text/candidates/boundary.json',
    'Verification/hdl/text_cpu_probe.sv','Verification/dm02/io_bridge.py','Verification/dm02/text_card.py']


def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'dm02/CP1-NA1/'+name))


def inputs():
    locks=[json.loads((VROOT/p).read_text()) for p in ('targets/cp1/lock.json','bridge-evidence.json','text-evidence.json')]
    paths={b:(BUILD/(f'cp1-hct273/native/{b}' if i<11 else
        f'cp1-bridge/native/{b}' if b!='TX1' else 'cp1-text/iteration-2/native/TX1')) for i,b in enumerate(BOARDS)}
    hashes={}
    for b,folder in paths.items():
        lock=locks[0 if b in BOARDS[:11] else 2 if b=='TX1' else 1]
        for ext in ('xml','kicad_sch'):
            p=folder/(b+'.'+ext);name=str(p.relative_to(BUILD))
            require(digest(p)==lock['artifacts'][name],'Changed native assembly input: '+name)
            hashes[name]=digest(p)
    return paths,hashes


class Assembly:
    def __init__(self):
        self.paths,self.hashes=inputs();self.components={};self.pins={};self.nets={};self.parent={}
        self.refs={};self.joins=[];self.contacts=[]
        for index,(b,folder) in enumerate(self.paths.items(),1):
            tree=ET.parse(folder/(b+'.xml')).getroot()
            libraries={(p.get('lib'),p.get('part')):pin_signature(p) for p in tree.findall('./libparts/libpart')}
            for c in tree.findall('./components/comp'):
                ref=c.get('ref');m=re.fullmatch(r'([A-Za-z]+)(\d+)',ref)
                require(m and int(m[2])<1000,'Unsupported source annotation: '+ref)
                target=m[1]+str(index*1000+int(m[2]));self.refs[b,ref]=target
                fitted=not ref.startswith('J') or (b=='BR1' and ref in ('J5','J6','J7','J8')) or b=='TX1'
                self.components[b,ref]=dict(value=c.findtext('value'),footprint=c.findtext('footprint') or '',
                    reference=target,fitted=fitted,pin_signature=libraries[tuple(c.find('libsource').get(k) for k in ('lib','part'))])
            for net in tree.findall('./nets/net'):
                n=(b,net.get('name').removeprefix('/'));require(n not in self.nets,'Duplicate native net name')
                self.parent[n]=n;self.nets[n]=[]
                for p in net.findall('node'):
                    pin=b,p.get('ref'),p.get('pin');require(pin not in self.pins,'Duplicate source pin')
                    self.pins[pin]=n;self.nets[n].append(pin)
        self.connect()

    def root(self,n):
        while self.parent[n]!=n:n=self.parent[n]
        return n

    def join(self,a,b,reason):
        require(a in self.pins and b in self.pins,'Missing assembly boundary pin')
        x,y=self.root(self.pins[a]),self.root(self.pins[b]);self.parent[max(x,y)]=min(x,y)
        self.joins.append(dict(a=list(a),b=list(b),reason=reason))

    def connect(self):
        baseline=connector_plan.native_boundary();self.hashes.update(baseline['source_hashes'])
        # Locked BP1 establishes aliases; equal local names never imply a join.
        for signal,endpoints in baseline['nets'].items():
            pins=[(e['board'],e['connector'],e['pin']) for e in endpoints if e['board']!='BP1']
            for p in pins[1:]:self.join(pins[0],p,'R2 BP1 '+signal)
        boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
        circuit=io_bridge.Circuit(BUILD/'cp1-bridge/native',boundary)
        self.binding=io_bridge_boundary.audit(circuit,baseline)
        for row in self.binding['bindings']:
            old=row['r2_endpoint']
            self.join((row['board'],row['connector'],row['pin']),
                (old['board'],old['connector'],old['pin']),'BR1 binding '+row['assembly_net'])
        for row in self.binding['memory_extensions']:
            p=row['logical_pin'];self.join(('MQ1','J2',p),('BR1','J2',p),'CN1 extension '+row['signal'])
        # Candidate uses a common qualified rail, as in BR1/TX1. No isolation inferred.
        for supply in ('5V','GND'):
            nodes=[self.nets[b,supply][0] for b in BOARDS]
            for p in nodes[1:]:self.join(nodes[0],p,'Common supply '+supply)
        # Logical contact-number mating only: actual connector orientation remains open.
        for contact in connector_plan.CONTACTS:
            a=('BR1','J5',contact);b=('TX1','J1',contact)
            require(a in self.pins and b in self.pins,'Missing DIN96 contact')
            an,bn=self.pins[a][1],self.pins[b][1]
            used=not an.startswith('unconnected-')
            require(used==not_unconnected(bn),'Slot5 NC assignment differs')
            if used:self.join(a,b,'Slot5 contact '+contact)
            self.contacts.append(dict(pin=contact,bridge_net=an,text_net=bn,connected=used))
        self.aliases={n:self.net_name(n) for n in self.nets}
        require(self.root(('C1','5V'))!=self.root(('C1','GND')),'Assembly shorts supply rails')
        require(self.root(('BR1','RESET_n'))!=self.root(('MQ1','ME1_RESET_n')),'Assembly shorts reset branches')

    def net_name(self,n):
        group=[k for k in self.nets if self.root(k)==self.root(n)]
        for power in ('GND','5V'):
            if any(k[1]==power for k in group):return 'NA1_'+power
        b,label=min(group)
        return 'NA1_'+b+'__'+label

    def expected(self):
        groups=defaultdict(list)
        for pin,n in self.pins.items():groups[self.root(n)].append((self.refs[pin[:2]],pin[2]))
        return {frozenset(pins) for pins in groups.values()}

    def source_manifest(self):
        return dict(revision='CP1-NA1',accepted_revision='CP1-R2',physical_qualification=False,
            promoted_into_R2=False,source_hashes={n:digest(ROOT/n) for n in SOURCES},input_hashes=self.hashes,
            components=[dict(board=b,source_reference=r,**c) for (b,r),c in self.components.items()],
            joins=self.joins,slot5_contacts=self.contacts)

    def model_bindings(self,path):
        """Resolve added module ports in the exported hierarchy against TB1 wiring.

        R2 internal connections come from locked BP1. This checks the added
        connections, not analog loading or a new simulation of the hierarchy.
        """
        require(self.compare(path)['passed'],'Model binding requires complete native parity')
        tree=ET.parse(path).getroot();nodes={}
        for net in tree.findall('./nets/net'):
            for n in net.findall('node'):nodes[n.get('ref'),n.get('pin')]=net.get('code')
        def net(pin):return nodes[self.refs[pin[:2]],pin[2]]
        rows=[]
        for binding in self.binding['bindings']:
            old=binding['r2_endpoint'];a=(binding['board'],binding['connector'],binding['pin'])
            b=(old['board'],old['connector'],old['pin'])
            require(net(a)==net(b),'NA1 exported CPU/bridge port differs')
            rows.append(dict(signal=binding['assembly_net'],pins=[list(a),list(b)],native_net=net(a)))
        for row in self.binding['memory_extensions']:
            a=('MQ1','J2',row['logical_pin']);b=('BR1','J2',row['logical_pin'])
            require(net(a)==net(b),'NA1 exported memory extension differs')
            rows.append(dict(signal=row['signal'],pins=[list(a),list(b)],native_net=net(a)))
        tx=json.loads((text_card.SOURCE/'boundary.json').read_text())['ports']['J1']
        bridge=json.loads((io_bridge.SOURCE/'boundary.json').read_text())['ports']['BR1']['J5']
        for p,signal in bridge.items():
            a=('BR1','J5',p);b=('TX1','J1',p)
            require(net(a)==net(b),'NA1 exported slot5 contact differs')
            rows.append(dict(signal=signal,text_signal=tx[p],pins=[list(a),list(b)],native_net=net(a)))
        require(net(('MQ1','J1','21'))!=net(('BR1','J4','3')),'Reset branches merged')
        for bit in range(8):
            require(net(('BR1','J1',str(bit+3)))!=net(('BR1','J2',str(bit+3))),'Read/write addresses merged')
        # Fail closed if the reused TB1 composition changes its argument ordering.
        probe=re.sub(r'\s+','',(VROOT/'hdl/text_cpu_probe.sv').read_text())
        require('bridge_dutbridge(mar,mem_n,load_n[10],reset_n,ME1_RESET_n,physical_memory.io_address,physical_memory.io_data,physical_memory.io_strobe,card_data,{3\'b110,ABSENT[0]},bridge_result,slot_waddr,slot_wdata,slot_raddr,slot_strobe,slot_read,slot_reset);' in probe,'TB1 bridge wiring changed')
        require('text_duttext_card(text_osc,slot_reset[0],slot_waddr[7:0],slot_wdata[7:0],slot_strobe[0],slot_raddr[7:0],slot_read[0],text_status,serial_tx);' in probe,'TB1 text wiring changed')
        return dict(passed=True,bindings=rows,reset_branches_distinct=True,read_write_addresses_distinct=True,
            tb1_lock_sha256=digest(text_boot_evidence.LOCK),new_simulation=False,
            scope='Native pin-graph and explicit port-binding equivalence to the TB1 composition. TB1 slot6 fixture is external behavioral test equipment; supply/clocks and loading remain assumed.')

    def sheet(self,b,fault=None):
        text=(self.paths[b]/(b+'.kicad_sch')).read_text();output=[]
        positions=[child(parse(block),'at') for block in blocks(text) if block.startswith('(symbol (lib_id ') or block.startswith('(label ')]
        width=max(420,math.ceil((max(float(p[1]) for p in positions)+50)/10)*10)
        height=max(297,math.ceil((max(float(p[2]) for p in positions)+50)/10)*10)
        for block in blocks(text):
            if block.startswith('(paper '):
                block=f'(paper "User" {width} {height})\n(title_block (title "CP1-NA1 {b} connectivity candidate") (rev "CP1-NA1") (comment 1 "Inherited functional layout; physical and production acceptance open"))'
            elif block.startswith('(label '):
                local=parse(block)[1];require((b,local) in self.aliases,'Unknown source label')
                label=self.aliases[b,local]
                if fault=='merged-reset' and b=='MQ1' and local=='ME1_RESET_n':label=self.aliases['BR1','RESET_n']
                if fault=='stale-read-address' and b=='BR1' and local=='LIVE_ADDRESS0':label=self.aliases['BR1','IO_ADDRESS0']
                if fault=='private-return-alias' and b=='TX1' and local=='R_DATA0':label=self.aliases['BR1','SLOT6_R_DATA0']
                block=re.sub(r'^\(label "(?:\\.|[^"\\])*"',lambda _: '(global_label '+quote(label)+' (shape bidirectional)',block)
            elif block.startswith('(symbol (lib_id '):
                node=parse(block);old=next(p[2] for p in node if isinstance(p,list) and p[:2]==['property','Reference'])
                c=self.components[b,old];new=c['reference']
                block=block.replace('(property "Reference" '+quote(old),'(property "Reference" '+quote(new),1)
                instances=next(p for p in blocks(block) if p.startswith('(instances '))
                unit=child(node,'unit')[1]
                block=block.replace(instances,f'(instances (project "NA1" (path "/{uid("root")}/{uid(b)}" (reference {quote(new)}) (unit {unit}))))')
                if not c['fitted']:
                    block=block.replace('(in_bom yes)','(in_bom no)').replace('(on_board yes)','(on_board no)')
                # Retain source value/footprint and embedded library geometry unchanged.
            output.append(block)
        # A hierarchy must not reuse DM02:U1 for unrelated symbols on different sheets.
        return ('(kicad_sch\n'+'\n'.join(output)+'\n)\n').replace('"DM02:',quote('NA1_'+b+':')[:-1])

    def documents(self,fault=None):
        documents={b+'.kicad_sch':self.sheet(b,fault) for b in BOARDS}
        root=['(kicad_sch (version 20250114) (generator "dm02_na1")',f'(uuid {uid("root")}) (paper "A3") (lib_symbols)',
            '(title_block (title "R2 + BR1 + TX1 native connectivity candidate") (rev "CP1-NA1") (comment 1 "270 DIP ICs; physical and production acceptance open"))']
        for i,b in enumerate(BOARDS):
            x=20+(i%3)*125;y=30+(i//3)*45
            root.append(f'''(sheet (at {x} {y}) (size 100 25) (stroke (width 0) (type default))
 (fill (color 0 0 0 0)) (uuid {uid(b)})
 (property "Sheetname" "{b}" (at {x} {y-1} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
 (property "Sheetfile" "{b}.kicad_sch" (at {x} {y+26} 0) (effects (font (size 1.27 1.27)) (justify left top)))
 (instances (project "NA1" (path "/{uid("root")}" (page "{i+2}")))))''')
        root+=['(sheet_instances (path "/" (page "1")))',')']
        documents['NA1.kicad_sch']='\n'.join(root)+'\n'
        return documents

    def generate(self,folder,fault=None):
        folder=Path(folder);require(not folder.exists(),'Preserve NA1 attempt: '+str(folder));folder.mkdir(parents=True)
        for name,text in self.documents(fault).items():(folder/name).write_text(text)
        write_json(folder/'provenance.json',self.source_manifest())
        code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',folder/'NA1.xml',folder/'NA1.kicad_sch'])
        (folder/'export.log').write_text(log);require(code==0,'Native assembly export failed: '+log)
        result=self.compare(folder/'NA1.xml');result['fault']=fault;write_json(folder/'comparison.json',result)
        if result['passed']:write_json(folder/'model-bindings.json',self.model_bindings(folder/'NA1.xml'))
        return result

    def compare(self,path):
        tree=ET.parse(path).getroot();expected=self.expected()
        libraries={(p.get('lib'),p.get('part')):pin_signature(p) for p in tree.findall('./libparts/libpart')}
        groups={frozenset((n.get('ref'),n.get('pin')) for n in net.findall('node')) for net in tree.findall('./nets/net')}
        actual={c.get('ref'):(c.findtext('value'),c.findtext('footprint') or '') for c in tree.findall('./components/comp')}
        wanted={c['reference']:(c['value'],c['footprint']) for c in self.components.values()}
        expected_by_ref={c['reference']:c for c in self.components.values()}
        symbols=True;fitted=True
        for c in tree.findall('./components/comp'):
            if c.get('ref') not in expected_by_ref:symbols=fitted=False;continue
            wanted_part=expected_by_ref[c.get('ref')]
            key=tuple(c.find('libsource').get(k) for k in ('lib','part'))
            symbols &= libraries.get(key)==wanted_part['pin_signature']
            props={p.get('name') for p in c.findall('property')}
            fitted &= (('exclude_from_bom' not in props)==wanted_part['fitted'] and
                       ('exclude_from_board' not in props)==wanted_part['fitted'])
        difference=[dict(kind='missing' if g in expected else 'extra',pins=[list(p) for p in sorted(g)])
                    for g in sorted(expected^groups,key=lambda g:sorted(g))]
        count=sum(r.startswith('U') for b,r in self.components)
        require(count==270,'Unexpected assembled DIP count')
        require(all(c['footprint'].startswith('Package_DIP:') for (b,r),c in self.components.items() if r.startswith('U')),'Non-DIP logic/memory')
        return dict(passed=actual==wanted and not difference and symbols and fitted,components=len(actual),dip_count=count,
            symbol_pin_metadata_match=bool(symbols),fitted_flags_match=bool(fitted),
            component_identity_match=actual==wanted,net_groups=len(groups),physical_pins=sum(map(len,groups)),
            differences=difference,slot5_contacts_checked=len(self.contacts),physical_qualification=False,
            fitted_components=sum(c['fitted'] for c in self.components.values()),
            boundary_markers=sum(not c['fitted'] for c in self.components.values()))


def not_unconnected(name):return not name.startswith('unconnected-')


def pin_signature(part):
    return sorted([dict(p.attrib) for p in part.findall('./pins/pin')],key=lambda p:p['num'])


def run(folder):
    text_boot_evidence.load();a=Assembly();folder=Path(folder)
    require(not folder.exists(),'Preserve NA1 study');folder.mkdir(parents=True)
    result=a.generate(folder/'native');require(result['passed'],'NA1 native parity failed')
    mutations={f:a.generate(folder/f, f) for f in ('merged-reset','stale-read-address','private-return-alias')}
    require(all(not r['passed'] for r in mutations.values()),'NA1 undetected mutation')
    write_json(folder/'summary.json',dict(revision='CP1-NA1',accepted_revision='CP1-R2',native=result,
        mutations=mutations,physical_qualification=False,promoted_into_R2=False))
    print('NA1 native assembly:',result,'mutations detected:',len(mutations))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();run(args.output)

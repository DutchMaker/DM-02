"""MD1: isolate ME1 address loads with two native SN74AHCT244N packages."""
from collections import defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET
from .common import ROOT,BUILD,digest,write_json,command
from . import connector_assembly as ca,connector_assembly_evidence as cae,link_loads as ll
from .native_migrate import blocks
from .sexpr import parse,child,quote

STUDY=BUILD/'cp1-mar-distribution'
CANONICAL=ROOT/'Circuits/KiCad/Integrated/candidates/MD1'
INPUTS=[2,4,6,8,17,15,13,11]
OUTPUTS=[18,16,14,12,3,5,7,9]
FAULTS=('swapped-address','buffer-bypass','disabled-buffer')
require=ca.require


def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'dm02/CP1-MD1/'+name))


class Candidate:
    def __init__(self):
        self.base=ll.Inventory();self.components=deepcopy(self.base.components)
        self.groups=defaultdict(set);self.addresses=[]
        tree=ET.parse(ll.NATIVE/'CA1.xml').getroot()
        for net in tree.findall('./nets/net'):
            self.groups[net.get('name')]={(p.get('ref'),p.get('pin')) for p in net.findall('node')}
        source=(ca.CANONICAL/'ME1.kicad_sch').read_text();lib=next(b for b in blocks(source) if b.startswith('(lib_symbols'))
        symbols={parse(b)[1]:b for b in blocks(lib) if b.startswith('(symbol ')}
        self.templates={}
        for kind,value in [('buffer','SN74AHCT244N'),('cap','100nF')]:
            ref=next(r for r,c in self.components.items() if c['board']=='ME1' and c['value']==value)
            instance=next(b for b in blocks(source) if b.startswith('(symbol (lib_id ') and
                any(isinstance(p,list) and p[:3]==['property','Reference',ref] for p in parse(b)))
            symbol=symbols[child(parse(instance),'lib_id')[1]];old=parse(symbol)[1]
            name='AHCT244' if kind=='buffer' else 'C';symbol=symbol.replace(quote(old),quote('MD1:'+name),1)
            symbol=re.sub(r'\(symbol "[^"\n]+_(\d+_\d+)"',lambda m:'(symbol "'+name+'_'+m[1]+'"',symbol)
            self.templates[kind]=dict(symbol=symbol,component=deepcopy(self.components[ref]),name=name)
        for i in (1,2):
            for prefix,kind in [('U','buffer'),('C','cap')]:
                ref=prefix+str(17000+i);c=deepcopy(self.templates[kind]['component'])
                c.update(reference=ref,board='MB1',source_reference=prefix+str(i),role='memory')
                self.components[ref]=c
        for bit in range(16):
            raw='CA1_memory__NA1_MA1__STATE'+str(bit);out='MD1_memory__ADDRESS'+str(bit)
            require(raw in self.groups,'Missing raw MAR bit')
            moved=sorted(p for p in self.groups[raw] if self.components[p[0]]['board']=='ME1')
            require(len(moved)==3,'Unexpected ME1 address receiver set')
            self.groups[raw]-=set(moved);self.groups[out].update(moved)
            ref='U'+str(17001+bit//8);inp=str(INPUTS[bit%8]);output=str(OUTPUTS[bit%8])
            self.groups[raw].add((ref,inp));self.groups[out].add((ref,output))
            self.addresses.append(dict(bit=bit,raw_net=raw,buffered_net=out,reference=ref,
                input_pin=inp,output_pin=output,moved_pins=[list(p) for p in moved]))
        self.rail={'5V':'CA1_memory__NA1_5V','GND':'CA1_memory__NA1_GND'}
        for i in (1,2):
            ref='U'+str(17000+i);cap='C'+str(17000+i)
            self.groups[self.rail['5V']].update([(ref,'20'),(cap,'1')])
            self.groups[self.rail['GND']].update([(ref,'10'),(ref,'1'),(ref,'19'),(cap,'2')])

    def buffer_sheet(self,fault=None):
        out=['(kicad_sch (version 20250114) (generator "dm02_md1")',f'(uuid {uid("buffer-root")})',
            '(paper "A3") (title_block (title "MD1 memory address isolation") (rev "CP1-MD1")',
            '(comment 1 "Two always-enabled SN74AHCT244N; conditional planning loads only"))',
            '(lib_symbols '+'\n'.join(t['symbol'] for t in self.templates.values())+')']
        for i in (1,2):
            for kind,prefix,x,y in [('buffer','U',70+(i-1)*190,60),('cap','C',120+(i-1)*190,60)]:
                ref=prefix+str(17000+i);c=self.components[ref];template=self.templates[kind]
                pins={}
                for unit in [p for p in parse(template['symbol']) if isinstance(p,list) and p[0]=='symbol']:
                    for pin in [p for p in unit if isinstance(p,list) and p[0]=='pin']:
                        pins[child(pin,'number')[1]]=tuple(map(float,child(pin,'at')[1:3]))
                names={p:net for net,group in self.groups.items() for r,p in group if r==ref}
                require(set(names)==set(pins),'Incomplete buffer package pin map')
                if fault=='disabled-buffer' and kind=='buffer' and i==1:names['1']=self.rail['5V']
                if fault=='swapped-address' and kind=='buffer' and i==1:names['18'],names['16']=names['16'],names['18']
                out.append(f'''(symbol (lib_id "MD1:{template['name']}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})
 (property "Reference" "{ref}" (at {x} {y-7} 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{c['value']}" (at {x} {y-4} 0) (effects (font (size 1.27 1.27))))
 (property "Footprint" "{c['footprint']}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
 (instances (project "MD1" (path "/{uid('root')}/{uid('MB1')}" (reference "{ref}") (unit 1)))))''')
                for pin,(px,py) in pins.items():
                    out.append(f'(global_label {quote(names[pin])} (shape bidirectional) (at {x+px} {y-py} 0) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid {uid(ref+pin)}))')
        return '\n'.join(out+[')',''])

    def documents(self,fault=None):
        require(fault is None or fault in FAULTS,'Unknown MD1 fault')
        docs={}
        for source in sorted(ca.CANONICAL.glob('*.kicad_sch')):
            text=source.read_text().replace(ca.uid('root'),uid('root')).replace('(project "CA1"','(project "MD1"')
            text=text.replace('CP1-CA1','CP1-MD1')
            if source.stem=='ME1':
                for row in self.addresses:text=text.replace(quote(row['raw_net']),quote(row['buffered_net']))
            name=source.name
            if source.stem=='CA1':
                name='MD1.kicad_sch';text=text.replace('CPU connector assembly candidate','Buffered memory address candidate')
                sheet=f'''(sheet (at 20 255) (size 100 25) (stroke (width 0) (type default)) (fill (color 0 0 0 0)) (uuid {uid('MB1')})
 (property "Sheetname" "MB1" (at 20 254 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
 (property "Sheetfile" "MB1.kicad_sch" (at 20 281 0) (effects (font (size 1.27 1.27)) (justify left top)))
 (instances (project "MD1" (path "/{uid('root')}" (page "17")))))'''
                text=text.rsplit(')',1)[0]+sheet+'\n)\n'
            docs[name]=text
        docs['MB1.kicad_sch']=self.buffer_sheet(fault)
        if fault=='buffer-bypass':
            for row in self.addresses:
                docs={name:text.replace(quote(row['buffered_net']),quote(row['raw_net'])) for name,text in docs.items()}
        return docs

    def compare(self,path):
        tree=ET.parse(path).getroot();groups=ca.groups_from_xml(tree)
        wanted={frozenset(g) for g in self.groups.values()};delta=ca.differences(wanted,groups)
        components={c.get('ref'):c for c in tree.findall('./components/comp')}
        libraries={(p.get('lib'),p.get('part')):ca.na.pin_signature(p) for p in tree.findall('./libparts/libpart')}
        identity=set(components)==set(self.components)
        for ref,c in self.components.items():
            if ref not in components:identity=False;continue
            actual=components[ref];key=tuple(actual.find('libsource').get(k) for k in ('lib','part'))
            identity &= (actual.findtext('value')==c['value'] and (actual.findtext('footprint') or '')==c['footprint'] and
                libraries[key]==c['pin_signature'] and not {p.get('name') for p in actual.findall('property')}&{'exclude_from_bom','exclude_from_board'})
        parent={p:p for g in groups for p in g}
        def root(p):
            while parent[p]!=p:p=parent[p]
            return p
        def join(a,b):
            x,y=root(a),root(b);parent[max(x,y)]=min(x,y)
        for group in groups:
            pins=sorted(group)
            for pin in pins[1:]:join(pins[0],pin)
        # Logical contraction only. Physical input/output nets must remain separate.
        for a in self.addresses:join((a['reference'],a['input_pin']),(a['reference'],a['output_pin']))
        projected=defaultdict(set)
        for pin in parent:
            if not pin[0].startswith(('U17','C17')):projected[root(pin)].add(pin)
        baseline=ca.groups_from_xml(ET.parse(ll.NATIVE/'CA1.xml').getroot())
        contracted=ca.differences(baseline,{frozenset(g) for g in projected.values()})
        return dict(passed=bool(identity) and not delta and not contracted,component_identity_match=bool(identity),
            unmated_differences=delta,contracted_CA1_differences=contracted,components=len(components),
            dip_count=sum(r.startswith('U') for r in components),physical_pins=sum(map(len,groups)),
            unmated_groups=len(groups),buffer_arcs=16,physical_qualification=False,promoted_into_R2=False)

    def bindings(self,path):
        """Derive the buffer transfer mapping from actual exported physical pins."""
        tree=ET.parse(path).getroot()
        nets={(p.get('ref'),p.get('pin')):n.get('code') for n in tree.findall('./nets/net') for p in n.findall('node')}
        raw={};dest={}
        for row in self.addresses:
            bit=row['bit'];original=self.base.pins
            source=next(p for p in original.values() if p['native_name']==row['raw_net'] and p['driver'])
            raw[nets[source['reference'],source['pin']]]=bit
            targets={nets[tuple(p)] for p in row['moved_pins']};require(len(targets)==1,'Split ME1 address receivers')
            dest[bit]=targets.pop()
        # Buffer package power is on the memory card, unmated from Y1001 rails.
        gnd=nets['U17001','10'];vcc=nets['U17001','20']
        result=[]
        for bit,out_net in dest.items():
            candidates=[]
            for row in self.addresses:
                ref=row['reference'];output=row['output_pin'];inp=row['input_pin']
                if nets[ref,output]!=out_net:continue
                enable_pin='1' if OUTPUTS.index(int(output))<4 else '19'
                enable=nets[ref,enable_pin];require(enable in (gnd,vcc),'Unresolved buffer enable')
                require(nets[ref,inp] in raw,'Unknown raw MAR buffer input')
                candidates.append(dict(bit=bit,source_bit=raw[nets[ref,inp]],reference=ref,input_pin=inp,
                    output_pin=output,enable_pin=enable_pin,enabled=enable==gnd,
                    receiver_pins=self.addresses[bit]['moved_pins']))
            require(len(candidates)==1,'Missing or multiply driven buffered address bit')
            result+=candidates
        return result

    def generate(self,folder,fault=None):
        folder=Path(folder);require(not folder.exists(),'Preserve MD1 attempt');folder.mkdir(parents=True)
        for name,text in self.documents(fault).items():(folder/name).write_text(text)
        write_json(folder/'provenance.json',dict(revision='CP1-MD1',components=self.components,addresses=self.addresses,
            cpu_contacts=self.base.provenance['contacts'],physical_qualification=False))
        code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',folder/'MD1.xml',folder/'MD1.kicad_sch'])
        (folder/'export.log').write_text(log);require(code==0,'MD1 export failed: '+log)
        result=self.compare(folder/'MD1.xml');write_json(folder/'comparison.json',result);return result


class LoadInventory(ll.Inventory):
    def __init__(self,candidate,path):
        super().__init__()
        require(candidate.compare(path)['passed'],'MD1 load inventory needs complete native parity')
        self.path=Path(path);self.components=candidate.components;self.pins={};self.parent={};self.groups={}
        for net in ET.parse(path).getroot().findall('./nets/net'):
            code=net.get('code');self.parent[code]=code;self.groups[code]=net.get('name')
            for node in net.findall('node'):
                ref,pin=node.get('ref'),node.get('pin');key=ref+'.'+pin;c=self.components[ref]
                require(key not in self.pins,'Duplicate MD1 load pin')
                meta=next(p for p in c['pin_signature'] if p['num']==pin)
                self.pins[key]=dict(id=key,reference=ref,pin=pin,part=c['value'],board=c['board'],
                    source_reference=c['source_reference'],card=c['role'],native_net=code,
                    native_name=net.get('name'),symbol_type=meta['type'],pin_name=meta['name'])
        self.contacts=[]
        for row in self.provenance['contacts']:
            self.contact(row['card_reference']+'.'+row['pin'],row['backplane_reference']+'.'+row['pin'],
                'CPU '+row['role']+' '+row['connector'],row['kind'])
        for pin in ca.connector_plan.CONTACTS:self.contact('J13005.'+pin,'J14001.'+pin,'slot5','peripheral')
        self.nets=defaultdict(list)
        for p in self.pins.values():
            p['net']=self.root(p['native_net']);self.nets[p['net']].append(p)
        self.rails={self.pins['Y1001.8']['net']:'5V',self.pins['Y1001.4']['net']:'GND'}
        for r in self.resistors:r['nets']=[self.pins[p]['net'] for p in r['pins']]
        for d in self.directions:
            d['direction_net']=self.pins[d['direction_pin']]['net'];d['enable_net']=self.pins[d['enable_pin']]['net']
            require(self.rails.get(d['direction_net'])=='5V','Changed 245 direction')
        for p in self.pins.values():self.classify(p)

    def audit(self,candidate):
        rows=self.matrix();by_net={r['net']:r for r in rows};paths=[]
        for row in candidate.addresses:
            raw=by_net[self.pins[row['reference']+'.'+row['input_pin']]['net']]
            out=by_net[self.pins[row['reference']+'.'+row['output_pin']]['net']]
            for label,net in [('raw',raw),('buffered',out)]:
                require(len(net['scenarios'])==1,'Unexpected MAR driver multiplicity')
                s=net['scenarios'][0];ic_pins=s['load_pins']+[s['driver']]
                # Design allocations, all subject to actual socket/layout/probe qualification.
                allowance=len(ic_pins)*1+6+5
                paths.append(dict(bit=row['bit'],stage=label,driver=s['driver'],load_pins=s['load_pins'],
                    ic_only_pf=s['ic_only_pf'],socket_allocation_per_pin_pf=1,socket_pins=len(ic_pins),
                    trace_via_pad_allocation_pf=6,probe_allocation_pf=5,parasitic_allocation_pf=allowance,
                    total_planning_pf=s['ic_only_pf']+allowance,fixture_pf=50,
                    planning_margin_pf=50-s['ic_only_pf']-allowance,
                    full_OC1_unknown_pin_maxima=s['unknown_pin_maxima'],total_physical_load_pf=None))
        require(all(p['planning_margin_pf']>0 for p in paths),'MD1 planning margin exhausted')
        return dict(revision='CP1-MD1',pins=self.pins,nets=rows,contacts=self.contacts,resistors=self.resistors,
            directions=self.directions,mar_paths=paths,components=len(self.components),physical_pins=len(self.pins),
            driver_scenarios=sum(len(n['scenarios']) for n in rows),
            physical_qualification=False,planning_scope='1 pF per attached socket pin + 6 pF trace/via/pad + 5 pF probe. Allocation only; no manufacturer or measurement guarantee. Full OC1 pin maxima unresolved as in LL1.')


def run(folder):
    cae.load();folder=Path(folder);require(not folder.exists(),'Preserve MD1 study');folder.mkdir(parents=True)
    c=Candidate();native=c.generate(folder/'native');require(native['passed'],'MD1 native parity failed')
    faults={f:c.generate(folder/f,f) for f in FAULTS}
    require(all(not r['passed'] for r in faults.values()),'Undetected MD1 wiring fault')
    write_json(folder/'summary.json',dict(revision='CP1-MD1',native=native,mutations=faults,physical_qualification=False))
    write_json(folder/'bindings.json',c.bindings(folder/'native/MD1.xml'))
    write_json(folder/'loads.json',LoadInventory(c,folder/'native/MD1.xml').audit(c))
    print(native)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)

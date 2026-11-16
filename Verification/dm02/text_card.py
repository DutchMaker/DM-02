"""Compile TX1 native KiCad physical pins into independent discrete-cell HDL."""
from collections import Counter,defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from .legacy import read_sheet
from .native_migrate import validate
from .electrical import audit as electrical_audit

SOURCE=ROOT/'Circuits/KiCad/Text/candidates'
PARTS=VROOT/'text-parts.json'
STUDY=BUILD/'cp1-text'
SOURCES=['Verification/designs/text_candidate.py','Verification/dm02/text_card.py',
    'Verification/text-parts.json','Verification/bridge-parts.json','Verification/hdl/text_cells.sv',
    'Circuits/KiCad/Text/candidates/TX1.sch','Circuits/KiCad/Text/candidates/boundary.json',
    'Circuits/KiCad/Libraries/DM02Text.lib','Circuits/KiCad/Libraries/DM02Bridge.lib']


def require(ok,message):
    if not ok:raise ValueError(message)


def parts():
    p=json.loads(PARTS.read_text());base=VROOT/p['base_parts']
    require(digest(base)==p['base_sha256'],'Changed base parts')
    p['devices']={**json.loads(base.read_text())['devices'],**p['devices']}
    for d in list(p['devices'].values())+[p['oscillator']]:
        require(digest(STUDY/'sources'/d['file'])==d['sha256'],'Changed TX1 manufacturer source: '+d['file'])
    return p


class Circuit:
    def __init__(self,folder):
        self.parts=parts();root=ET.parse(Path(folder)/'TX1.xml').getroot()
        self.components={p.get('ref'):dict(value=p.findtext('value'),footprint=p.findtext('footprint') or '')
                         for p in root.findall('./components/comp')}
        self.nodes={};self.labels={};self.nets=[]
        for net in root.findall('./nets/net'):
            index=len(self.nets);name=net.get('name').removeprefix('/')
            pins=[(p.get('ref'),p.get('pin')) for p in net.findall('node')]
            self.nets.append(dict(name=name,pins=pins));self.labels[name]=index
            for pin in pins:
                require(pin not in self.nodes,'Duplicate TX1 native pin');self.nodes[pin]=index
        self.operations=[];self.sequential=[];self.inputs=defaultdict(set);self.outputs=defaultdict(set)
        self.compile()

    def n(self,ref,pin):return self.nodes[ref,str(pin)]

    def compile(self):
        def pins(ref,items,table):
            for p in items:table[self.n(ref,p)].add((ref,str(p)))
        def gate(ref,kind,ins,out):
            pins(ref,ins,self.inputs);pins(ref,[out],self.outputs)
            self.operations.append(dict(ref=ref,kind=kind,inputs=[self.n(ref,p) for p in ins],
                output=self.n(ref,out),pin=str(out)))
        def sequential(ref,kind,ins,outs):
            pins(ref,ins,self.inputs);pins(ref,outs,self.outputs)
            self.sequential.append(dict(ref=ref,kind=kind,inputs=[self.n(ref,p) for p in ins],
                outputs=[self.n(ref,p) for p in outs]))
        for ref,p in self.components.items():
            if not ref.startswith('U'):continue
            require(p['value'] in self.parts['devices'],'Unknown TX1 device')
            spec=self.parts['devices'][p['value']];count=spec['pins']
            require(self.n(ref,count)==self.labels['5V'] and self.n(ref,count//2)==self.labels['GND'],'Wrong supply pins')
            kind=p['value'].removeprefix('CD74HCT').removesuffix('E')
            if kind in ('00','08','32'):
                for a,b,y in ((1,2,3),(4,5,6),(9,10,8),(12,13,11)):
                    gate(ref,{'00':'nand','08':'and','32':'or'}[kind],[a,b],y)
            elif kind=='04':
                for a,y in ((1,2),(3,4),(5,6),(9,8),(11,10),(13,12)):gate(ref,'not',[a],y)
            elif kind=='244':
                for i,(a,y) in enumerate(zip((2,4,6,8,17,15,13,11),(18,16,14,12,3,5,7,9))):
                    gate(ref,'buffer',[a,1 if i<4 else 19],y)
            elif kind=='154':
                for i,y in enumerate(list(range(1,12))+list(range(13,18))):gate(ref,'decode'+str(i),[23,22,21,20,18,19],y)
            elif kind=='157':
                for a,b,y in ((2,3,4),(5,6,7),(11,10,9),(14,13,12)):gate(ref,'mux2',[a,b,1,15],y)
            elif kind=='151':
                for out in (5,6):gate(ref,'mux8'+('n' if out==6 else ''),[4,3,2,1,15,14,13,12,11,10,9,7],out)
            elif kind=='74':
                for ins,outs in (((2,3,1,4),(5,6)),((12,11,13,10),(9,8))):sequential(ref,'ff',ins,outs)
            elif kind=='273':sequential(ref,'reg',(3,4,7,8,13,14,17,18,11,1),(2,5,6,9,12,15,16,19))
            elif kind=='161':sequential(ref,'count',(3,4,5,6,2,1,9,7,10),(14,13,12,11,15))
            else:raise ValueError(kind)

    def fault(self,name):
        c=deepcopy(self)
        if name=='mailbox-overwrite':
            for op in c.operations:
                if op['kind']=='mux2' and c.nets[op['inputs'][2]]['name']=='ACCEPT':op['inputs'][2]=c.labels['TEXT_WRITE']
        elif name=='early-credit':
            for op in c.operations:
                if c.nets[op['output']]['name']=='EMPTY':op['kind']='not';op['inputs']=[c.labels['GND']]
        elif name=='reversed-bits':
            for op in c.operations:
                if op['kind'].startswith('mux8'):op['inputs'][:8]=list(reversed(op['inputs'][:8]))
        elif name=='stale-read-address':
            for op in c.operations:
                for i,n in enumerate(op['inputs']):
                    label=c.nets[n]['name']
                    if label.startswith('R_ADDR'):op['inputs'][i]=c.labels['W_ADDR'+label[6:]]
        else:raise ValueError(name)
        return c

    def hdl(self,profile=1):
        lines=['`timescale 1ns/1ps','module text_dut(input osc,reset_n,input [7:0] waddr,wdata,',
            'input strobe,input [7:0] raddr,input rvalid,output [7:0] result,output tx);',f'tri n[0:{len(self.nets)-1}];']
        expr=lambda n:f'n[{n}]'
        def delay(ref,index):
            t=self.parts['devices'][self.components[ref]['value']]['max_delay_ns']
            return 0 if profile==0 else t if profile==1 or index%2==profile-2 else 0
        # Top ports attach to physical DIN contacts from the independent CN1 plan.
        from .connector_plan import generate
        mapping={'RESET_n':'reset_n','W_STROBE':'strobe','R_VALID':'rvalid',
                 **{f'{p}{i}':f'{v}[{i}]' for p,v in (('W_ADDR','waddr'),('W_DATA','wdata'),('R_ADDR','raddr')) for i in range(8)}}
        for pin in generate()['peripheral_cards'][0]['connector']['pins']:
            signal=(pin['net'] or '').removeprefix('SLOT5_')
            if signal in mapping:lines.append(f'assign {expr(self.n("J1",pin["pin"]))}={mapping[signal]};')
            elif signal.startswith('R_DATA'):lines.append(f'assign result[{signal[6:]}]={expr(self.n("J1",pin["pin"]))};')
        lines += [f'assign {expr(self.n("Y1",5))}=osc;',f'assign {expr(self.n("Y1",8))}=1;',
                  f'assign {expr(self.n("Y1",4))}=0;',f'assign tx={expr(self.n("J2",2))};']
        require(self.components['Y1']['value']=='ACH-4.000MHZ-EK','Wrong local oscillator')
        for ref,p in self.components.items():
            if ref.startswith('R'):
                require(p['value']=='1k','Unmodeled resistor')
                lines.append(f'tran({expr(self.n(ref,1))},{expr(self.n(ref,2))}); // Ideal DC connection; no cable RC model')
        for index,op in enumerate(self.operations):
            ins=list(map(expr,op['inputs']));kind=op['kind']
            if kind in ('nand','and','or'):
                value='('+(' | ' if kind=='or' else ' & ').join(ins)+')'
                if kind=='nand':value='~'+value
            elif kind=='not':value='~'+ins[0]
            elif kind=='buffer':value=f'{ins[1]} ? 1\'bz : {ins[0]}'
            elif kind.startswith('decode'):value=f'({ins[4]} | {ins[5]} | ({{{",".join(reversed(ins[:4]))}}} != 4\'d{kind[6:]}))'
            elif kind=='mux2':value=f'{ins[3]} ? 1\'b0 : ({ins[2]} ? {ins[1]} : {ins[0]})'
            elif kind.startswith('mux8'):
                lines.append(f'wire [7:0] mux_{index}={{{",".join(reversed(ins[:8]))}}};')
                value=f'({ins[11]} ? 1\'b0 : mux_{index}[{{{",".join(reversed(ins[8:11]))}}}])'
                if kind.endswith('n'):value='~'+value
            else:raise ValueError(kind)
            lines.append(f'assign #({delay(op["ref"],index)}) {expr(op["output"])}={value}; // {op["ref"]}.{op["pin"]}')
        for index,op in enumerate(self.sequential):
            ins=list(map(expr,op['inputs']));outs=list(map(expr,op['outputs']));kind=op['kind']
            vector=lambda bits:'{'+','.join(reversed(bits))+'}'
            # First synchronizer samples asynchronous REQ by design. Never claim
            # its setup/hold passes; downstream synchronizer is still monitored.
            first_sync=kind=='ff' and self.nets[op['outputs'][0]]['name']=='REQ1'
            check=int(profile==1 and not first_sync)
            if kind=='ff':args=ins+outs
            elif kind=='reg':args=[vector(ins[:8])]+ins[8:]+[vector(outs)]
            else:args=[vector(ins[:4])]+ins[4:]+[vector(outs[:4]),outs[4]]
            lines.append(f'tx_{kind} #({delay(op["ref"],index)},{check}) cell_{index}({",".join(args)}); // {op["ref"]}')
        return '\n'.join(lines+['endmodule',''])

    def audit(self):
        require(all(len(pins)==1 for pins in self.outputs.values()),'Multiple TX1 output drivers')
        counts=Counter(p['value'] for ref,p in self.components.items() if ref.startswith('U'))
        require(all(p['footprint'].startswith('Package_DIP:') for ref,p in self.components.items() if ref.startswith('U')),'Non-DIP logic')
        loads=[]
        for n,pins in self.inputs.items():
            if self.nets[n]['name'] in ('5V','GND'):continue
            cap=sum(self.parts['devices'][self.components[r]['value']]['input_cap_max_pf'] for r,p in pins)
            loads.append(dict(net=self.nets[n]['name'],pins=sorted(pins),input_cap_pf=cap,planning_wire_pf=5,
                within_screen=cap+5<=(15 if n==self.n('Y1',5) else 50)))
        from .connector_plan import generate
        bindings=[]
        for pin in generate()['peripheral_cards'][0]['connector']['pins']:
            net=pin['net'];expected=net.removeprefix('SLOT5_') if net else None
            if expected=='PRESENT_n' or expected in [f'R_DATA{i}' for i in range(2,7)]:expected='GND'
            if expected=='R_DATA7':expected='STATUS_READ'
            actual=self.nets[self.n('J1',pin['pin'])]
            require(actual['name']==expected if expected else len(actual['pins'])==1,'CN1 pin mismatch: '+pin['pin'])
            bindings.append(dict(pin=pin['pin'],cn1_signal=net,tx1_net=expected))
        op_by_net={o['output']:o for o in self.operations}
        def path(n,origins,stack=()):
            if n in origins:return 0,[]
            if n not in op_by_net:return None
            require(n not in stack,'Combinational cycle')
            op=op_by_net[n];priors=[p for i in op['inputs'] if (p:=path(i,origins,stack+(n,))) is not None]
            if not priors:return None
            delay,arcs=max(priors,key=lambda p:p[0]);value=self.components[op['ref']]['value']
            return delay+self.parts['devices'][value]['max_delay_ns'],arcs+[op['ref']+'.'+op['pin']]
        paths={}
        for name,origins,target in [('read_address',[f'R_ADDR{i}' for i in range(8)],'R_DATA0'),
            ('read_valid',['R_VALID'],'R_DATA0'),('write_address',[f'W_ADDR{i}' for i in range(8)],'MAIL0_D'),
            ('write_data',['W_DATA0'],'MAIL0_D')]:
            delay,arcs=path(self.labels[target],{self.labels[n] for n in origins})
            paths[name]=dict(table_sum_ns=delay,arcs=arcs)
        return dict(dip_count=sum(counts.values()),parts=dict(counts),loads=loads,connector_bindings=bindings,
            conditional_paths=paths,
            over_screen=[r for r in loads if not r['within_screen']],physical_qualification=False,
            scope='IC input maxima plus 5 pF planning wire only. Clock slew, cable/connector, min-delay, CDC, power and reset remain unqualified.')


def simulate(c,folder,profile=1,ppm=0):
    folder=Path(folder);require(not folder.exists(),'Preserve prior TX1 run: '+str(folder));folder.mkdir(parents=True)
    source_hashes={n:digest(ROOT/n) for n in SOURCES+['Verification/hdl/text_tb.sv']}
    (folder/'text.sv').write_text(c.hdl(profile))
    args=['iverilog','-g2012','-s','text_tb','-o','text.vvp','-P',f'text_tb.PPM={ppm}',
          'text.sv',VROOT/'hdl/text_cells.sv',VROOT/'hdl/text_tb.sv']
    code,log=command(args,cwd=folder);(folder/'compile.log').write_text(log)
    require(code==0,'TX1 compilation failed: '+log)
    code,log=command(['vvp','text.vvp'],cwd=folder,timeout=600)
    (folder/'simulation.log').write_text(log)
    violations=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
    result=dict(passed=code==0 and 'PASS TX1' in log and not violations,exit_code=code,
        profile=profile,ppm=ppm,timing_violations=violations,physical_qualification=False,source_hashes=source_hashes,
        hashes={n:digest(folder/n) for n in ('text.sv','simulation.log','compile.log')})
    write_json(folder/'result.json',result);print(folder.name,result,log[-600:],flush=True)
    require(all(digest(ROOT/n)==sha for n,sha in source_hashes.items()),'Source changed during TX1 run')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--native',type=Path);parser.add_argument('--profile',type=int,default=1)
    args=parser.parse_args()
    if args.native:native=args.native
    else:
        native=args.output/'native'/'TX1';s=read_sheet(SOURCE/'TX1.sch')
        require(validate(s,native)['status']=='pass','Native pin parity failed')
        structure=electrical_audit(s);write_json(args.output/'structure.json',structure)
        require(not structure['findings'],'Structural findings')
    c=Circuit(native);write_json(args.output/'audit.json',c.audit())
    simulate(c,args.output/f'profile-{args.profile}',args.profile)

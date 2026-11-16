"""Independent native-pin compiler and checks for the CP1-BR1 candidate."""
from collections import Counter, defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from .common import ROOT,VROOT,BUILD,command,digest,write_json
from .legacy import read_sheet
from .native_migrate import validate as native_validate
from .electrical import audit as electrical_audit

SOURCE=ROOT/'Circuits/KiCad/IO-Bridge/candidates'
PARTS=VROOT/'bridge-parts.json'


def require(condition,message):
    if not condition:raise ValueError(message)


class Circuit:
    """Component behavior uses physical pin numbers, not drawing expressions."""
    def __init__(self,native,boundary):
        self.parts=json.loads(PARTS.read_text())
        self.boundary=boundary['ports']
        self.nodes={};self.labels={};self.components={};self.nets=[]
        for board in ('MQ1','BR1'):
            root=ET.parse(Path(native)/board/(board+'.xml')).getroot()
            for part in root.findall('./components/comp'):
                self.components[board,part.get('ref')]=dict(value=part.findtext('value'),footprint=part.findtext('footprint') or '')
            for net in root.findall('./nets/net'):
                index=len(self.nets);name=net.get('name').removeprefix('/')
                pins=[(board,n.get('ref'),n.get('pin')) for n in net.findall('node')]
                self.nets.append(dict(board=board,name=name,pins=pins))
                self.labels[board,name]=index
                for pin in pins:
                    require(pin not in self.nodes,'Duplicate native pin')
                    self.nodes[pin]=index
        self.operations=self.ops()

    def n(self,board,ref,pin):return self.nodes[board,ref,str(pin)]

    def ops(self):
        operations=[]
        def add(board,ref,kind,inputs,output):
            operations.append(dict(board=board,ref=ref,kind=kind,inputs=[self.n(board,ref,p) for p in inputs],
                output=self.n(board,ref,output),pin=str(output),value=self.components[board,ref]['value']))
        for (board,ref),part in self.components.items():
            if not ref.startswith('U'):continue
            value=part['value'];require(value in self.parts['devices'],'Unsupported candidate device: '+value)
            number=value.removeprefix('CD74HCT').removesuffix('E')
            pins=self.parts['devices'][value]['pins']
            require(self.n(board,ref,pins)==self.labels[board,'5V'] and
                    self.n(board,ref,pins//2)==self.labels[board,'GND'],'IC supply pin mismatch')
            if number in ('00','08','32'):
                for a,b,y in ((1,2,3),(4,5,6),(9,10,8),(12,13,11)):
                    add(board,ref,{'00':'nand','08':'and','32':'or'}[number],[a,b],y)
            elif number=='04':
                for a,y in ((1,2),(3,4),(5,6),(9,8),(11,10),(13,12)):add(board,ref,'not',[a],y)
            elif number=='244':
                for i,(a,y) in enumerate(zip((2,4,6,8,17,15,13,11),(18,16,14,12,3,5,7,9))):
                    add(board,ref,'buffer',[a,1 if i<4 else 19],y)
            elif number=='154':
                for i,y in enumerate(list(range(1,12))+list(range(13,18))):
                    add(board,ref,'decode'+str(i),[23,22,21,20,18,19],y)
            elif number=='153':
                add(board,ref,'mux',[6,5,4,3,14,2,1],7)
                add(board,ref,'mux',[10,11,12,13,14,2,15],9)
            else:raise ValueError(number)
        return operations

    def fault(self,name):
        c=deepcopy(self)
        if name=='stale-read-address':
            # Substitute registered write bits for live address at both decoders.
            for op in c.operations:
                if op['kind'].startswith('decode'):
                    for i,n in enumerate(op['inputs']):
                        label=c.nets[n]['name']
                        if label.startswith('LIVE_ADDRESS'):
                            op['inputs'][i]=c.labels['BR1','IO_ADDRESS'+label.removeprefix('LIVE_ADDRESS')]
        elif name=='return-slot-alias':
            op=next(o for o in c.operations if o['kind']=='mux')
            op['inputs'][1]=op['inputs'][0]
        elif name=='reset-release-write':
            op=next(o for o in c.operations if c.nets[o['output']]['name']=='ARMED_STROBE')
            op['inputs'][1]=c.labels['BR1','5V']
        elif name=='missing-page-qualifier':
            old=c.labels['MQ1','PAGE_FF']
            for op in c.operations:
                op['inputs']=[c.labels['MQ1','5V'] if n==old else n for n in op['inputs']]
        else:raise ValueError(name)
        return c

    def hdl(self,profile):
        lines=['`timescale 1ns/1ps','module bridge_dut(',
            'input [15:0] address,input mem_n,write_n,reset_n,memory_reset_n,input [7:0] waddr,wdata,input strobe,',
            'input [31:0] card_data,input [3:0] present_n,output [7:0] result,',
            'output [31:0] slot_waddr,slot_wdata,slot_raddr,output [3:0] slot_strobe,slot_read,slot_reset);',
            f'tri n[0:{len(self.nets)-1}];']
        # Connect internal sheet boundaries through explicit connector pins.
        exports=defaultdict(list)
        for board,ports in self.boundary.items():
            for ref,pins in ports.items():
                for pin,signal in pins.items():exports[signal].append(self.n(board,ref,pin))
        for signal,indices in exports.items():
            for n in sorted(set(indices))[1:]:lines.append(f'tran(n[{indices[0]}],n[{n}]);')
        top={**{f'ADDRESS{i}':f'address[{i}]' for i in range(16)},
            'MEM_n':'mem_n','LOAD_n10':'write_n','RESET_n':'reset_n','ME1_RESET_n':'memory_reset_n',
            'IO_STROBE':'strobe',**{f'IO_ADDRESS{i}':f'waddr[{i}]' for i in range(8)},
            **{f'IO_DATA{i}':f'wdata[{i}]' for i in range(8)}}
        outs={f'IO_INPUT{i}':f'result[{i}]' for i in range(8)}
        for s in range(5,9):
            top[f'SLOT{s}_PRESENT_n']=f'present_n[{s-5}]'
            for b in range(8):
                top[f'SLOT{s}_R_DATA{b}']=f'card_data[{(s-5)*8+b}]'
                for p,var in (('W_ADDR','slot_waddr'),('W_DATA','slot_wdata'),('R_ADDR','slot_raddr')):
                    outs[f'SLOT{s}_{p}{b}']=f'{var}[{(s-5)*8+b}]'
            for p,var in (('W_STROBE','slot_strobe'),('R_VALID','slot_read'),('RESET_n','slot_reset')):
                outs[f'SLOT{s}_{p}']=f'{var}[{s-5}]'
        for signal,expr in top.items():lines.append(f'assign n[{exports[signal][0]}]={expr};')
        for signal,expr in outs.items():lines.append(f'assign {expr}=n[{exports[signal][0]}];')
        for board in ('MQ1','BR1'):
            lines += [f'assign n[{self.labels[board,"5V"]}]=1;',f'assign n[{self.labels[board,"GND"]}]=0;']
        for (board,ref),part in self.components.items():
            if not ref.startswith('R'):continue
            a,b=self.n(board,ref,1),self.n(board,ref,2)
            if b==self.labels[board,'5V'] and part['value']=='10k':lines.append(f'pullup(n[{a}]);')
            elif b==self.labels[board,'GND'] and part['value']=='100k':lines.append(f'pulldown(n[{a}]);')
            else:raise ValueError('Unsupported resistor model')
        for index,op in enumerate(self.operations):
            ins=[f'n[{n}]' for n in op['inputs']];k=op['kind']
            if k in ('and','nand','or'):
                expr='('+(' | ' if k=='or' else ' & ').join(ins)+')'
                if k=='nand':expr='~'+expr
            elif k=='not':expr='~'+ins[0]
            elif k=='buffer':expr=f'{ins[1]} ? 1\'bz : {ins[0]}'
            elif k.startswith('decode'):
                expr=f'({ins[4]} | {ins[5]} | ({{{",".join(reversed(ins[:4]))}}} != 4\'d{k[6:]}))'
            elif k=='mux':
                expr=f'{ins[6]} ? 1\'b0 : ({ins[5]} ? ({ins[4]} ? {ins[3]} : {ins[2]}) : ({ins[4]} ? {ins[1]} : {ins[0]}))'
            else:raise ValueError(k)
            maximum=self.parts['devices'][op['value']]['max_delay_ns']
            delay=0 if profile==0 else maximum if profile==1 else maximum if (index%2)==profile-2 else 0
            lines.append(f'assign #({delay}) n[{op["output"]}]={expr}; // {op["board"]} {op["ref"]}.{op["pin"]}')
        return '\n'.join(lines+['endmodule',''])

    def audit(self):
        # Collapse only explicit module boundary connections for global loading.
        parent=list(range(len(self.nets)))
        def root(n):
            while n!=parent[n]:n=parent[n]
            return n
        by_name={}
        for board,ports in self.boundary.items():
            for ref,pins in ports.items():
                for pin,name in pins.items():
                    n=self.n(board,ref,pin)
                    if name in by_name:parent[root(n)]=root(by_name[name])
                    else:by_name[name]=n
        drivers=defaultdict(set);receivers=defaultdict(set)
        for op in self.operations:
            drivers[root(op['output'])].add((op['board'],op['ref'],op['pin']))
        # Distinct physical input pins, not repeated decode truth-table arcs.
        for (board,ref),part in self.components.items():
            if not ref.startswith('U'):continue
            kind=part['value'].removeprefix('CD74HCT').removesuffix('E')
            pins={'00':[1,2,4,5,9,10,12,13],'08':[1,2,4,5,9,10,12,13],
                '32':[1,2,4,5,9,10,12,13],'04':[1,3,5,9,11,13],
                '244':[1,19,2,4,6,8,17,15,13,11],'154':[18,19,20,21,22,23],
                '153':[1,2,3,4,5,6,10,11,12,13,14,15]}[kind]
            for p in pins:receivers[root(self.n(board,ref,p))].add((board,ref,str(p)))
        require(not [d for d in drivers.values() if len(d)>1],'Multiple IC drivers on a net')
        op_by_net={root(op['output']):op for op in self.operations}
        def arrival(n,stack=()):
            n=root(n)
            require(n not in stack,'Sequential feedback is outside combinational timing screen')
            if n not in op_by_net:return (0,[])
            op=op_by_net[n]
            prior=max((arrival(i,stack+(n,)) for i in op['inputs']),key=lambda r:r[0])
            delay=self.parts['devices'][op['value']]['max_delay_ns']
            return prior[0]+delay,prior[1]+[dict(board=op['board'],ref=op['ref'],pin=op['pin'],
                value=op['value'],delay_ns=delay,net=self.nets[op['output']]['name'])]
        paths={}
        for name in ('IO_INPUT0','SLOT5_R_ADDR0','SLOT5_R_VALID','SLOT5_RESET_n'):
            delay,arcs=arrival(by_name[name]);paths[name]=dict(max_table_sum_ns=delay,arcs=arcs)
        rows=[]
        for n,pins in sorted(receivers.items()):
            names=sorted({net['name'] for i,net in enumerate(self.nets) if root(i)==n})
            if names in (['5V'],['GND']):continue
            cap=sum(self.parts['devices'][self.components[b,r]['value']]['input_cap_max_pf'] for b,r,p in pins)
            rows.append(dict(nets=names,input_pins=sorted(pins),input_cap_max_pf=cap,
                planning_wire_allowance_pf=5,within_50pf_screen=cap+5<=50,
                ic_drivers=sorted(drivers.get(n,set()))))
        counts=Counter(p['value'] for (b,r),p in self.components.items() if r.startswith('U'))
        require(all(p['footprint'].startswith('Package_DIP:') for (b,r),p in self.components.items() if r.startswith('U')),
                'Non-DIP bridge logic')
        return dict(passed=True,dip_count=sum(counts.values()),parts=dict(counts),loads=rows,
            over_50pf=[r for r in rows if not r['within_50pf_screen']],
            conditional_paths=paths,
            timing_limitations='Table-delay sums assume characterized load and 6 ns input edges. Generated HCT outputs do not establish that edge condition. No endpoint response, R2 MAR arrival, ME1/BF1/destination path, routing, minimum hold/release or physical timing margin is included.',
            scope='Connected IC input maxima plus a 5 pF planning allowance only. Slot/device/cable output loads, slew, resistor RC, current and power-off clamps are unqualified.',
            physical_qualification=False)


def simulate(circuit,folder,profile=1):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    (folder/'bridge.sv').write_text(circuit.hdl(profile))
    code,log=command(['iverilog','-g2012','-s','bridge_tb','-o','bridge.vvp','bridge.sv',VROOT/'hdl/io_bridge_tb.sv'],cwd=folder)
    require(code==0,'Bridge HDL compile failed: '+log)
    code,out=command(['vvp','bridge.vvp'],cwd=folder,timeout=180)
    log+=out;(folder/'simulation.log').write_text(log)
    return dict(passed=code==0 and 'PASS bridge' in log,profile=profile,log=log)


def run(folder=None,refresh_native=True):
    folder=BUILD/'cp1-bridge' if folder is None else Path(folder)
    require(not (folder/'manifest.json').exists(),'Preserve published bridge study; choose new output')
    folder.mkdir(parents=True,exist_ok=True)
    parts=json.loads(PARTS.read_text())
    for d in parts['devices'].values():
        p=BUILD/'cp1-bridge/sources'/d['file']
        require(digest(p)==d['sha256'],'Manufacturer source changed: '+str(p))
    boundary=json.loads((SOURCE/'boundary.json').read_text())
    comparisons={};structure={}
    for board in ('MQ1','BR1'):
        sheet=read_sheet(SOURCE/(board+'.sch'))
        if refresh_native:comparisons[board]=native_validate(sheet,folder/'native'/board)
        else:comparisons[board]=json.loads((folder/'native'/board/'comparison.json').read_text())
        require(comparisons[board]['status']=='pass','Native connectivity mismatch')
        structure[board]=electrical_audit(sheet)
        require(not structure[board]['findings'],'Structural electrical findings')
    c=Circuit(folder/'native',boundary);audit=c.audit()
    from .io_bridge_boundary import audit as boundary_audit
    binding=boundary_audit(c)
    write_json(folder/'boundary-audit.json',binding)
    runs={str(p):simulate(c,folder/f'profile-{p}',p) for p in range(4)}
    require(all(r['passed'] for r in runs.values()),'Bridge simulation failed')
    mutations={name:simulate(c.fault(name),folder/'mutations'/name) for name in
               ('stale-read-address','return-slot-alias','reset-release-write','missing-page-qualifier')}
    require(all(not r['passed'] for r in mutations.values()),'Undetected bridge mutation')
    result=dict(passed=True,revision='CP1-BR1',baseline_revision='CP1-R2',native=comparisons,
        structure=structure,package_load_audit=audit,profiles=runs,mutations=mutations,boundary_audit=binding,
        physical_qualification=False,integrated_into_R2=False,
        source_hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(SOURCE.glob('*')) if p.is_file()},
        scope='Native-pin candidate simulation; external card returns are test fixtures. No CPU boot, text serializer, powered-off isolation or full-link timing acceptance.')
    write_json(folder/'summary.json',result)
    print('CP1-BR1:',audit['dip_count'],'DIP;',len(audit['over_50pf']),'load screens exceed 50 pF; four profiles and four detected mutations.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output');parser.add_argument('--reuse-native',action='store_true')
    args=parser.parse_args();run(args.output,not args.reuse_native)

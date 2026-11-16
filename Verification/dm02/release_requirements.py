"""RR1: native DATA/SRAM release obligations, conditional on device fixtures."""
from copy import deepcopy
import json
from pathlib import Path
from .common import ROOT,VROOT,BUILD,digest,write_json
from . import mar_distribution as md

STUDY=BUILD/'cp1-release'
require=md.require
INPUTS={'read_n':'U9020.3','write_n':'U9020.5','reset_n':'U9101.2',
        'ph2':'U9023.13','ph3':'U9020.11'}
OUTPUTS={'ram_oe_n':'U9002.24','ram_we_n':'U9002.29','writer_oe_n':'U9004.1'}
QUAD=[([1,2],3),([4,5],6),([9,10],8),([12,13],11)]
DEVICES={'SN74AHCT04N':('not',8.5,[([a],b) for a,b in [(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]]),
         'SN74AHCT08N':('and',9,QUAD),'SN74AHCT00N':('nand',9,QUAD),'SN74AHCT32N':('or',10,QUAD),
         'SN74AHCT244N':('buf',9.5,[([a],b) for a,b in zip(md.INPUTS,md.OUTPUTS)])}


class Graph:
    def __init__(self,inventory=None):
        self.inventory=inventory or json.loads((md.STUDY/'final/loads.json').read_text())
        self.pins=self.inventory['pins'];self.rows={r['net']:r for r in self.inventory['nets']}
        self.rails={self.net('Y1001.4'):0,self.net('Y1001.8'):1};self.gates={}
        refs={p['reference']:p for p in self.pins.values() if p['board'] in ('ME1','BF1','MA1')}
        for ref,p in sorted(refs.items()):
            if p['part'] not in DEVICES:continue
            kind,delay,units=DEVICES[p['part']]
            for inputs,output in units:
                op=ref+'.'+str(output);ips=[ref+'.'+str(i) for i in inputs]
                if kind=='buf':
                    enable=ref+'.'+('1' if md.OUTPUTS.index(output)<4 else '19')
                    # Tri-state write buffer is an endpoint, never a combinational arc.
                    if self.net(enable) not in self.rails or self.rails[self.net(enable)]!=0:continue
                net=self.net(op);require(net not in self.gates,'Multiple combinational drivers')
                self.gates[net]=dict(output_pin=op,input_pins=ips,kind=kind,conditional_max_ns=delay,
                                     part=p['part'],board=p['board'],source_reference=p['source_reference'])

    def net(self,pin):return self.pins[pin]['net']

    def cone(self,pin,stops,seen=()):
        net=self.net(pin)
        if net in stops or net in self.rails:return {}
        require(net not in seen,'Cyclic release cone')
        require(net in self.gates,'Unresolved release input: '+pin)
        g=self.gates[net];result={net:g}
        for p in g['input_pins']:result.update(self.cone(p,stops,seen+(net,)))
        return result

    def paths(self,target,origin,seen=()):
        net=self.net(target)
        if net==self.net(origin):return [[]]
        if net in self.rails or net not in self.gates:return []
        require(net not in seen,'Cyclic release path');g=self.gates[net];result=[]
        for p in g['input_pins']:
            for path in self.paths(p,origin,seen+(net,)):
                result.append(path+[dict(input_pin=p,output_pin=g['output_pin'],part=g['part'],
                                        conditional_max_ns=g['conditional_max_ns'])])
        return result

    def controls(self):
        inputs=dict(INPUTS)
        for bit in range(8,16):inputs['a'+str(bit)]='U9002.'+str([27,26,23,25,4,28,3,31][bit-8])
        stops={self.net(p) for p in inputs.values()};cone={}
        for p in OUTPUTS.values():cone.update(self.cone(p,stops))
        return inputs,cone

    def evaluate(self,values):
        inputs,cone=self.controls();known=dict(self.rails)
        known.update({self.net(pin):values[name] for name,pin in inputs.items()})
        def value(net):
            if net in known:return known[net]
            g=cone[net];a=[value(self.net(p)) for p in g['input_pins']]
            known[net]={'not':lambda:1-a[0],'buf':lambda:a[0],'and':lambda:int(all(a)),
                        'nand':lambda:int(not all(a)),'or':lambda:int(any(a))}[g['kind']]()
            return known[net]
        return {name:value(self.net(pin)) for name,pin in OUTPUTS.items()}

    def hdl(self,profile='max'):
        require(profile in ('max','zero','read-slow','write-slow'),'Unknown RR1 profile')
        inputs,cone=self.controls();allnets=set(cone)|set(self.rails)|{self.net(p) for p in inputs.values()}
        lines=['`timescale 1ns/1ps','module release_controls(input '+','.join(inputs)+',output '+','.join(OUTPUTS)+');']
        names={n:'n'+n for n in sorted(allnets)}
        lines+=['wire '+','.join(names.values())+';']
        for n,v in self.rails.items():lines.append(f"assign {names[n]}=1'b{v};")
        for name,pin in inputs.items():lines.append(f'assign {names[self.net(pin)]}={name};')
        slow=set()
        target='ram_oe_n' if profile=='read-slow' else 'writer_oe_n'
        if profile.endswith('-slow'):
            for origin in ('read_n','write_n'):
                for path in self.paths(OUTPUTS[target],INPUTS[origin]):slow.update(g['output_pin'] for g in path)
        for n,g in sorted(cone.items()):
            a=[names[self.net(p)] for p in g['input_pins']]
            expr={'buf':lambda:a[0],'not':lambda:'~'+a[0],
                  'and':lambda:' & '.join(a),'nand':lambda:'~('+' & '.join(a)+')',
                  'or':lambda:' | '.join(a)}[g['kind']]()
            delay=g['conditional_max_ns'] if profile=='max' or g['output_pin'] in slow else 0
            lines.append(f'assign #({delay}) {names[n]}={expr}; // {g["output_pin"]}')
        for name,pin in OUTPUTS.items():lines.append(f'assign {name}={names[self.net(pin)]};')
        return '\n'.join(lines+['endmodule',''])

    def audit(self):
        require(self.net('U9004.1')==self.net('U9004.19'),'Split writer enables')
        require(self.net('U9002.24')==self.net('U9009.19'),'SRAM/source enable coupling changed')
        require(self.rails.get(self.net('U9002.22'))==0 and self.rails.get(self.net('U9002.30'))==1,'SRAM selects changed')
        for ref in ('U9009','U10105'):
            require(self.rails.get(self.net(ref+'.1'))==1,'Changed transceiver direction')
        buses=[]
        for kind,pins in [('DATA',[f'U10105.{18-i}' for i in range(8)]),
                          ('RAM',[f'U9002.{i}' for i in (13,14,15,17,18,19,20,21)]),
                          ('SOURCE3',[f'U9009.{18-i}' for i in range(8)])]:
            for bit,pin in enumerate(pins):
                row=deepcopy(self.rows[self.net(pin)])
                if kind=='DATA':require(row['driver_pins']==[pin],'DATA is not sole-driver')
                elif kind=='RAM':require(set(row['driver_pins'])=={pin,'U9004.'+str(md.OUTPUTS[bit])},'Unexpected RAM drivers')
                buses.append(dict(bus=kind,bit=bit,**row))
        paths={}
        for target,pin in OUTPUTS.items():
            paths[target]={}
            for name,origin in self.controls()[0].items():
                paths[target][name]=[dict(gates=p,conditional_max_ns=sum(g['conditional_max_ns'] for g in p)) for p in self.paths(pin,origin)]
        paths['source_oe_n']=deepcopy(paths['ram_oe_n'])
        bf_inputs={'reset_n':'U10110.1'}
        # Trace every non-rail leaf of the final DATA OE cone to a physical input pin.
        def leaves(pin,seen=()):
            n=self.net(pin)
            if n in self.rails:return set()
            if n not in self.gates:return {pin}
            require(n not in seen,'Cyclic BF1 cone')
            return set().union(*(leaves(p,seen+(n,)) for p in self.gates[n]['input_pins']))
        for p in sorted(leaves('U10105.19')):bf_inputs[p]=p
        paths['data_oe_n']={name:[dict(gates=p,conditional_max_ns=sum(g['conditional_max_ns'] for g in p))
                                  for p in self.paths('U10105.19',origin)] for name,origin in bf_inputs.items()}
        for name,pin in [('mar_low_oe_n','U8020.19'),('mar_high_oe_n','U8021.19'),('group3_oe_n','U10104.19')]:
            paths[name]={origin:[dict(gates=p,conditional_max_ns=sum(g['conditional_max_ns'] for g in p))
                                for p in self.paths(pin,origin)] for origin in sorted(leaves(pin))}
        states=[]
        for reset in (0,1):
            for read in (0,1):
                for write in (0,1):
                    for ph2 in (0,1):
                        for ph3 in (0,1):
                            for high in range(256):
                                v=dict(reset_n=reset,read_n=read,write_n=write,ph2=ph2,ph3=ph3)
                                v.update({'a'+str(i+8):(high>>i)&1 for i in range(8)})
                                got=self.evaluate(v)
                                expected=dict(ram_oe_n=int(not(reset and not read and write)),
                                    writer_oe_n=int(not(reset and not write and read)),
                                    ram_we_n=int(not(reset and not write and read and ph2 and not ph3 and 0x40<=high<0xff)))
                                require(got==expected,'Native release control truth mismatch')
                                states.append(got)
        def longest(target,origin):return max(p['conditional_max_ns'] for p in paths[target][origin])
        return dict(revision='CP1-RR1',candidate='CP1-MD1',buses=buses,paths=paths,
            truth_cases=len(states),steady_state_dual_drive_cases=sum(not s['ram_oe_n'] and not s['writer_oe_n'] for s in states),
            source_oe_coupled_to_ram=True,physical_qualification=False,
            fixture_bounds=dict(sram_OE_release_ns=9,sram_WE_release_ns=8,sram_CE_release_ns=10,
                sram_release_fixture_pf=5,sram_read_fixture_pf=30,writer_release_ns=13,
                writer_fixture_pf=50,hct245_release_ns=50,hct245_release_fixture_pf=50,
                hct245_enable_ns=74,hct245_enable_fixture_pf=150),
            conditional_blank_ns=dict(read_to_write=longest('ram_oe_n','read_n')+10,
                write_to_read=longest('writer_oe_n','write_n')+13,
                source3_release=longest('source_oe_n','read_n')+50),
            blank_scope='From old command rising at ME1 pins, with zero earliest new-driver activation; SRAM generic model uses 10 ns, one ns above OE table. Add routing/skew/measurement uncertainty and positive reserve. Bounds require applicable loads/slew; no guaranteed physical blank or release inferred.')


def mutations(inventory):
    results={}
    for name,pin,target in [('data-direction','U10105.1','U10105.10'),
                            ('sram-OE-ground','U9002.24','U9002.16'),
                            ('writer-enable-split','U9004.19','U9004.20')]:
        data=deepcopy(inventory);data['pins'][pin]['net']=data['pins'][target]['net']
        try:Graph(data).audit()
        except ValueError as e:results[name]=dict(detected=True,reason=str(e))
        else:raise ValueError('Undetected RR1 native fault: '+name)
    data=deepcopy(inventory);net=data['pins']['U10105.18']['net']
    next(r for r in data['nets'] if r['net']==net)['driver_pins'].append('synthetic-extra-driver')
    try:Graph(data).audit()
    except ValueError as e:results['extra-DATA-driver']=dict(detected=True,reason=str(e))
    else:raise ValueError('Undetected extra DATA driver')
    return results

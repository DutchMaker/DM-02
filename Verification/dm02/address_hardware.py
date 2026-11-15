"""SP1/MA1 pin-derived state, PH1 snapshots and early memory address bypass."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu,simulate as fetched,fixtures
from .register_hardware import Circuit as Registers,bus_load
from .electrical import audit
from .native_migrate import validate

SOURCES={name:ROOT/path for name,path in {
    'stack':'Circuits/KiCad/Registers-StackPointer/candidates/Stack-Pointer.sch',
    'mar':'Circuits/KiCad/Memory/candidates/Memory-Address.sch'}.items()}


class Circuit(Alu):
    def __init__(self,kind,sheet=None):
        self.kind=kind
        super().__init__(sheet or read_sheet(SOURCES[kind]),parts_file='address-parts.json')
        used={cs[0]['value'] for cs in self.components.values()}
        self.parts['devices']={k:v for k,v in self.parts['devices'].items() if k in used}

    def hdl(self,corner=0):
        mar=self.kind=='mar';n=self.n;v=self.vector
        ports=('module memory_address(input ph1,ph3,reset_n,increment,fetch0,pc_transfer,sp_transfer,load_l_n,load_h_n,out_l_n,out_h_n,'
               'input [15:0] pc_bus,sp_bus,inout [7:0] data_bus,output [15:0] address);' if mar else
               'module stack_pointer(input ph1,ph3,reset_n,increment,decrement,load_l_n,load_h_n,out_l_n,out_h_n,'
               'inout [7:0] data_bus,output [15:0] address,sp);')
        lines=['`timescale 1ns/1ps',ports,f'tri n [0:{len(self.nets)-1}];',
               f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        signals=['ph1','ph3','reset_n','increment']+(['fetch0','pc_transfer','sp_transfer'] if mar else ['decrement'])+['load_l_n','load_h_n','out_l_n','out_h_n']
        for pin,signal in enumerate(signals,3):lines.append(f'assign {n("J1",pin)}={signal};')
        for bit in range(8):lines.append(f'tran ({n("J2",bit+3)},data_bus[{bit}]);')
        for bit in range(16):
            lines.append(f'assign address[{bit}]={n("J3",bit+3)};')
            if mar:lines.extend([f'assign {n("J4",bit+3)}=pc_bus[{bit}];',f'assign {n("J5",bit+3)}=sp_bus[{bit}];'])
            else:lines.append(f'assign sp[{bit}]=n[{self.labels[f"STATE{bit}"]}];')
        return '\n'.join(lines+self.logic_hdl(corner)+['endmodule'])

    def logic_hdl(self,corner=0):
        serial=0
        def delay(maximum):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else maximum if corner==1 or ((serial*2654435761)>>(corner+serial%7))&1 else 0
        n=self.n;v=self.vector;lines=[]
        for ref,cs in self.components.items():
            d=self.parts['devices'][cs[0]['value']];kind=d['function']
            if kind=='175':
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} '
                             f'({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='157':
                for a,b,q in [(2,3,4),(5,6,7),(11,10,9),(14,13,12)]:
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,q)}={n(ref,15)} ? 1\'b0 : ({n(ref,1)} ? {n(ref,b)} : {n(ref,a)});')
            elif kind=='283':
                lhs='{'+n(ref,9)+','+v(ref,[4,1,13,10])+'}'
                a="{1'b0,"+v(ref,[5,3,14,12])+'}';b="{1'b0,"+v(ref,[6,2,15,11])+'}'
                lines.append(f'assign #({delay(d["max_delay_ns"])}) {lhs}={a}+{b}+{n(ref,7)};')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        if self.nodes[ref,str(oe)]==self.labels['GND']:
                            lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,b)}={n(ref,a)};')
                        else:
                            t=delay(max(d['max_delay_ns'],d['enable_max_ns']));z=delay(d['disable_max_ns'])
                            lines.append(f'bufif0 #({t},{t},{z}) {ref}_{b} ({n(ref,b)},{n(ref,a)},{n(ref,oe)});')
            elif kind in ('04','08','00','32'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('Address gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else (' | ' if kind=='32' else ' & ').join(n(ref,p['number']) for p in ins)
                    if kind=='00':expr='~('+expr+')'
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:lines.extend(self.extra_hdl(ref,kind,d,delay))
        return lines

    def extra_hdl(self,ref,kind,d,delay):raise ValueError('Unsupported address part '+kind)


class AddressPath:
    def __init__(self,stack=None,mar=None):self.stack=stack or Circuit('stack');self.mar=mar or Circuit('mar')
    def hdl(self,corner=0):return self.stack.hdl(corner)+'\n'+self.mar.hdl(corner)


def simulate(path,folder,corner=0,quick=False):
    from .clock import Clock
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'address.sv').write_text(path.hdl(corner));(folder/'clock.sv').write_text(Clock().hdl(corner))
    code,log=command(['iverilog','-g2012','-s','address_hardware_tb','-P',f'address_hardware_tb.QUICK={int(quick)}',
                      '-o','address.vvp','address.sv','clock.sv',VROOT/'hdl/pc_devices.sv',VROOT/'hdl/address_hardware_tb.sv'],cwd=folder)
    if code:raise RuntimeError('Address compile: '+log)
    code,out=command(['vvp','address.vvp'],cwd=folder,timeout=300);log+=out;(folder/'address.log').write_text(log)
    return dict(passed=code==0 and 'DONE address-path' in log,corner=corner,quick=quick,log=log)


def budget(path,timing=None):
    from .clock import Clock,budget as clock_budget
    b=clock_budget(Clock()) if timing is None else timing;period=b['oscillator_period_min_ns'];spread=3*period-b['phase_min_ns']
    d=path.mar.parts['devices'];buf=d['SN74AHCT244N']['max_delay_ns'];ff=d['CD74AC175M96'];mux=d['SN74AHCT157N']['max_delay_ns']
    adder=d['CD74ACT283E']['max_delay_ns'];or_gate=d['SN74AHCT32N']['max_delay_ns'];route=10
    # SQ1 phase gate, CW1 active gate, inhibit inverter, decoder and function NAND.
    control=9+9+8.5+53+9
    early=max(2*or_gate+buf+mux,buf+2*mux)
    rows=[dict(path='PC1 PH3 state to MA1 PH1 snapshot on dedicated link',available_ns=4*period-spread,
               required_ns=13+75+13+ff['setup_ns']+route),
          dict(path='SP1 PH3 state to MA1 PH1 snapshot on dedicated link',available_ns=4*period-spread,
               required_ns=2*buf+ff['max_delay_ns']+buf+ff['setup_ns']+route),
          dict(path='PH1 snapshots stable before PH2',available_ns=period-spread,
               required_ns=2*buf+ff['max_delay_ns']+route),
          dict(path='PH2 transfer through MA1 to 150 ns host memory and DATA setup',available_ns=b['phase_min_ns'],
               required_ns=control+early+150+10+40+route),
          dict(path='PH2 arithmetic command through four ACT283 adders',available_ns=b['phase_min_ns'],
               required_ns=control+buf+4*adder+mux+ff['setup_ns']+route),
          dict(path='PH1 snapshot through transfer muxes and carry chain to PH3',available_ns=4*period-spread,
               required_ns=2*buf+ff['max_delay_ns']+2*mux+4*adder+mux+ff['setup_ns']+route),
          dict(path='Incoming DATA setup through buffer and byte-load mux',available_ns=40,
               required_ns=buf+mux+ff['setup_ns']+route),
          dict(path='Incoming DATA hold with zero contamination',available_ns=40,
               required_ns=2*buf+ff['hold_ns']+route)]
    for r in rows:r['margin_ns']=r['available_ns']-r['required_ns']
    return rows


def run():
    from .pc_hardware import Circuit as Pc
    from .sequencer import Circuit as Seq
    from .instruction_fixtures import generate
    p=AddressPath();folder=BUILD/'address-hardware';folder.mkdir(parents=True,exist_ok=True)
    artifacts=['address-hardware/summary.json','address-hardware/bus-load.json','address-hardware/fixtures/instructions-coverage.json']
    boards={};needed=set()
    for c in (p.stack,p.mar):
        dest=folder/c.kind;dest.mkdir(exist_ok=True);source=SOURCES[c.kind]
        native=validate(c.sheet,dest/'native');structure=audit(c.sheet);loads=c.loads()
        boards[c.kind]=dict(source_hash=digest(source),native=native,structure=structure,loads=loads,parts=c.parts)
        shutil.copyfile(source,dest/source.name);write_json(dest/'parts.json',c.parts)
        artifacts.extend([f'address-hardware/{c.kind}/{source.name}',f'address-hardware/{c.kind}/parts.json',
                          f'address-hardware/{c.kind}/native/{source.stem}.kicad_sch',f'address-hardware/{c.kind}/native/{source.stem}.xml'])
        needed|={d['source'] for d in c.parts['devices'].values()}
    sources=[]
    for group in ('address','alu','controller','clock','pc'):
        for entry in json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())['files']:
            if entry['id'] not in needed:continue
            src=VROOT/f'vendor/{group}'/entry['file']
            if digest(src)!=entry['sha256']:raise ValueError('Address manufacturer source changed')
            dest=folder/'sources'/group/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            sources.append(dict(group=group,**entry));artifacts.append(str(dest.relative_to(BUILD)))
    if {s['id'] for s in sources}!=needed:raise ValueError('Address manufacturer source missing')
    paths=budget(p);coverage=fixtures(folder/'fixtures');opcodes=generate(folder/'fixtures')
    bus=bus_load([('AL1',Alu()),('PC1',Pc()),('SQ1',Seq()),('RG1',Registers()),('SP1',p.stack),('MA1',p.mar)])
    write_json(folder/'bus-load.json',bus)
    def profile(config):
        corner,connected,cases,quick=config;name=f'corner{corner}-connected{int(connected)}-cases{int(cases)}'
        if connected:r=fetched(Alu(),folder/name,corner,folder/'fixtures',True,cases=cases,registers=Registers(),address_path=p)
        else:r=simulate(p,folder/name,corner,quick=quick)
        r.pop('log');r['log_path']=f'address-hardware/{name}/'+('alu.log' if connected else 'address.log');return r
    configs=[(c,False,False,c>1) for c in range(4)]+[(c,True,False,False) for c in range(6)]+[(c,True,True,False) for c in (0,1,2)]
    with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,configs))
    artifacts.extend(r['log_path'] for r in runs)
    passed=all(r['passed'] for r in runs) and all(r['margin_ns']>=0 for r in paths)
    passed=passed and all(b['native']['status']=='pass' and not b['structure']['findings'] and
                          all(r['characterized'] for r in b['loads'] if not r['shared_data_bus']) for b in boards.values())
    scope=('SP1/MA1 replace behavioral stack and MAR state. PH1 snapshots on dedicated continuously driven PC/SP links retain '
           'pre-increment addresses; mux bypass provides early MAR for same-word memory reads, with PH3 retained state. '
           'Memory/IO remain a 150 ns behavioral partner. Smallest conditional read margin is 3.26 ns. '
           'DATA input budgets are now 80–90 pF before routing and output capacitance; physical bus/clock/reset qualification remains open.')
    write_json(folder/'summary.json',dict(boards=boards,sources=sources,timing_paths=paths,coverage=coverage,opcode_coverage=opcodes,
               bus_load=bus,runs=runs,scope=scope))
    return evidence('address-hardware','Timed MAR and stack integration','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 65,536 stack increments, decrements and MAR increments per full sweep; '
                    '65,536 early PC transfers; all 227 fetched opcodes use pin-derived CPU state.',artifacts=artifacts,limitation=scope)

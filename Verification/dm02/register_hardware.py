"""RG1 pin-derived B/C/H/L and combined fetched DATA load evidence."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu,simulate as alu_simulate,fixtures
from .electrical import audit
from .native_migrate import validate

SOURCE=ROOT/'Circuits/KiCad/Registers-StackPointer/candidates/General-Registers.sch'


class Circuit(Alu):
    def __init__(self,sheet=None):
        # Same characterized device set and load-accounting rules as AL1.
        super().__init__(sheet or read_sheet(SOURCE))
        used={cs[0]['value'] for cs in self.components.values()}
        self.parts['devices']={k:v for k,v in self.parts['devices'].items() if k in used}
        self.parts['revision']='RG1'
        self.parts['scope']='Buffered DATA input; resettable B/C/H/L; PH3 capture; reset-inhibited outputs.'
        self.parts['conditions']='Retained 4.5 V, CL=50 pF logic timing bounds encompassing 0..50 C. Input slew, actual load and reset distribution remain unqualified.'
        self.parts.pop('device_sources',None)

    def hdl(self,corner=0):
        serial=0
        def delay(maximum):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else maximum if corner==1 or ((serial*2654435761)>>(corner+serial%7))&1 else 0
        n=self.n;v=self.vector
        lines=['`timescale 1ns/1ps',
               'module general_registers(input ph3,reset_n,input [3:0] load_n,out_n,inout [7:0] data_bus,output [31:0] registers);',
               f'tri n [0:{len(self.nets)-1}];',f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;',
               f'assign {n("J1",3)}=ph3;assign {n("J1",4)}=reset_n;']
        for i,r in enumerate('BCHL'):
            lines.append(f'assign {n("J1",5+i)}=load_n[{i}];assign {n("J1",9+i)}=out_n[{i}];')
            for b in range(8):lines.append(f'assign registers[{24-8*i+b}]=n[{self.labels[f"{r}{b}"]}];')
        for b in range(8):lines.append(f'tran ({n("J2",b+3)},data_bus[{b}]);')
        for ref,cs in self.components.items():
            d=self.parts['devices'][cs[0]['value']];kind=d['function']
            if kind=='175':
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} '
                             f'({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='157':
                for a,b,q in [(2,3,4),(5,6,7),(11,10,9),(14,13,12)]:
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,q)}={n(ref,15)} ? 1\'b0 : ({n(ref,1)} ? {n(ref,b)} : {n(ref,a)});')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        if self.nodes[ref,str(oe)]==self.labels['GND']:
                            lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,b)}={n(ref,a)};')
                        else:
                            t=delay(max(d['max_delay_ns'],d['enable_max_ns']));z=delay(d['disable_max_ns'])
                            lines.append(f'bufif0 #({t},{t},{z}) {ref}_{b} ({n(ref,b)},{n(ref,a)},{n(ref,oe)});')
            elif kind in ('04','08','00'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('RG1 gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else ' & '.join(n(ref,p['number']) for p in ins)
                    if kind=='00':expr='~('+expr+')'
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:raise ValueError('RG1 unsupported device '+kind)
        return '\n'.join(lines+['endmodule'])


def bus_load(circuits=None):
    from .pc_hardware import Circuit as Pc
    from .sequencer import Circuit as Seq
    circuits=circuits or [('AL1',Alu()),('PC1',Pc()),('SQ1',Seq()),('RG1',Circuit())]
    rows=[]
    for bit in range(8):
        receivers=[];drivers=[]
        for name,c in circuits:
            net=c.nets[c.nodes['J2',str(bit+3)]]
            pins={(p['ref'],x['number']):(p,x) for p in c.sheet['components'] for x in p['pins']}
            for node in net['nodes']:
                part,pin=pins[tuple(node)]
                if not part['ref'].startswith('U'):continue
                d=c.parts['devices'][part['value']];endpoint=dict(candidate=name,ref=part['ref'],pin=pin['number'],mpn=part['value'])
                if pin['kind']=='I':receivers.append(dict(endpoint,cap_pf=d['input_cap_pf']))
                elif pin['kind']=='T':drivers.append(endpoint)
        cap=sum(r['cap_pf'] for r in receivers)
        rows.append(dict(bit=bit,input_cap_budget_pf=cap,timing_table_load_pf=50,receivers=receivers,drivers=drivers,
                         inputs_alone_exceed_table=cap>50))
    return dict(rows=rows,scope='Sum of retained maximum input-capacitance entries at connected DATA pins. '
                'No per-board external-load allocations are added. This is a worst-case input budget, not a measured minimum. '
                'Inactive output capacitance, routing and unlisted partners are additional; clock/reset fanout remains unaudited.')


def budget(c,timing=None):
    from .clock import Clock,budget as clock_budget
    d=c.parts['devices'];buf=d['SN74AHCT244N'];ff=d['CD74AC175M96'];mux=d['SN74AHCT157N'];route=10
    rows=[dict(path='DATA setup through input buffer and selection',available_ns=40,
               required_ns=buf['max_delay_ns']+mux['max_delay_ns']+ff['setup_ns']+route),
          dict(path='DATA hold with zero contamination and two clock buffers',available_ns=40,
               required_ns=2*buf['max_delay_ns']+ff['hold_ns']+route),
          dict(path='PH2 decoded load to PH3 capture',available_ns=(clock_budget(Clock()) if timing is None else timing)['phase_min_ns'],
               required_ns=9+9+8.5+53+d['SN74AHCT04N']['max_delay_ns']+d['SN74AHCT08DR']['max_delay_ns']+mux['max_delay_ns']+ff['setup_ns']+route)]
    for r in rows:r['margin_ns']=r['available_ns']-r['required_ns']
    return rows


def simulate(circuit,folder,corner=0):
    from .clock import Clock
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'registers.sv').write_text(circuit.hdl(corner));(folder/'clock.sv').write_text(Clock().hdl(corner))
    code,log=command(['iverilog','-g2012','-s','register_hardware_tb','-o','registers.vvp','registers.sv','clock.sv',
                      VROOT/'hdl/pc_devices.sv',VROOT/'hdl/register_hardware_tb.sv'],cwd=folder)
    if code:raise RuntimeError('RG1 compile: '+log)
    code,out=command(['vvp','registers.vvp'],cwd=folder,timeout=60);log+=out;(folder/'registers.log').write_text(log)
    return dict(passed=code==0 and 'DONE RG1' in log,corner=corner,log=log)


def run():
    from .instruction_fixtures import generate
    c=Circuit();folder=BUILD/'register-hardware';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c)
    coverage=fixtures(folder/'fixtures');opcodes=generate(folder/'fixtures');bus=bus_load()
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts);write_json(folder/'bus-load.json',bus)
    artifacts=['register-hardware/summary.json','register-hardware/parts.json','register-hardware/bus-load.json',
               'register-hardware/General-Registers.sch','register-hardware/native/General-Registers.kicad_sch',
               'register-hardware/native/General-Registers.xml','register-hardware/fixtures/instructions-coverage.json']
    sources=[];needed={d['source'] for d in c.parts['devices'].values()}
    for group in ('alu','controller','clock','pc'):
        for entry in json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())['files']:
            if entry['id'] not in needed:continue
            src=VROOT/f'vendor/{group}'/entry['file']
            if digest(src)!=entry['sha256']:raise ValueError('RG1 manufacturer source changed')
            dest=folder/'sources'/group/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            sources.append(dict(group=group,**entry));artifacts.append(str(dest.relative_to(BUILD)))
    if {s['id'] for s in sources}!=needed:raise ValueError('RG1 manufacturer source missing')
    def profile(config):
        corner,connected,cases=config;name=f'corner{corner}-connected{int(connected)}-cases{int(cases)}'
        if connected:r=alu_simulate(Alu(),folder/name,corner,folder/'fixtures',True,cases=cases,registers=c)
        else:r=simulate(c,folder/name,corner)
        r.pop('log');r['log_path']=f'register-hardware/{name}/'+('alu.log' if connected else 'registers.log');return r
    configs=[(c,False,False) for c in (0,1,2)]+[(c,True,False) for c in range(6)]+[(c,True,True) for c in (0,1,2)]
    with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,configs))
    artifacts.extend(r['log_path'] for r in runs)
    passed=native['status']=='pass' and not structure['findings'] and all(r['passed'] for r in runs) and all(r['margin_ns']>=0 for r in paths)
    passed=passed and all(r['characterized'] for r in loads if not r['shared_data_bus'])
    scope=('RG1 replaces behavioral B/C/H/L with KiCad-derived resettable storage, buffered DATA input and reset-inhibited outputs. '
           'C1/SQ1/CW1/PC1/AL1/RG1 fetched execution uses all five stored general registers. '
           'MAR/stack/memory/IO remain behavioral. Combined DATA input budgets are 60–70 pF before routing and capacitance of nine output pins; '
           '50 pF delay-table simulations remain conditional. Physical reset, bus handover and clock loading remain unqualified.')
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=sources,native=native,structure=structure,
               loads=loads,timing_paths=paths,coverage=coverage,opcode_coverage=opcodes,runs=runs,bus_load=bus,scope=scope))
    return evidence('register-hardware','Timed general registers and combined DATA loading','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 2,048 byte-sweep captures and 4,096 register transfers per standalone profile; '
                    '227 fetched opcodes with pin-derived A/B/C/H/L and flags.',artifacts=artifacts,limitation=scope)

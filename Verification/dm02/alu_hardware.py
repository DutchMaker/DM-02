"""AL1 pin-derived timed datapath with opposite-phase result isolation."""
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet,connectivity,function_number
from .electrical import audit
from .native_migrate import validate
from .controller_hardware import Circuit as Word

SOURCE=ROOT/'Circuits/KiCad/ALU/candidates/Timed-ALU.sch'


class Circuit(Word):
    def __init__(self,sheet=None,parts_file='alu-parts.json'):
        self.sheet=sheet or read_sheet(SOURCE);self.parts=json.loads((VROOT/parts_file).read_text())
        self.parts['devices'].update({name:json.loads((VROOT/source).read_text())['devices'][name]
                                     for name,source in self.parts['device_sources'].items()})
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,net in enumerate(self.nets) for node in net['nodes']}
        self.labels={label:i for i,net in enumerate(self.nets) for label in net['labels']}
        self.components={}
        for c in self.sheet['components']:
            if not c['ref'].startswith('U'):continue
            d=self.parts['devices'].get(c['value']);symbol=c['lib_id'].split(':')[1]
            if not d or (function_number(symbol) or symbol)!=d['function']:
                raise ValueError('Unmodelled ALU device or symbol/function conflict: '+c['ref'])
            self.components.setdefault(c['ref'],[]).append(c)
        if any(len({c['value'] for c in cs})!=1 for cs in self.components.values()):raise ValueError('ALU package conflict')

    def loads(self):
        pins={(c['ref'],p['number']):(c,p) for c in self.sheet['components'] for p in c['pins']};rows=[]
        for net in self.nets:
            drivers=[];cap=self.parts['constraints']['local_trace_cap_pf'];limits=[]
            shared=any(s.startswith('DATA') for s in net['labels'])
            for node in net['nodes']:
                c,p=pins[tuple(node)]
                if not c['ref'].startswith('U'):continue
                device=self.parts['devices'][c['value']]
                if p['kind']=='I':cap+=device['input_cap_pf']
                elif p['kind'] in ('O','T'):drivers.append(node);limits.append(device.get('timing_load_pf',50))
            if not drivers:continue
            if any(node[0].startswith('J') for node in net['nodes']):
                cap+=self.parts['constraints']['data_bus_external_load_pf' if shared else 'connector_load_pf']
            rows.append(dict(labels=net['labels'],drivers=drivers,cap_pf=cap,limit_pf=min(limits),shared_data_bus=shared,
                             characterized=cap<=min(limits) and len(drivers)==1,
                             limitation='Inactive driver capacitance is additional and unbounded.' if shared else 'Allocated load, not measured.'))
        return rows

    def rom_address_hdl(self):
        return 'assign rom_address='+self.vector('U1',[10,9,8,7,6,5,4,3,41,40,39,38,37,36,35,34,33,2,1,42,32])+';'

    def extra_hdl(self,ref,kind,d,delay):raise ValueError('Unsupported ALU device '+kind)

    def hdl(self,corner=0):
        serial=0
        def delay(maximum):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else maximum if corner==1 or ((serial*2654435761)>>(corner+serial%7))&1 else 0
        n=self.n;v=self.vector
        lines=['`timescale 1ns/1ps',
               'module timed_alu(input ph1,ph3,reset_n,a_load_n,alu_load_n,f_load_n,a_out_n,alu_out_n,f_out_n,',
               'input set_c,set_z,clear_c,clear_z,input [4:0] operation,inout [7:0] data_bus,',
               'output [7:0] a,output [3:0] flags,output [20:0] rom_address,output [15:0] result);',
               f'tri n [0:{len(self.nets)-1}];',f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        for pin,sig in enumerate(['ph1','ph3','reset_n','a_load_n','alu_load_n','f_load_n','a_out_n','alu_out_n','f_out_n',
                                  'set_c','set_z','clear_c','clear_z'],3):lines.append(f'assign {n("J1",pin)}={sig};')
        for b in range(8):
            lines.append(f'tran ({n("J2",b+3)},data_bus[{b}]);assign a[{b}]=n[{self.labels[f"A{b}"]}];')
        for b in range(5):lines.append(f'assign {n("J3",b+3)}=operation[{b}];')
        for b in range(4):lines.append(f'assign flags[{b}]={n("J3",b+8)};')
        apins=[10,9,8,7,6,5,4,3,41,40,39,38,37,36,35,34,33,2,1,42,32]
        dpins=[14,16,18,20,23,25,27,29,15,17,19,21,24,26,28,30]
        lines.append(self.rom_address_hdl())
        lines.append('assign result={'+','.join(n(f'U{8+b//8}',19-b%8) for b in reversed(range(16)))+'};')
        for ref,cs in self.components.items():
            d=self.parts['devices'][cs[0]['value']];kind=d['function']
            if kind=='M27C322':
                lines.append(f'al1_rom #({delay(d["max_delay_ns"])}) {ref} ({v(ref,apins)},{n(ref,11)},{n(ref,13)},{v(ref,dpins)});')
            elif kind=='175':
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} '
                             f'({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='377':
                lines.append(f'al1_377 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["enable_hold_ns"]},{d["pulse_ns"]}) {ref} '
                             f'({v(ref,[3,4,7,8,13,14,17,18])},{n(ref,11)},{n(ref,1)},{v(ref,[2,5,6,9,12,15,16,19])},reset_n);')
            elif kind=='574':
                lines.append(f'cw574 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["pulse_ns"]}) {ref} '
                             f'({v(ref,range(2,10))},{n(ref,11)},{n(ref,1)},{v(ref,range(19,11,-1))},reset_n);')
            elif kind=='157':
                for a,b,q in [(2,3,4),(5,6,7),(11,10,9),(14,13,12)]:
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,q)}={n(ref,15)} ? 1\'b0 : ({n(ref,1)} ? {n(ref,b)} : {n(ref,a)});')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        t=delay(max(d['max_delay_ns'],d['enable_max_ns']));z=delay(d['disable_max_ns'])
                        # Clock branches have grounded OE; use the data-only bound.
                        if self.nodes[ref,str(oe)]==self.labels['GND']:
                            lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,b)}={n(ref,a)};')
                        else:lines.append(f'bufif0 #({t},{t},{z}) {ref}_{b} ({n(ref,b)},{n(ref,a)},{n(ref,oe)});')
            elif kind in ('04','08','00'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('ALU gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else ' & '.join(n(ref,p['number']) for p in ins)
                    if kind=='00':expr='~('+expr+')'
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:lines.extend(self.extra_hdl(ref,kind,d,delay))
        return '\n'.join(lines+['endmodule',(VROOT/'hdl/alu_devices.sv').read_text()])


def simulate(circuit,folder,corner=0,fixtures=None,connected=False,quick=False,cases=False,registers=None,address_path=None,memory=None,demo=False,power_on_wait_ns=None):
    from .clock import Clock
    from .pc_hardware import Circuit as Pc
    from .sequencer import Circuit as Seq
    from .controller_hardware import roms
    folder.mkdir(parents=True,exist_ok=True)
    if registers is not None and not connected:raise ValueError('RG1 requires fetched integration')
    if address_path is not None and (not connected or registers is None):raise ValueError('Address integration requires RG1')
    if memory is not None and address_path is None:raise ValueError('Memory integration requires SP1/MA1')
    if demo and (memory is None or cases):raise ValueError('Demo integration requires ME1 and continuous execution')
    for name in ('alu.bin','vectors.hex','program.hex','expected.txt','cases.txt','instructions.txt','io-expected.txt'):
        if fixtures and (fixtures/name).exists():shutil.copyfile(fixtures/name,folder/name)
    if hasattr(circuit,'prepare_simulation'):circuit.prepare_simulation(folder)
    (folder/'alu.sv').write_text(circuit.hdl(corner));(folder/'clock.sv').write_text(Clock().hdl(corner))
    if connected:
        roms(folder)
        (folder/'controller.sv').write_text(Word().hdl(corner));(folder/'pc.sv').write_text(Pc().hdl(corner))
        (folder/'sequencer.sv').write_text(Seq().hdl(corner))
        top='sequencer_tb';files=['alu.sv','clock.sv','controller.sv','pc.sv','sequencer.sv',VROOT/'hdl/sequencer_tb.sv']
        parameters=['-P','sequencer_tb.HARD_ALU=1','-P',f'sequencer_tb.CASE_SUITE={int(cases)}'];done='DONE fetched-opcodes' if cases else 'DONE sequencer'
        if demo:parameters.extend(['-P','sequencer_tb.DEMO=1']);done='DONE hardware-demo'
        if registers is not None:
            (folder/'registers.sv').write_text(registers.hdl(corner));files.append('registers.sv')
            parameters.extend(['-P','sequencer_tb.HARD_REGISTERS=1'])
        if address_path is not None:
            (folder/'address.sv').write_text(address_path.hdl(corner));files.append('address.sv')
            parameters.extend(['-P','sequencer_tb.HARD_ADDRESS=1'])
        if memory is not None:
            (folder/'memory.sv').write_text(memory.hdl(corner));files.append('memory.sv')
            parameters.extend(['-P','sequencer_tb.HARD_MEMORY=1'])
    else:
        top='alu_hardware_tb';files=['alu.sv','clock.sv',VROOT/'hdl/pc_devices.sv',VROOT/'hdl/controller_devices.sv',VROOT/'hdl/alu_hardware_tb.sv']
        parameters=['-P',f'alu_hardware_tb.QUICK={int(quick)}'];done='DONE AL1'
    wait=getattr(circuit,'power_on_wait_ns',0) if power_on_wait_ns is None else power_on_wait_ns
    if wait<0:raise ValueError('Power-on wait must be nonnegative')
    parameters.extend(['-P',f'{top}.STARTUP_WAIT_NS={wait}'])
    code,log=command(['iverilog','-g2012','-s',top,*parameters,'-o','alu.vvp',*files],cwd=folder)
    if code:raise RuntimeError('AL1 compile: '+log)
    timeout=3600 if demo else 180
    try:code,out=command(['vvp','alu.vvp'],cwd=folder,timeout=timeout)
    except subprocess.TimeoutExpired as err:
        out=err.stdout or '';out=out.decode('utf-8',errors='replace') if isinstance(out,bytes) else out
        (folder/'alu.log').write_text(log+out+f'\nAL1 simulation timed out after {timeout} seconds.\n');raise
    log+=out;(folder/'alu.log').write_text(log)
    return dict(passed=code==0 and done in log,corner=corner,connected=connected,cases=cases,registers=registers is not None,address_path=address_path is not None,memory=memory is not None,demo=demo,log=log)


def fixtures(folder):
    from .sequencer import fixtures as program_fixtures
    from .alu import expected
    coverage=program_fixtures(folder)
    rows=[]
    for op in range(32):
        for a in range(256):
            b=(a*73+op*19)&255
            rows.append(f'{(op<<32)|(a<<24)|(b<<16)|expected(op,a,b):010x}\n')
    (folder/'vectors.hex').write_text(''.join(rows))
    return coverage


def budget(c,timing=None):
    from .clock import Clock,budget as clock_budget
    b=clock_budget(Clock()) if timing is None else timing;p=b['oscillator_period_min_ns'];spread=3*p-b['phase_min_ns']
    d=c.parts['devices'];route=c.parts['constraints']['routing_uncertainty_ns']
    buf=d['SN74AHCT244N'];ff=d['CD74AC175M96'];latch=d['SN74HCT574N'];operand=d['CD74HCT377M96']
    mux=d['SN74AHCT157N']['max_delay_ns'];rom=d['M27C322-100F1']['max_delay_ns'];gate=d['SN74AHCT08DR']['max_delay_ns']
    inv=d['SN74AHCT04N']['max_delay_ns'];nand=d['SN74AHCT00DR']['max_delay_ns'];clock=buf['max_delay_ns']
    rows=[dict(path='PH3 operands to PH1 result snapshot',available_ns=4*p-spread,
               required_ns=2*clock+max(operand['max_delay_ns'],ff['max_delay_ns'])+rom+latch['setup_ns']+route),
          dict(path='PH1 result stable before PH2 output window',available_ns=p-spread,
               required_ns=clock+latch['max_delay_ns']+route),
          dict(path='PH3 A/flags hold before next PH1 result change',available_ns=4*p-spread,
               required_ns=2*clock+ff['hold_ns']+route),
          dict(path='Stored flags settle for next CW1 ROM capture',available_ns=4*p-spread,
               required_ns=2*clock+ff['max_delay_ns']+150+route),
          dict(path='PH2 CW1 command to synchronous flags',available_ns=b['phase_min_ns'],
               required_ns=9+9+8.5+53+9+inv+nand+gate+2*mux+ff['setup_ns']+route),
          dict(path='DATA setup interface to A/operand/flag capture',available_ns=c.parts['constraints']['data_setup_ns'],
               required_ns=max(mux+ff['setup_ns'],operand['setup_ns'])+route),
          dict(path='DATA hold interface with zero contamination',available_ns=c.parts['constraints']['data_hold_ns'],
               required_ns=2*clock+max(ff['hold_ns'],operand['hold_ns'])+route),
          dict(path='PH2 close to PH1 result change: release before update',available_ns=b['phase_min_ns'],
               required_ns=9+9+8.5+53+inv+nand+buf['disable_max_ns']+route)]
    for r in rows:r['margin_ns']=r['available_ns']-r['required_ns']
    return rows


def run():
    from .instruction_fixtures import generate
    c=Circuit();folder=BUILD/'alu-hardware';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c)
    coverage=fixtures(folder/'fixtures');opcode_coverage=generate(folder/'fixtures')
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    artifacts=['alu-hardware/summary.json','alu-hardware/Timed-ALU.sch','alu-hardware/parts.json',
               'alu-hardware/native/Timed-ALU.kicad_sch','alu-hardware/native/Timed-ALU.xml',
               'alu-hardware/fixtures/vectors.hex','alu-hardware/fixtures/instructions-coverage.json',
               'alu-hardware/fixtures/cases.txt','alu-hardware/fixtures/instructions.txt']
    needed={d['source'] for d in c.parts['devices'].values()};sources=[]
    for group in ('alu','controller','clock','pc'):
        manifest=json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())
        for entry in manifest['files']:
            if entry['id'] not in needed:continue
            source=VROOT/f'vendor/{group}'/entry['file']
            if digest(source)!=entry['sha256']:raise ValueError('AL1 source excerpt changed')
            sources.append(dict(group=group,**entry));dest=folder/'sources'/group/entry['file']
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);artifacts.append(str(dest.relative_to(BUILD)))
    if {s['id'] for s in sources}!=needed:raise ValueError('AL1 manufacturer provenance missing')
    configurations=[(c,False,False) for c in (0,1)]+[(c,True,False) for c in range(6)]+[(c,True,True) for c in (0,1,2)]
    def profile(config):
        corner,connected,cases=config;name=f'corner{corner}-connected{int(connected)}-cases{int(cases)}'
        r=simulate(c,folder/name,corner,folder/'fixtures',connected,cases=cases);r.pop('log')
        r['log_path']=f'alu-hardware/{name}/alu.log';return r
    with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,configurations))
    artifacts.extend(r['log_path'] for r in runs)
    functional=(native['status']=='pass' and not structure['findings'] and all(r['passed'] for r in runs)
                and all(r['margin_ns']>=0 for r in paths) and all(r['characterized'] for r in loads if not r['shared_data_bus'])
                and opcode_coverage['target_opcodes']==227 and opcode_coverage['cases']==454)
    scope=('AL1 A/operand/function storage, PH1 result snapshot, synchronous C/O/Z/N flags and bus outputs are pin-derived. '
           'SQ1/CW1/PC1/C1 fetched tests use AL1 flags directly at the control ROM. MAR, stack, B/C/H/L, flat memory and IO remain behavioral. '
           'DATA allocation is 75–85 pF before inactive-driver capacitance, exceeding 50 pF timing conditions. '
           'The legacy M27C322-100F1 is obsolete; replacement/programmer/sourcing remain open. Device-delay tests are conditional, not electrical qualification.')
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=sources,native=native,structure=structure,
                                        loads=loads,timing_paths=paths,coverage=coverage,opcode_coverage=opcode_coverage,runs=runs,
                                        functional_contract_passed=functional,scope=scope))
    return evidence('alu-hardware','Timed ALU and fetched flag integration','limited' if functional else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 8,192 operand vectors per standalone profile; '
                    '227 fetched opcodes in 454 cases per instruction profile; pin-derived flag storage drives CW1.',
                    functional_contract_passed=functional,artifacts=artifacts,limitation=scope)

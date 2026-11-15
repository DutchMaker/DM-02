"""ME1 pin-derived ROM/RAM and registered IO connector."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu
from .address_hardware import Circuit as Logic

SOURCE=ROOT/'Circuits/KiCad/Memory/candidates/Memory-IO.sch'


class Circuit(Logic):
    def __init__(self,sheet=None):
        Alu.__init__(self,sheet or read_sheet(SOURCE),parts_file='memory-parts.json')

    def loads(self):
        rows=super().loads()
        for row in rows:
            if any(label.startswith('RAM') and label[3:].isdigit() for label in row['labels']):
                row['cap_pf']+=self.parts['devices']['AS6C1008-55PCN']['io_cap_pf']
                row['characterized']=False
                row['limitation']='SRAM DQ maximum 8 pF at 25 C included for write drive; inactive AHCT output capacitance and 5 pF SRAM disable condition remain unqualified.'
        return rows

    def extra_hdl(self,ref,kind,d,delay):
        n=self.n;v=self.vector
        if kind=='27C512':
            return [f'me_rom #({delay(d["max_delay_ns"])}) {ref} ({v(ref,[10,9,8,7,6,5,4,3,25,24,21,23,2,26,27,1])},'
                    f'{n(ref,20)},{n(ref,22)},{v(ref,[11,12,13,15,16,17,18,19])});']
        if kind=='AS6C1008':
            timing=','.join(str(d[k]) for k in ('write_cycle_ns','address_write_setup_ns','write_pulse_ns','write_data_setup_ns'))
            return [f'me_sram #({delay(d["max_delay_ns"])},{delay(d["disable_max_ns"])},{timing}) {ref} '
                    f'({v(ref,[12,11,10,9,8,7,6,5,27,26,23,25,4,28,3,31,2])},{n(ref,22)},{n(ref,30)},{n(ref,24)},{n(ref,29)},'
                    f'{v(ref,[13,14,15,17,18,19,20,21])},reset_n);']
        return super().extra_hdl(ref,kind,d,delay)

    def hdl(self,corner=0):
        n=self.n
        lines=['`timescale 1ns/1ps',
               'module memory_io(input ph0,ph2,ph3,reset_n,read_n,write_n,input [15:0] address,inout [7:0] data_bus,',
               'input [7:0] io_input,output [7:0] io_data,io_address,output io_strobe);',
               f'tri n [0:{len(self.nets)-1}];',f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        for pin,s in enumerate(['ph0','ph2','ph3','reset_n','read_n','write_n'],3):lines.append(f'assign {n("J1",pin)}={s};')
        for b in range(8):
            lines.extend([f'tran ({n("J2",b+3)},data_bus[{b}]);',f'assign {n("J5",b+3)}=io_input[{b}];',
                          f'assign io_data[{b}]={n("J4",b+4)};',f'assign io_address[{b}]={n("J4",b+12)};'])
        lines.append(f'assign io_strobe={n("J4",3)};')
        for b in range(16):lines.append(f'assign {n("J3",b+3)}=address[{b}];')
        lines+=self.logic_hdl(corner)
        # Testbench-only device programming. These tasks never drive CPU state,
        # bus values or control signals; they populate the device model arrays.
        lines.extend(['task fixture_byte(input [15:0] a,input [7:0] value);begin',
                      'if(reset_n) $fatal(1,"ME1 fixture programming requires reset");',
                      'if(a<16384) U1.memory[a]=value;U2.memory[a]=value;end endtask',
                      'task fixture_ready;begin U1.version=U1.version+1;U2.version=U2.version+1;end endtask',
                      'endmodule',(VROOT/'hdl/memory_devices.sv').read_text()])
        return '\n'.join(lines)


def simulate(circuit,folder,corner=0,quick=False):
    from .clock import Clock
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'program.hex').write_text(''.join(f'{((a*37)^(a>>8)^0xa5)&255:02x}\n' for a in range(65536)))
    (folder/'memory.sv').write_text(circuit.hdl(corner));(folder/'clock.sv').write_text(Clock().hdl(corner))
    code,log=command(['iverilog','-g2012','-s','memory_hardware_tb','-P',f'memory_hardware_tb.QUICK={int(quick)}',
                      '-o','memory.vvp','memory.sv','clock.sv',VROOT/'hdl/pc_devices.sv',VROOT/'hdl/memory_hardware_tb.sv'],cwd=folder)
    if code:raise RuntimeError('ME1 compile: '+log)
    code,out=command(['vvp','memory.vvp'],cwd=folder,timeout=300);log+=out;(folder/'memory.log').write_text(log)
    return dict(passed=code==0 and 'DONE memory-io' in log,corner=corner,quick=quick,log=log)


def budget(c,timing=None):
    from .clock import Clock,budget as clock_budget
    b=clock_budget(Clock()) if timing is None else timing;period=b['oscillator_period_min_ns'];spread=3*period-b['phase_min_ns']
    d=c.parts['devices'];buf=d['SN74AHCT244N'];mux=d['SN74AHCT157N']['max_delay_ns'];ff=d['CD74AC175M96']
    inv=d['SN74AHCT04N']['max_delay_ns'];gate=d['SN74AHCT08DR']['max_delay_ns'];nand=d['SN74AHCT00DR']['max_delay_ns']
    ram=d['AS6C1008-55PCN'];route=10;control=9+9+8.5+53+9
    early=max(20+buf['max_delay_ns']+mux,buf['max_delay_ns']+2*mux)
    address=control+early
    rows=[dict(path='PH2 early MA1 address through ROM to DATA setup',available_ns=b['phase_min_ns'],
               required_ns=address+d['AT27C512R-70PU']['max_delay_ns']+2*mux+buf['enable_max_ns']+40+route),
          dict(path='PH2 early MA1 address through SRAM to DATA setup',available_ns=b['phase_min_ns'],
               required_ns=address+ram['max_delay_ns']+2*mux+buf['enable_max_ns']+40+route),
          dict(path='PH2 early MA1 address through IO select to DATA setup',available_ns=b['phase_min_ns'],
               required_ns=address+3*gate+mux+buf['enable_max_ns']+40+route),
          dict(path='SRAM minimum write pulse after decoded PH2 command',available_ns=b['phase_min_ns'],
               required_ns=control+inv+4*gate+nand+ram['write_pulse_ns']+route),
          dict(path='SRAM DATA setup through two buffers, 60 ns connector contract',available_ns=60,
               required_ns=buf['max_delay_ns']+buf['enable_max_ns']+ram['write_data_setup_ns']+route),
          dict(path='SRAM DATA hold until latest PH3 write termination',available_ns=40,
               required_ns=inv+gate+nand+ram['write_data_hold_ns']+route),
          dict(path='IO DATA setup through input buffer and feedback mux',available_ns=60,
               required_ns=buf['max_delay_ns']+mux+ff['setup_ns']+route),
          dict(path='IO DATA hold across two clock buffers',available_ns=40,
               required_ns=2*buf['max_delay_ns']+ff['hold_ns']+route),
          dict(path='PH2 decoded IO request through feedback select to PH3',available_ns=b['phase_min_ns'],
               required_ns=control+inv+3*gate+buf['max_delay_ns']+mux+ff['setup_ns']+route),
          dict(path='PH3 IO capture to PH0 external 40 ns setup',available_ns=period-spread,
               required_ns=2*buf['max_delay_ns']+ff['max_delay_ns']+40+route)]
    for row in rows:row['margin_ns']=row['available_ns']-row['required_ns']
    return rows


def address_load(c,mar):
    rows=[]
    for bit in range(16):
        receivers=[]
        for name,board,connector in [('MA1',mar,'J3'),('ME1',c,'J3')]:
            net=board.nets[board.nodes[connector,str(bit+3)]]
            pins={(p['ref'],pin['number']):(p,pin) for p in board.sheet['components'] for pin in p['pins']}
            for node in net['nodes']:
                part,pin=pins[tuple(node)]
                if part['ref'].startswith('U') and pin['kind']=='I':
                    receivers.append(dict(candidate=name,ref=part['ref'],pin=pin['number'],cap_pf=board.parts['devices'][part['value']]['input_cap_pf']))
        cap=sum(r['cap_pf'] for r in receivers)
        rows.append(dict(bit=bit,receivers=receivers,input_cap_budget_pf=cap,trace_allocation_pf=10,total_budget_pf=cap+10,
                         timing_table_load_pf=50,within_allocation=cap+10<=50))
    return dict(rows=rows,scope='Dedicated MA1 to ME1 link. Receiver maximum capacitance plus 5 pF per board; connector/cable parasitics and SRAM temperature dependence remain unqualified.')


def run():
    from .alu_hardware import simulate as fetched,fixtures
    from .address_hardware import AddressPath
    from .register_hardware import Circuit as Registers,bus_load
    from .pc_hardware import Circuit as Pc
    from .sequencer import Circuit as Seq
    from .instruction_fixtures import generate
    from .electrical import audit
    from .native_migrate import validate
    c=Circuit();p=AddressPath();folder=BUILD/'memory-hardware';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c)
    coverage=fixtures(folder/'fixtures');opcodes=generate(folder/'fixtures')
    bus=bus_load([('AL1',Alu()),('PC1',Pc()),('SQ1',Seq()),('RG1',Registers()),('SP1',p.stack),('MA1',p.mar),('ME1',c)])
    link=address_load(c,p.mar)
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    write_json(folder/'bus-load.json',bus);write_json(folder/'address-load.json',link)
    artifacts=['memory-hardware/'+s for s in ('summary.json','parts.json','bus-load.json','address-load.json','Memory-IO.sch',
               'native/Memory-IO.kicad_sch','native/Memory-IO.xml','fixtures/instructions-coverage.json')]
    sources=[];needed={d['source'] for d in c.parts['devices'].values()}
    for group in ('memory','alu','controller','clock','pc'):
        for entry in json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())['files']:
            if entry['id'] not in needed:continue
            src=VROOT/f'vendor/{group}'/entry['file']
            if digest(src)!=entry['sha256']:raise ValueError('ME1 manufacturer source changed')
            dest=folder/'sources'/group/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            sources.append(dict(group=group,**entry));artifacts.append(str(dest.relative_to(BUILD)))
    if {s['id'] for s in sources}!=needed:raise ValueError('ME1 manufacturer source missing')
    def profile(config):
        corner,connected,cases=config;name=f'corner{corner}-connected{int(connected)}-cases{int(cases)}'
        if connected:r=fetched(Alu(),folder/name,corner,folder/'fixtures',True,cases=cases,registers=Registers(),address_path=p,memory=c)
        else:r=simulate(c,folder/name,corner,quick=corner>1)
        r.pop('log');r['log_path']=f'memory-hardware/{name}/'+('alu.log' if connected else 'memory.log');return r
    configs=[(n,False,False) for n in range(4)]+[(n,True,False) for n in range(6)]+[(n,True,True) for n in (0,1,2)]
    with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,configs))
    artifacts.extend(r['log_path'] for r in runs)
    passed=native['status']=='pass' and not structure['findings'] and all(r['passed'] for r in runs) and all(r['margin_ns']>=0 for r in paths)
    # Private SRAM turnaround stays explicitly unqualified despite its numeric load allocation.
    passed=passed and all(r['cap_pf']<=r['limit_pf'] for r in loads if not r['shared_data_bus']) and all(r['within_allocation'] for r in link['rows'])
    scope=('ME1 completes pin-derived CPU state and ROM/SRAM/IO routing for all 227 fetched opcodes. '
           'Standalone full profiles check every address, all RAM writes, ROM protection and 256 external IO addresses. '
           'Shared DATA input budgets are 90–100 pF plus routing and fourteen output pins. SRAM private-bus inactive output '
           'capacitance, its 5 pF disable timing condition, clock/reset distribution and global handover remain unqualified. '
           'Program loading is fixture initialization; external display hardware remains open. Complete demos are a separate hardware-programs stage.')
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=sources,native=native,structure=structure,
               loads=loads,timing_paths=paths,coverage=coverage,opcode_coverage=opcodes,runs=runs,bus_load=bus,address_load=link,scope=scope))
    return evidence('memory-hardware','Timed memory and registered IO integration','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 65,536 address reads, 48,896 RAM addresses, '
                    '16,384 protected ROM writes and 256 IO ports per full sweep; 227 fetched opcodes.',artifacts=artifacts,limitation=scope)

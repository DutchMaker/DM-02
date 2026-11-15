"""SQ1 pin-derived fetch/t-state/IR/HALT circuit connected to C1, CW1 and PC1."""
import json
import shutil
import struct
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet,connectivity,function_number
from .electrical import audit
from .native_migrate import validate
from .controller_hardware import Circuit as Word,roms

SOURCE=ROOT/'Circuits/KiCad/Controller/candidates/Sequencer.sch'


class Circuit(Word):
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(SOURCE)
        self.parts=json.loads((VROOT/'sequencer-parts.json').read_text())
        self.parts['devices']={name:json.loads((VROOT/source).read_text())['devices'][name]
                               for name,source in self.parts['device_sources'].items()}
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,net in enumerate(self.nets) for node in net['nodes']}
        self.labels={label:i for i,net in enumerate(self.nets) for label in net['labels']}
        self.components={}
        for c in self.sheet['components']:
            if not c['ref'].startswith('U'):continue
            if c['value'] not in self.parts['devices']:raise ValueError('Unmodelled sequencer device')
            if function_number(c['lib_id'].split(':')[1])!=self.parts['devices'][c['value']]['function']:
                raise ValueError('Sequencer symbol/function conflict')
            self.components.setdefault(c['ref'],[]).append(c)
        if any(len({c['value'] for c in cs})!=1 for cs in self.components.values()):raise ValueError('Sequencer package conflict')

    def hdl(self,corner=0):
        serial=0
        def delay(maximum):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else maximum if corner==1 or ((serial*2654435761)>>(corner+serial%7))&1 else 0
        n=self.n;v=self.vector
        lines=['`timescale 1ns/1ps',
               'module sequencer(input [3:0] phase,input reset_n,run,resume,cw_valid,cw_end,cw_halt,cw_inc,cw_pc_n,cw_mem_n,',
               'input [7:0] data,output [7:0] opcode,output [3:0] tstate,',
               'output cw_ph2,request,halted,fetch0,fetch1,executing,pc_inc,pc_address_n,mem_n);',
               f'tri n [0:{len(self.nets)-1}];',
               f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        for pin,sig in enumerate(['phase[0]','phase[1]','phase[2]','phase[3]','reset_n','run','resume','cw_valid',
                                  'cw_end','cw_halt','cw_inc','cw_pc_n','cw_mem_n'],3):lines.append(f'assign {n("J1",pin)}={sig};')
        for b in range(8):lines.append(f'assign {n("J2",b+3)}=data[{b}];assign opcode[{b}]={n("J3",b+7)};')
        for b in range(4):lines.append(f'assign tstate[{b}]={n("J3",b+3)};')
        for pin,sig in enumerate(['cw_ph2','request','halted','fetch0','fetch1','executing','pc_inc','pc_address_n','mem_n'],3):
            lines.append(f'assign {sig}={n("J4",pin)};')
        for ref,cs in self.components.items():
            d=self.parts['devices'][cs[0]['value']];kind=d['function']
            if kind=='161':
                maximum=max(d['clock_q_max_ns'],d['clock_tc_max_ns'],d['clear_max_ns'])
                timing=','.join(str(d[k]) for k in ('data_setup_ns','data_hold_ns','enable_setup_ns','enable_hold_ns',
                                                   'load_setup_ns','load_hold_ns','recovery_ns','reset_pulse_ns','clock_low_ns'))
                lines.append(f'pc161 #({delay(maximum)},{delay(maximum)},{timing}) {ref} '
                             f'({v(ref,[3,4,5,6])},{n(ref,2)},{n(ref,1)},{n(ref,9)},{n(ref,7)},{n(ref,10)},'
                             f'{v(ref,[14,13,12,11])},{n(ref,15)});')
            elif kind=='175':
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} '
                             f'({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='574':
                lines.append(f'cw574 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["pulse_ns"]}) {ref} '
                             f'({v(ref,range(2,10))},{n(ref,11)},{n(ref,1)},{v(ref,range(19,11,-1))},reset_n);')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    if self.nodes[ref,str(oe)]!=self.labels['GND']:raise ValueError('Sequencer buffer OE must be grounded')
                    for a,b in zip(ins,outs):lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,b)}={n(ref,a)};')
            elif kind in ('04','08','00'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('Sequencer gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else ' & '.join(n(ref,p['number']) for p in ins)
                    if kind=='00':expr='~('+expr+')'
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:raise ValueError('Unmodelled sequencer function')
        return '\n'.join(lines+['endmodule'])

    def loads(self):
        rows=super().loads()
        for r in rows:
            if 'PC_INC' in r['labels']:
                r['cap_pf']+=self.parts['constraints']['pc_increment_connector_load_pf']-self.parts['constraints']['connector_load_pf']
                r['within_allocated_test_load']=r['cap_pf']<=50 and len(r['drivers'])==1
        return rows


def simulate(circuit,folder,corner=0,fixtures=None):
    from .clock import Clock
    from .pc_hardware import Circuit as Pc
    folder.mkdir(parents=True,exist_ok=True);roms(folder)
    for name,text in [('sequencer.sv',circuit.hdl(corner)),('controller.sv',Word().hdl(corner)),
                      ('clock.sv',Clock().hdl(corner)),('pc.sv',Pc().hdl(corner))]:
        (folder/name).write_text(text)
    if fixtures:
        for name in ('program.hex','alu.bin','expected.txt'):shutil.copyfile(fixtures/name,folder/name)
    code,log=command(['iverilog','-g2012','-s','sequencer_tb','-o','sequencer.vvp','sequencer.sv','controller.sv',
                      'clock.sv','pc.sv',VROOT/'hdl/sequencer_tb.sv'],cwd=folder)
    if code:raise RuntimeError('Sequencer compile: '+log)
    code,out=command(['vvp','sequencer.vvp'],cwd=folder,timeout=180);log+=out;(folder/'sequencer.log').write_text(log)
    return dict(passed=code==0 and 'DONE sequencer' in log,corner=corner,log=log)


def fixtures(folder):
    """Continuous programs; expected state also checked against instruction semantics."""
    from .control import State,execute,instruction,differences
    from .microcode import reference
    folder.mkdir(parents=True,exist_ok=True)
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    by_name={v['name']:op for op,v in spec['instructions'].items()}
    program=bytearray(65536);labels={};fixups=[];cursor=0
    def label(name):labels[name]=cursor
    def emit(name,value=None):
        nonlocal cursor
        op=by_name[name];size=spec['instructions'][op]['size'];program[cursor]=op;cursor+=1
        if size==3:
            if isinstance(value,str):fixups.append((cursor,value));value=0
            program[cursor:cursor+2]=value.to_bytes(2,'big');cursor+=2
        elif size==2:program[cursor]=value;cursor+=1
    emit('SP address',0x9000)
    # Flags traverse the actual bus partner, stack and decoded F load.
    for flags in range(16):
        emit('MOV A,value',flags|0xf0);emit('PUSH A');emit('POP F')
        for suffix,bit,want in [('C',0,1),('O',1,1),('Z',2,1),('N',3,1),('NC',0,0),('NO',1,0),('NZ',2,0),('P',3,0)]:
            name=f'branch_{flags}_{suffix}'
            emit('J'+suffix+' address',name);emit('NOP');label(name)
    emit('MOV A,value',0x7f);emit('ADD value',1)
    emit('JO address','overflow');emit('HALT');label('overflow')
    emit('FCLR C');emit('FSET Z');emit('FCLR Z');emit('FSET C')
    emit('MOV address,A',0x8100);emit('MOV B,address',0x8100)
    # Fourteen execution t-states exercise the upper sequencer count bits.
    emit('MOV BC,(address)',0x8000)
    emit('CALL address','sub1');emit('JMP address','after_subs')
    label('sub1');emit('CALL address','sub2');emit('RET')
    label('sub2');emit('MOV C,value',0x5a);emit('RET')
    label('after_subs');emit('HALT')
    # Resume and step must continue after HALT rather than execute HALT again.
    emit('MOV A,value',0xa5);emit('HALT');emit('NOP');emit('HALT')
    # Force opcode/operand fetch across FFFF and PC wrap back to 0000.
    emit('JMP address',0xffff)
    program[0xffff]=by_name['NOP']
    for at,name in fixups:program[at:at+2]=labels[name].to_bytes(2,'big')
    program[0x8000:0x8002]=b'\x82\x00';program[0x8200:0x8202]=b'\x12\x34'
    (folder/'program.hex').write_text(''.join(f'{b:02x}\n' for b in program))
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    raw=b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8))
    alu=struct.unpack('<2097152H',raw)
    swapped=bytearray(len(raw));swapped[0::2]=raw[1::2];swapped[1::2]=raw[0::2]
    (folder/'alu.bin').write_bytes(swapped)
    state=State(pc=0,registers={r:0 for r in 'ABCHL'},sp=0);state.memory=dict(enumerate(program))
    rows=[];count=halts=0;opcodes=set();max_t=0;wrap=False
    def row(kind,op,t,word,before,after,bus=None):
        packed=sum(after['registers'][r]<<(8*(4-i)) for i,r in enumerate('ABCHL'))
        values=[kind,op,t,word,before,after['pc'],after['flags'],after['sp'],after['mar'],packed,bus or 0,int(bus is not None)]
        rows.append(' '.join(f'{v:x}' for v in values)+'\n')
    while count<2000:
        pc=state.pc;op=state.get(pc);opcodes.add(op)
        state.mar=pc;after=dict(**state.snapshot(),mar=state.mar)
        row(0,op,0,0,pc,after)
        state.pc=(pc+1)&65535;after=dict(**state.snapshot(),mar=state.mar)
        row(1,op,0,0,pc,after,op)
        want=deepcopy(state);ins=spec['instructions'][op];instruction(ins['name'],ins['size'],want)
        trace=execute(words,alu,op,state,'circuit','output')
        delta=differences(state,want)
        if delta:raise ValueError(f'Sequencer program oracle disagreement: {ins["name"]}: {delta}')
        for i,s in enumerate(trace):
            after=trace[i+1] if i+1<len(trace) else dict(**state.snapshot(),mar=state.mar)
            row(2,op,s['t'],int(s['word'],16),s['pc'],after,s['bus']);max_t=max(max_t,s['t'])
        count+=1
        if state.halted:halts+=1;state.halted=False
        if pc==0xffff:wrap=True;break
    if not wrap or halts!=3:raise ValueError('Sequencer program did not reach expected resume/wrap path')
    (folder/'expected.txt').write_text(''.join(rows))
    result=dict(instructions=count,microcycles=len(rows),execution_cycles=len(rows)-2*count,distinct_opcodes=len(opcodes),
                max_tstate=max_t,halts=halts,flag_values=16,conditional_branches=128,pc_wrap=wrap,
                program_sha256=digest(folder/'program.hex'))
    write_json(folder/'coverage.json',result);return result


def budget(c,timing=None):
    from .clock import Clock,budget as clock_budget
    clock=Clock();b=clock_budget(clock) if timing is None else timing;period=b['oscillator_period_min_ns'];spread=3*period-b['phase_min_ns']
    d=c.parts['devices'];route=c.parts['constraints']['routing_uncertainty_ns']
    buf=d['SN74AHCT244N']['max_delay_ns'];ff=d['CD74AC175M96'];ir=d['SN74HCT574N'];counter=d['CD74HCT161M96']
    gate=d['SN74AHCT08DR']['max_delay_ns'];inv=d['SN74AHCT04N']['max_delay_ns'];nand=d['SN74AHCT00DR']['max_delay_ns']
    cw=Word().parts['devices'];dec=cw['CD74HCT154M96']['max_delay_ns']
    osc=b['oscillator'];maximum_period=1e9/(osc['frequency_hz']*(1-osc['stability_ppm']/1e6))
    sync=clock.parts['devices']['SN74AHC74N'];or_gate=clock.parts['devices']['SN74AHC32N']['max_delay_ns']
    rows=[dict(path='PH3 retained decision to PH0 state/count update',available_ns=period-spread,
               required_ns=buf+ff['max_delay_ns']+max(ff['setup_ns'],counter['load_setup_ns'])+route),
          dict(path='PH0 t-state publication to CW1 ROM setup contract',available_ns=b['phase_min_ns'],
               required_ns=buf+max(counter['clock_q_max_ns'],counter['clear_max_ns'])+150+route),
          dict(path='PH3 opcode capture to next PH1 ROM setup contract',available_ns=4*period-spread,
               required_ns=buf+ir['max_delay_ns']+150+route),
          dict(path='PH0 mode publication to PH1 mode latch',available_ns=b['phase_min_ns'],
               required_ns=buf+ff['max_delay_ns']+ff['setup_ns']+route),
          dict(path='PH1 mode latch settles before PH2 window',available_ns=period-spread,
               required_ns=buf+ff['max_delay_ns']+2*gate+route),
          dict(path='PH2 decoded end to PH3 retained decision',available_ns=b['phase_min_ns'],
               required_ns=gate+gate+inv+dec+nand+inv+nand+inv+gate+ff['setup_ns']+route),
          dict(path='PH2 CW1 increment through SQ1 to PC1 capture',available_ns=b['phase_min_ns'],
               required_ns=gate+gate+inv+dec+nand+inv+nand+gate+counter['enable_setup_ns']+route),
          dict(path='HALT reaches C1 request synchronizer before idle PH1',available_ns=4*period-spread,
               required_ns=buf+ff['max_delay_ns']+gate+2*inv+or_gate+maximum_period+
                2*sync['max_delay_ns']+maximum_period*osc['duty_max']+route),
          dict(path='IR data setup interface through NAND mux',available_ns=c.parts['constraints']['ir_data_setup_ns'],
               required_ns=2*nand+ir['setup_ns']+route),
          dict(path='IR data hold interface with zero contamination',available_ns=c.parts['constraints']['ir_data_hold_ns'],
               required_ns=buf+ir['hold_ns'])]
    for r in rows:r['margin_ns']=r['available_ns']-r['required_ns']
    return rows


def run():
    c=Circuit();folder=BUILD/'sequencer';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c)
    coverage=fixtures(folder/'fixtures')
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    artifacts=['sequencer/summary.json','sequencer/Sequencer.sch','sequencer/parts.json',
               'sequencer/native/Sequencer.kicad_sch','sequencer/native/Sequencer.xml',
               'sequencer/fixtures/coverage.json','sequencer/fixtures/program.hex','sequencer/fixtures/expected.txt']
    needed={d['source'] for d in c.parts['devices'].values()};sources=[]
    for group in ('controller','clock','pc'):
        manifest=json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())
        for entry in manifest['files']:
            if entry['id'] not in needed:continue
            source=VROOT/f'vendor/{group}'/entry['file']
            if digest(source)!=entry['sha256']:raise ValueError('Sequencer source excerpt changed')
            sources.append(dict(group=group,**entry))
            dest=folder/'sources'/group/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
            artifacts.append(str(dest.relative_to(BUILD)))
    if {s['id'] for s in sources}!=needed:raise ValueError('Sequencer manufacturer provenance missing')
    def profile(corner):
        r=simulate(c,folder/f'corner{corner}',corner,folder/'fixtures');r.pop('log')
        r['log_path']=f'sequencer/corner{corner}/sequencer.log';return r
    with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,range(6)))
    artifacts.extend(r['log_path'] for r in runs)
    passed=(native['status']=='pass' and not structure['findings'] and all(r['within_allocated_test_load'] for r in loads)
            and all(r['margin_ns']>=0 for r in paths) and all(r['passed'] for r in runs))
    scope=('SQ1 physical fetch/IR/t-state/HALT candidate drives C1, CW1 and PC1; host never selects ROM addresses. '
           'Behavioral memory, early-transfer MAR, stack, registers and ALU provide bus values and live flags from actual controls. '
           'Peripheral electrical timing, physical flag hookup, shared-bus capacitance, debounce, idle RESUME/reset protocol and backplane qualification remain open. '
           'Adding SQ1 adds an HCT input to the already overloaded DATA bus; this evidence does not qualify that bus.')
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=sources,native=native,structure=structure,
                                        loads=loads,timing_paths=paths,coverage=coverage,runs=runs,scope=scope))
    return evidence('sequencer-hardware','Fetched controller execution','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; {coverage["instructions"]} fetched instructions / '
                    f'{coverage["microcycles"]:,} cycles per profile; 128 conditional branches, nested calls, HALT/resume, held STEP and PC wrap.',
                    artifacts=artifacts,limitation=scope)

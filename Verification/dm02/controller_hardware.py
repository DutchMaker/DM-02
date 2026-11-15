"""Pin-derived control ROMs, word latch, phase blanking and full field decode."""
import json
import shutil
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet,connectivity,function_number
from .electrical import audit
from .native_migrate import validate

SOURCE=ROOT/'Circuits/KiCad/Controller/candidates/Control-Word.sch'


class Circuit:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(SOURCE)
        self.parts=json.loads((VROOT/'controller-parts.json').read_text())
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,net in enumerate(self.nets) for node in net['nodes']}
        self.labels={label:i for i,net in enumerate(self.nets) for label in net['labels']}
        self.components={}
        for c in self.sheet['components']:
            if not c['ref'].startswith('U'):continue
            if c['value'] not in self.parts['devices']:raise ValueError('Unmodelled controller device '+c['value'])
            kind=self.parts['devices'][c['value']]['function'];symbol=c['lib_id'].split(':')[1]
            if (symbol if kind=='27C512' else function_number(symbol))!=kind:raise ValueError('Controller symbol/function conflict')
            self.components.setdefault(c['ref'],[]).append(c)
        for ref,cs in self.components.items():
            if len({c['value'] for c in cs})!=1:raise ValueError('Controller package conflict '+ref)

    def n(self,ref,pin):return f'n[{self.nodes[ref,str(pin)]}]'
    def vector(self,ref,pins):return '{'+','.join(self.n(ref,p) for p in reversed(pins))+'}'

    def loads(self):
        pins={(c['ref'],p['number']):(c,p) for c in self.sheet['components'] for p in c['pins']}
        rows=[];limits=self.parts['constraints']
        for net in self.nets:
            drivers=[];cap=limits['local_trace_cap_pf']
            for node in net['nodes']:
                c,p=pins[tuple(node)]
                if not c['ref'].startswith('U'):continue
                if p['kind']=='I':cap+=self.parts['devices'][c['value']]['input_cap_pf']
                elif p['kind'] in ('O','T'):drivers.append(node)
            if not drivers:continue
            if any(n[0].startswith('J') for n in net['nodes']):
                cap+=limits['pc_increment_connector_load_pf'] if 'FUN5' in net['labels'] else limits['connector_load_pf']
            rows.append(dict(labels=net['labels'],drivers=drivers,cap_pf=cap,within_allocated_test_load=cap<=50 and len(drivers)==1))
        return rows

    def hdl(self,corner=0):
        serial=0
        def delay(value):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else value if corner==1 or ((serial*1103515245+corner*12345)>>(serial%13))&1 else 0
        n=self.n;v=self.vector
        lines=['`timescale 1ns/1ps',
               'module control_word(input ph1,ph2,reset_n,input [15:0] address,output [15:0] word,',
               'output [14:1] out_n,load_n,output [12:1] functions,output [4:0] alu_op,output alu_enable,pc_address_n,valid);',
               f'tri n [0:{len(self.nets)-1}];',
               f'assign n[{self.labels["5V"]}]=1; assign n[{self.labels["GND"]}]=0;']
        for p,s in [(3,'ph1'),(4,'ph2'),(5,'reset_n')]:lines.append(f'assign {n("J1",p)}={s};')
        for b in range(16):lines.append(f'assign {n("J2",b+3)}=address[{b}];')
        for b in range(1,15):
            lines.append(f'assign out_n[{b}]={n("J3",b+2)}; assign load_n[{b}]={n("J4",b+2)};')
        for b in range(1,13):lines.append(f'assign functions[{b}]={n("J5",b+2)};')
        for b in range(5):lines.append(f'assign alu_op[{b}]={n("J6",b+3)};')
        lines.append(f'assign pc_address_n={n("J6",8)}; assign alu_enable={n("J6",9)}; assign valid={n("J1",6)};')
        lines.append('assign word={'+','.join(n(f'U{3+b//8}',19-b%8) for b in reversed(range(16)))+'};')
        for ref,cs in self.components.items():
            d=self.parts['devices'][cs[0]['value']];kind=d['function']
            if kind=='27C512':
                bank='low' if ref=='U1' else 'high'
                lines.append(f'cw_rom #({delay(d["max_delay_ns"])},"{bank}.hex") {ref} '
                             f'({v(ref,[10,9,8,7,6,5,4,3,25,24,21,23,2,26,27,1])},{n(ref,20)},{n(ref,22)},'
                             f'{v(ref,[11,12,13,15,16,17,18,19])});')
            elif kind=='574':
                lines.append(f'cw574 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["pulse_ns"]}) {ref} '
                             f'({v(ref,range(2,10))},{n(ref,11)},{n(ref,1)},{v(ref,range(19,11,-1))},reset_n);')
            elif kind=='175':
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} '
                             f'({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='154':
                outputs=[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17]
                for bit,pin in enumerate(outputs):
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,pin)}=({n(ref,18)} || {n(ref,19)}) ? 1\'b1 : '
                                 f'({v(ref,[23,22,21,20])} != 4\'d{bit});')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        # OEs are grounded in this clock-buffer use.
                        if self.nodes[ref,str(oe)]!=self.labels['GND']:raise ValueError('Controller clock-buffer OE must be grounded')
                        lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,b)}={n(ref,a)};')
            elif kind in ('04','08','00'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('Controller gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else ' & '.join(n(ref,p['number']) for p in ins)
                    if kind=='00':expr='~('+expr+')'
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:raise ValueError('Unmodelled controller function')
        lines+=['endmodule',(VROOT/'hdl/controller_devices.sv').read_text()]
        return '\n'.join(lines)


def roms(folder,pattern=False):
    raw=(BUILD/'microcode/microcode.rom').read_bytes()
    if len(raw)!=131072:raise ValueError('Controller requires a complete microcode ROM')
    words=[a^0xa5c3 for a in range(65536)] if pattern else struct.unpack('<65536H',raw)
    for byte,name in enumerate(('low','high')):
        data=bytes((w>>(8*byte))&255 for w in words)
        (folder/f'{name}.bin').write_bytes(data)
        (folder/f'{name}.hex').write_text(''.join(f'{b:02x}\n' for b in data))
    if not pattern and bytes(v for pair in zip((folder/'low.bin').read_bytes(),(folder/'high.bin').read_bytes()) for v in pair)!=raw:
        raise ValueError('Controller byte-bank split failed')


def replay(folder):
    from .control import State,execute
    from .microcode import reference
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    alu=struct.unpack('<2097152H',b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8)))
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text());rows=[];instructions=0
    for op in spec['instructions']:
        for flags in range(16):
            state=State(pc=0x12ff,flags=flags);trace=execute(words,alu,op,state,phase='circuit');instructions+=1
            for i,t in enumerate(trace):
                after=trace[i+1]['pc'] if i+1<len(trace) else state.pc
                values=[int(t['address'],16),int(t['word'],16),t['pc'],after,t['bus'] or 0,int(t['bus'] is not None),int(i==0)]
                rows.append(' '.join(f'{value:x}' for value in values)+'\n')
    (folder/'replay.txt').write_text(''.join(rows))
    return dict(instructions=instructions,microinstructions=len(rows))


def simulate(circuit,folder,corner=0,pattern=True,counted=True,quick=False,fixtures=None):
    from .clock import Clock
    from .pc_hardware import Circuit as Pc
    folder.mkdir(parents=True,exist_ok=True);roms(folder,pattern)
    if fixtures:shutil.copyfile(fixtures/'replay.txt',folder/'replay.txt')
    else:(folder/'replay.txt').write_text('')
    for name,text in [('controller.sv',circuit.hdl(corner)),('clock.sv',Clock().hdl(corner)),('pc.sv',Pc().hdl(corner))]:
        (folder/name).write_text(text)
    code,log=command(['iverilog','-g2012','-s','controller_tb','-P',f'controller_tb.COUNTED={int(counted)}',
                      '-P',f'controller_tb.PATTERN={int(pattern)}','-P',f'controller_tb.QUICK={int(quick)}',
                      '-o','controller.vvp','controller.sv','clock.sv','pc.sv',VROOT/'hdl/controller_tb.sv'],cwd=folder)
    if code:raise RuntimeError('Controller HDL compile failed: '+log)
    try:
        code,out=command(['vvp','controller.vvp'],cwd=folder,timeout=300)
    except subprocess.TimeoutExpired as err:
        partial=err.stdout or ''
        log+=partial.decode('utf-8',errors='replace') if isinstance(partial,bytes) else partial
        (folder/'controller.log').write_text(log+'\nController simulation timed out after 300 seconds.\n')
        raise
    log+=out;(folder/'controller.log').write_text(log)
    return dict(passed=code==0 and 'DONE control-word' in log,corner=corner,pattern=pattern,counted=counted,log=log)


def budget(c,timing=None):
    from .clock import Clock,budget as clock_budget
    b=clock_budget(Clock()) if timing is None else timing;period=b['oscillator_period_min_ns'];spread=3*period-b['phase_min_ns']
    d=c.parts['devices'];route=c.parts['constraints']['routing_uncertainty_ns']
    ff=d['SN74HCT574N'];buf=d['SN74AHCT244N']['max_delay_ns'];gate=d['SN74AHCT08DR']['max_delay_ns']
    inv=d['SN74AHCT04N']['max_delay_ns'];dec=d['CD74HCT154M96']['max_delay_ns'];merge=d['SN74AHCT00DR']['max_delay_ns']
    rows=[dict(path='PH1 word capture to PH2 enable: address/format settled',available_ns=period-spread,
               required_ns=buf+ff['max_delay_ns']+max(gate,inv)+route),
          dict(path='PH2 control enable to PH3 PC capture',available_ns=b['phase_min_ns'],
               required_ns=gate+inv+dec+merge+inv+9+20+route),
          dict(path='PH2 disable to PH1 word change: break before make',available_ns=b['phase_min_ns'],
               required_ns=gate+inv+dec+merge+inv+10+13+route),
          dict(path='PH3 PC capture to PH2 disable: control hold',available_ns=period-spread,
               required_ns=13+5+route),
          dict(path='ROM address setup contract',available_ns=c.parts['constraints']['rom_address_setup_ns'],
               required_ns=d['AT27C512R-70PU']['max_delay_ns']+ff['setup_ns']+route),
          dict(path='ROM address hold with zero contamination delay',available_ns=c.parts['constraints']['rom_address_hold_ns'],
               required_ns=buf+ff['hold_ns'])]
    for r in rows:r['margin_ns']=r['available_ns']-r['required_ns']
    return rows


def run():
    c=Circuit();folder=BUILD/'controller';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c)
    fixtures=folder/'fixtures';fixtures.mkdir(exist_ok=True);coverage=replay(fixtures);roms(fixtures)
    sources=[];artifacts=['controller/summary.json','controller/Control-Word.sch','controller/parts.json',
                         'controller/native/Control-Word.kicad_sch','controller/native/Control-Word.xml',
                         'controller/fixtures/low.bin','controller/fixtures/high.bin','controller/fixtures/replay.txt']
    needed={p['source'] for p in c.parts['devices'].values()}
    for group in ('controller','clock','pc'):
        manifest=json.loads((VROOT/f'vendor/{group}/manifest.json').read_text());selected=[]
        dest=folder/'sources'/group;dest.mkdir(parents=True,exist_ok=True)
        for entry in manifest['files']:
            if entry['id'] not in needed:continue
            source=VROOT/f'vendor/{group}'/entry['file']
            if digest(source)!=entry['sha256']:raise ValueError('Controller source excerpt changed')
            shutil.copyfile(source,dest/entry['file']);selected.append(entry);sources.append(entry)
            artifacts.append(f'controller/sources/{group}/{entry["file"]}')
        write_json(dest/'manifest.json',dict(retrieved=manifest['retrieved'],files=selected))
        artifacts.append(f'controller/sources/{group}/manifest.json')
    if {s['id'] for s in sources}!=needed:raise ValueError('Controller manufacturer provenance missing')
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    def profile(config):
        corner,pattern,counted=config;name=f'corner{corner}-pattern{int(pattern)}-counted{int(counted)}'
        r=simulate(c,folder/name,corner,pattern,counted,fixtures=fixtures);r.pop('log');r['log_path']=f'controller/{name}/controller.log';return r
    with ThreadPoolExecutor(max_workers=3) as pool:
        runs=list(pool.map(profile,[(0,True,False),(1,True,True),(0,False,True),(1,False,True),(2,False,True)]))
    artifacts.extend(r['log_path'] for r in runs)
    passed=(native['status']=='pass' and not structure['findings'] and all(r['within_allocated_test_load'] for r in loads)
            and all(r['passed'] for r in runs) and all(r['margin_ns']>=0 for r in paths))
    scope=('Pin-derived ROM/latch/decode slice; C1 clocks PC1 through decoded controls. Host supplies opcode/t-state/live flags '
           'and non-PC bus values. Fetch, sequencer, HALT arbitration and complete module timing remain external. '
           'Bounds depend on allocated capacitance, input slew and reset protocol; PC1 shared-bus loading remains unqualified.')
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=sources,structure=structure,native=native,
                                        loads=loads,timing_paths=paths,runs=runs,coverage=coverage,scope=scope))
    return evidence('controller-hardware','Latched control-word circuit','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 65,536 synthetic words per decode sweep; '
                    f'{coverage["instructions"]:,} opcode/flag sequences and {coverage["microinstructions"]:,} microinstructions per connected-PC replay.',
                    artifacts=artifacts,limitation=scope)

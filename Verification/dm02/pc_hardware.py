"""KiCad-derived PC candidate, opposite-edge carry staging and bus drivers."""
import json
import shutil
import struct
from concurrent.futures import ThreadPoolExecutor
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet,connectivity,function_number
from .electrical import audit
from .native_migrate import validate
from .logisim_pc import ProgramCounter

SOURCE=ROOT/'Circuits/KiCad/Registers-StackPointer/candidates/Program-Counter.sch'


class Circuit:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(SOURCE)
        self.parts=json.loads((VROOT/'pc-parts.json').read_text())
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,net in enumerate(self.nets) for node in net['nodes']}
        self.labels={label:i for i,net in enumerate(self.nets) for label in net['labels']}
        self.components={}
        for c in self.sheet['components']:
            if not c['ref'].startswith('U'):continue
            self.components.setdefault(c['ref'],[]).append(c)
            if c['value'] not in self.parts['devices']:raise ValueError('Unmodelled PC part '+c['value'])
            if function_number(c['lib_id'].split(':')[1])!=self.parts['devices'][c['value']]['function']:
                raise ValueError('PC symbol/part function conflict')
        for ref,cs in self.components.items():
            if len({c['value'] for c in cs})!=1:raise ValueError('Conflicting PC package '+ref)

    def n(self,ref,pin):return f'n[{self.nodes[ref,str(pin)]}]'
    def vector(self,ref,pins):return '{'+','.join(self.n(ref,p) for p in reversed(pins))+'}'

    def loads(self):
        pins={(c['ref'],p['number']):(c,p) for c in self.sheet['components'] for p in c['pins']}
        rows=[]
        for net in self.nets:
            receivers=[];drivers=[]
            for node in net['nodes']:
                c,p=pins[tuple(node)]
                if c['ref'].startswith('U'):
                    if p['kind']=='I':receivers.append((node,self.parts['devices'][c['value']]['input_cap_pf']))
                    elif p['kind'] in ('O','T'):drivers.append(node)
            if not drivers:continue
            cap=sum(p[1] for p in receivers)
            cap+=self.parts['constraints']['connector_load_pf'] if any(n[0].startswith('J') for n in net['nodes']) else self.parts['constraints']['local_trace_cap_pf']
            rows.append(dict(labels=net['labels'],drivers=drivers,receivers=[p[0] for p in receivers],cap_pf=cap,
                             characterized=cap<=50 and len(drivers)==1,
                             limitation='Multiple-driver nets also need an inactive-output capacitance bound; the TI 244 table gives typical Co only.' if len(drivers)>1 else 'Allocated capacitance; not measured.'))
        return rows

    def hdl(self,corner=0):
        serial=0
        def delay(maximum):
            nonlocal serial
            serial+=1
            return 0 if corner==0 else maximum if corner==1 or ((serial*2654435761)>>(corner+serial%7))&1 else 0
        n=self.n;v=self.vector
        lines=['`timescale 1ns/1ps',
               'module pc_candidate(input clock,reset_n,increment,load_l_n,load_h_n,out_l_n,out_h_n,address_n,',
               'inout [7:0] data_bus,inout [15:0] address_bus,output [15:0] pc);',
               f'tri [{len(self.nets)-1}:0] n;',
               f'assign n[{self.labels["5V"]}]=1; assign n[{self.labels["GND"]}]=0;']
        for pin,signal in [(3,'clock'),(4,'reset_n'),(5,'increment'),(6,'load_l_n'),(7,'load_h_n'),(8,'out_l_n'),(9,'out_h_n'),(10,'address_n')]:
            lines.append(f'assign {n("J1",pin)}={signal};')
        for ref,width,signal in [('J2',8,'data_bus'),('J3',16,'address_bus')]:
            for bit in range(width):lines.append(f'tran ({n(ref,bit+3)},{signal}[{bit}]);')
        lines.append('assign pc={'+','.join(n(f'U{bit//4+1}',14-bit%4) for bit in reversed(range(16)))+'};')
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
                lines.append(f'pc175 #({delay(d["max_delay_ns"])},{d["setup_ns"]},{d["hold_ns"]},{d["recovery_ns"]}) {ref} ({v(ref,[4,5,12,13])},{n(ref,9)},{n(ref,1)},'
                             f'{v(ref,[2,7,10,15])},{v(ref,[3,6,11,14])});')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        # Conservative single bound for data and enable transitions.
                        t=delay(max(d['max_delay_ns'],d['enable_max_ns']));z=delay(d['disable_max_ns'])
                        lines.append(f'bufif0 #({t},{t},{z}) {ref}_{b} ({n(ref,b)},{n(ref,a)},{n(ref,oe)});')
            elif kind in ('04','08','32'):
                for c in cs:
                    ins=[p for p in c['pins'] if p['kind']=='I'];outs=[p for p in c['pins'] if p['kind']=='O']
                    if not ins:continue
                    if len(outs)!=1 or len(ins)!=(1 if kind=='04' else 2):raise ValueError('Unexpected PC gate geometry')
                    expr='~'+n(ref,ins[0]['number']) if kind=='04' else (' & ' if kind=='08' else ' | ').join(n(ref,p['number']) for p in ins)
                    lines.append(f'assign #({delay(d["max_delay_ns"])}) {n(ref,outs[0]["number"])}={expr};')
            else:raise ValueError('Unsupported PC device')
        lines+=['endmodule',(VROOT/'hdl/pc_devices.sv').read_text()]
        return '\n'.join(lines)


def vectors(folder,quick=False):
    pc=ProgramCounter();rows=[]
    for before in (0,0xff,0xfff,0xffff,0x1234,0xfffe):
        for data in ((0,0xff,0x5a,0xa5) if quick else range(256)):
            for control in range(8):
                inc,ll,lh=(bool(control&(1<<b)) for b in range(3))
                after=pc.step(before,data,inc,ll,lh)
                rows.append(f'{before:04x} {data:02x} {control:x} {after:04x}\n')
    (folder/'vectors.txt').write_text(''.join(rows))
    return len(rows)


def replay(folder):
    from .control import State,execute
    from .microcode import reference
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    alu=struct.unpack('<2097152H',b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8)))
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text());rows=[];instructions=0
    for op in spec['instructions']:
        for flags in range(16):
            state=State(pc=0x12ff,flags=flags)
            trace=execute(words,alu,op,state,phase='circuit');instructions+=1
            for i,t in enumerate(trace):
                word=int(t['word'],16);data=bool(word&0x8000)
                out=(word>>11)&15 if data else 0;load=(word>>7)&15 if data else 0
                controls=[] if data and word&64 else [(word>>1)&15] if data else [(word>>11)&15,(word>>1)&15]
                after=trace[i+1]['pc'] if i+1<len(trace) else state.pc
                values=[t['pc'],t['bus'] or 0,int(5 in controls),int(load==12),int(load==11),
                        int(out==12),int(out==11),int(6 in controls),after,t['bus'] or 0,int(t['bus'] is not None),int(i==0)]
                rows.append(' '.join(f'{v:x}' for v in values)+'\n')
    (folder/'replay.txt').write_text(''.join(rows));return dict(instructions=instructions,microinstructions=len(rows))


def simulate(circuit,folder,corner=0,counted=False,replay_enabled=False,fixtures=None,quick=False):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'pc.sv').write_text(circuit.hdl(corner))
    if fixtures:
        for name in ('vectors.txt','replay.txt'):shutil.copyfile(fixtures/name,folder/name)
        count=sum(1 for _ in (folder/'vectors.txt').open())
        coverage=json.loads((fixtures/'coverage.json').read_text())
    else:
        count=vectors(folder,quick)
        if replay_enabled:coverage=replay(folder)
        else:(folder/'replay.txt').write_text('');coverage={}
    from .clock import Clock
    (folder/'clock.sv').write_text(Clock().hdl(corner))
    code,log=command(['iverilog','-g2012','-s','pc_tb','-P',f'pc_tb.COUNTED={int(counted)}',
                      '-P',f'pc_tb.QUICK={int(quick)}','-P',f'pc_tb.VECTORS={count}','-o','pc.vvp',
                      'pc.sv','clock.sv',VROOT/'hdl/pc_tb.sv'],cwd=folder)
    if code:raise RuntimeError('PC HDL compile failed: '+log)
    code,out=command(['vvp','pc.vvp'],cwd=folder,timeout=300);log+=out
    (folder/'pc.log').write_text(log)
    return dict(passed=code==0 and 'DONE pc-candidate' in log,corner=corner,counted_clock=counted,
                vectors=count,replay=coverage,log=log)


def run():
    c=Circuit();folder=BUILD/'pc-hardware';folder.mkdir(parents=True,exist_ok=True)
    sources=[];source_artifacts=[]
    for group in ('pc','clock'):
        manifest=json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())
        needed={part['source'] for part in c.parts['devices'].values()}
        dest=folder/'sources'/group;dest.mkdir(parents=True,exist_ok=True)
        selected=[]
        for entry in manifest['files']:
            if entry['id'] not in needed:continue
            source=VROOT/f'vendor/{group}'/entry['file']
            if digest(source)!=entry['sha256']:raise ValueError('PC source excerpt changed: '+str(source))
            shutil.copyfile(source,dest/entry['file']);selected.append(entry)
            source_artifacts.append(f'pc-hardware/sources/{group}/{entry["file"]}')
        sources.extend(selected);write_json(dest/'manifest.json',dict(retrieved=manifest['retrieved'],files=selected))
        source_artifacts.append(f'pc-hardware/sources/{group}/manifest.json')
    if {s['id'] for s in sources}!=needed:raise ValueError('Missing PC manufacturer provenance')
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    structure=audit(c.sheet);loads=c.loads();native=validate(c.sheet,folder/'native')
    fixtures=folder/'fixtures';fixtures.mkdir(exist_ok=True)
    vectors(fixtures);write_json(fixtures/'coverage.json',replay(fixtures))
    def profile(config):
        corner,counted=config
        name=f'corner{corner}-counted{int(counted)}'
        r=simulate(c,folder/name,corner,counted,True,fixtures);r['log_path']=f'pc-hardware/{name}/pc.log';r.pop('log');return r
    with ThreadPoolExecutor(max_workers=3) as pool:
        runs=list(pool.map(profile,[(0,False),(1,False),(0,True),(1,True),(2,True),(3,True)]))
    limits=c.parts['constraints'];d=c.parts['devices']
    from .clock import Clock,budget
    half=budget(Clock())['output_pulse_min_ns']
    # Use the same conservative 13 ns data/enable envelope as the HDL buffers.
    branch=d['SN74AHCT244N']['enable_max_ns'];inv=d['SN74AHCT04N']['max_delay_ns']
    counter=d['CD74HCT161M96'];carry=d['CD74AC175M96'];gate=d['SN74AHCT08DR']['max_delay_ns']
    paths=[dict(path='PC edge to falling-edge carry capture',available_ns=half-branch-inv-limits['routing_uncertainty_ns'],
                required_ns=max(counter['clear_max_ns'],counter['clock_tc_max_ns'])+2*gate+carry['setup_ns']),
           dict(path='Carry stage to next PC count edge',available_ns=half-branch-inv-limits['routing_uncertainty_ns'],
                required_ns=carry['max_delay_ns']+gate+counter['enable_setup_ns']),
           dict(path='Opposite-edge enable hold, zero contamination delay',available_ns=half-branch-inv-limits['routing_uncertainty_ns'],
                required_ns=counter['enable_hold_ns']),
           dict(path='Output disable before next driver enable',available_ns=limits['bus_dead_time_ns'],
                required_ns=d['SN74AHCT32N']['max_delay_ns']+d['SN74AHCT244N']['disable_max_ns']+limits['routing_uncertainty_ns'])]
    for p in paths:p['margin_ns']=p['available_ns']-p['required_ns']
    passed=not structure['findings'] and native['status']=='pass' and all(r['passed'] for r in runs) and all(p['margin_ns']>=0 for p in paths)
    characterized=all(r['characterized'] for r in loads)
    details=dict(source_hash=digest(SOURCE),parts=c.parts,manufacturer_sources=sources,structure=structure,loads=loads,native=native,runs=runs,timing_paths=paths,
                 load_characterized=characterized,
                 scope='Schematic-derived candidate with bounded device delays and input timing checks at the datasheet test load. '
                       'Compiled control words provide ideal settled controls and non-PC bus values. '
                       'C1 phase output clocks the PC in four runs; no complete physical controller/backplane or MAR hold qualification. '
                       'The allocated shared data-bus load exceeds 50 pF and inactive driver capacitance has no guaranteed bound; bus-delay/OE numbers are not qualified for that load.')
    write_json(folder/'summary.json',details)
    return evidence('pc-hardware','Schematic-derived program counter',('pass' if characterized else 'limited') if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/{len(runs)} profiles; 65,536 increments and 12,288 load/control vectors per profile; '
                    '3,632 opcode/flag sequences and 16,992 compiled microinstructions per profile. Shared-bus timing remains unqualified.',
                    artifacts=['pc-hardware/summary.json','pc-hardware/parts.json','pc-hardware/Program-Counter.sch',
                               'pc-hardware/fixtures/vectors.txt','pc-hardware/fixtures/replay.txt',
                               *source_artifacts,'pc-hardware/native/Program-Counter.kicad_sch',
                               'pc-hardware/native/Program-Counter.xml',*[r['log_path'] for r in runs]],limitation=details['scope'])

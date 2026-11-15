"""Pin-derived counted-clock candidate with explicit interval timing bounds."""
import json
import re
from .common import ROOT, VROOT, BUILD, command, digest, evidence, write_json
from .legacy import read_sheet, connectivity, function_number
from .electrical import audit
from .migrate import validate
from .native_migrate import validate as native_validate
from .memory import Decoder

SOURCE=ROOT/'Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch'


class Clock:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(SOURCE)
        self.parts=json.loads((VROOT/'clock-parts.json').read_text())
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(n):i for i,net in enumerate(self.nets) for n in net['nodes']}
        self.labels={name:i for i,net in enumerate(self.nets) for name in net['labels']}
        self.packages={c['ref']:c['value'] for c in self.sheet['components'] if c['ref'].startswith('U')}
        for value in self.packages.values():
            if value not in self.parts['devices']: raise ValueError('Unmodelled clock device: '+value)
        for ref,value in self.packages.items():
            instances=[c for c in self.sheet['components'] if c['ref']==ref]
            if {c['value'] for c in instances}!={value}: raise ValueError('Conflicting clock package values: '+ref)
            if any(function_number(c['lib_id'].split(':')[1])!=self.parts['devices'][value]['function'] for c in instances):
                raise ValueError('Clock symbol function does not match selected part: '+ref)
        oscillator=next(c for c in self.sheet['components'] if c['ref']=='Y1')
        if oscillator['value']!=self.parts['oscillator']['mpn']: raise ValueError('Oscillator part differs from timing contract')

    def n(self,ref,pin): return f'n[{self.nodes[ref,str(pin)]}]'

    def load(self):
        by_node={(c['ref'],p['number']):(c,p) for c in self.sheet['components'] for p in c['pins']}
        result=[]
        for i,net in enumerate(self.nets):
            drivers=[];receivers=[];cap=0
            for node in net['nodes']:
                c,p=by_node[tuple(node)]
                if c['ref'].startswith('U') and p['kind'] in ('O','T'): drivers.append(node)
                if c['ref'].startswith('U') and p['kind']=='I':
                    receivers.append(node);cap+=self.parts['devices'][c['value']]['input_cap_pf']
            if not drivers: continue
            connector=any(n[0].startswith('J') for n in net['nodes'])
            cap+=self.parts['constraints']['phase_connector_load_pf'] if connector else self.parts['constraints']['local_trace_cap_pf']
            result.append(dict(net=i,labels=net['labels'],drivers=drivers,receivers=receivers,load_upper_pf=cap,
                               characterized=cap<=50,scope='Pin-capacitance bounds plus allocated routing/connector capacitance.'))
        return result

    def hdl(self,corner=0):
        # Corner 0 is zero-delay functionality, 1 all maximum, 2+ deterministic
        # mixed min/max and independent edge/output delays. Min=0 avoids using
        # a typical propagation time as a guaranteed contamination bound.
        loads={r['net']:r['load_upper_pf'] for r in self.load()}
        serial=0
        def delay(value,node=None):
            nonlocal serial
            serial+=1;d=self.parts['devices'][value]
            maximum=d.get('max_delay_15pf_ns',d['max_delay_ns']) if loads.get(node,50)<=15 else d['max_delay_ns']
            if corner==0: return '0'
            if corner==1: return str(maximum)
            code=(serial*1103515245+corner*12345) ^ (serial*corner*2654435761)
            return str(maximum if (code>>(serial%13))&1 else 0)
        lines=['`timescale 1ns/1ps',
               'module counted_clock(input osc, reset_n, request, step, output [3:0] phase, output active, ready, output [3:0] state);',
               f'tri [{len(self.nets)-1}:0] n;',
               f'assign n[{self.labels["5V"]}]=1\'b1; assign n[{self.labels["GND"]}]=1\'b0;',
               f'assign {self.n("Y1",8)}=osc; assign {self.n("J1",3)}=reset_n; assign {self.n("J1",4)}=request; assign {self.n("J1",8)}=step;',
               'assign phase={'+','.join(self.n('J2',p) for p in (6,5,4,3))+'};',
               f'assign active={self.n("J1",5)}; assign ready={self.n("J1",6)};',
               'assign state={'+','.join(self.n('U1',p) for p in (15,10,7,2))+'};']
        for c in self.sheet['components']:
            ref=c['ref'];value=c['value'];unit=c['unit']
            if not ref.startswith('U'): continue
            d=self.parts['devices'][value];kind=d['function']
            inputs=[p for p in c['pins'] if p['kind']=='I']
            if not inputs: continue
            n=lambda pin:self.n(ref,pin)
            outputs=[p for p in c['pins'] if p['kind']=='O']
            if kind in ('04','08','32'):
                if len(outputs)!=1 or len(inputs)!=(1 if kind=='04' else 2): raise ValueError('Unexpected gate geometry')
                expression=('~'+n(inputs[0]['number']) if kind=='04' else
                            (' & ' if kind=='08' else ' | ').join(n(p['number']) for p in inputs))
                node=self.nodes[ref,outputs[0]['number']]
                lines.append(f'assign #({delay(value,node)},{delay(value,node)}) n[{node}]={expression};')
            elif kind=='244':
                for oe,ins,outs in [(1,[2,4,6,8],[18,16,14,12]),(19,[17,15,13,11],[3,5,7,9])]:
                    for a,b in zip(ins,outs):
                        node=self.nodes[ref,str(b)]
                        lines.append(f'assign #({delay(value,node)},{delay(value,node)}) {n(b)}={n(oe)} ? 1\'bz : {n(a)};')
            elif kind in ('175','74'):
                if kind=='175':
                    groups=[(4,9,1,2,3),(5,9,1,7,6),(12,9,1,10,11),(13,9,1,15,14)]
                else: groups=[(2,3,1,5,6)] if unit==1 else [(12,11,13,9,8)]
                for index,(inp,clk,reset,q,nq) in enumerate(groups):
                    if kind=='74':
                        preset=4 if unit==1 else 10
                        if self.nodes[ref,str(preset)]!=self.labels['5V']: raise ValueError('Active preset not modelled')
                    # Entry synchronizers deliberately have asynchronous inputs.
                    # Downstream paths still have setup/hold/reset monitors.
                    check_data=not (ref=='U8' and unit==1)
                    check_reset=ref not in ('U6','U7')
                    lines.append(f'clock_ff #({delay(value)},{delay(value)},{d["setup_ns"]},{d["hold_ns"]},'
                                 f'{d["reset_setup_ns"]},{int(check_data)},{int(check_reset)}) '
                                 f'{ref}_{unit}_{index}({n(inp)},{n(clk)},{n(reset)},{n(q)},{n(nq)},reset_n);')
            else: raise ValueError('Unsupported clock device')
        lines.append('endmodule')
        lines.append('''
module clock_ff #(parameter real TQ=0,TNQ=0,TSU=0,TH=0,TR=0,
                  parameter CHECK_DATA=1,CHECK_RESET=1)
  (input d,clk,reset_n,output q,nq,input system_reset_n);
  reg stored,armed=0;
  real last_data=-10000,last_clock=-10000,last_release=-10000;
  assign #(TQ) q=stored;
  assign #(TNQ) nq=~stored;
  always @(d) begin
    if(armed && CHECK_DATA && reset_n===1'b1 && $realtime-last_clock<TH) begin
      if(system_reset_n) $fatal(1,"clock hold %m at %0t",$time);
      else $display("RESET_ABORT hold collision %m at %0t",$time);
    end
    last_data=$realtime;
  end
  always @(posedge reset_n) last_release=$realtime;
  always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin stored<=0;armed=1;end
    else begin
      if(armed && CHECK_DATA && $realtime-last_data<TSU) begin
        if(system_reset_n) $fatal(1,"clock setup %m at %0t",$time);
        else $display("RESET_ABORT setup collision %m at %0t",$time);
      end
      if(armed && CHECK_RESET && $realtime-last_release<TR) $fatal(1,"clock reset recovery %m at %0t",$time);
      stored<=d; last_clock=$realtime;
    end
  end
endmodule
''')
        return '\n'.join(lines)


def budget(circuit):
    parts=circuit.parts
    d=parts['devices'];c=parts['constraints'];osc=parts['oscillator']
    period=1e9/(osc['frequency_hz']*(1+osc['stability_ppm']/1e6))
    half=period*min(osc['duty_min'],1-osc['duty_max'])
    inv=d['SN74AHCT04N']['max_delay_ns'];buf=d['SN74AHCT244N']['max_delay_ns']
    ff=d['CD74AC175M96'];sync=d['SN74AHC74N'];uncertainty=c['clock_routing_and_jitter_ns']
    forward=half-inv-buf-uncertainty
    backward=half-2*inv-buf-uncertainty
    loads={tuple(driver):r['load_upper_pf'] for r in circuit.load() for driver in r['drivers']}
    logic=sum(d[value]['max_delay_15pf_ns'] if loads[ref,'3']<=15 else d[value]['max_delay_ns']
              for ref,value in [('U4','SN74AHC32N'),('U5','SN74AHC08N')])
    rows=[dict(path='P to N: Johnson next-state logic',available_ns=forward,required_ns=ff['max_delay_ns']+logic+ff['setup_ns']),
          dict(path='N to P: staging register',available_ns=backward,required_ns=ff['max_delay_ns']+ff['setup_ns']),
          dict(path='N to P: request and reset synchronizers',available_ns=backward,required_ns=sync['max_delay_ns']+sync['setup_ns']),
          dict(path='P to N: synchronized request through next-state logic',available_ns=forward,required_ns=sync['max_delay_ns']+logic+ff['setup_ns']),
          dict(path='Shortest opposite-edge hold window, zero contamination delay',available_ns=min(forward,backward),required_ns=max(ff['hold_ns'],sync['hold_ns'])),
          dict(path='Reset release to downstream edge',available_ns=min(forward,backward),required_ns=sync['max_delay_ns']+max(ff['reset_setup_ns'],sync['reset_setup_ns'])),
          dict(path='Shortest internal clock pulse',available_ns=backward,required_ns=max(ff['pulse_ns'],sync['pulse_ns'])),
          dict(path='External reset pulse after worst assertion/release spread',
               available_ns=c['minimum_reset_input_ns']-2*inv-sync['max_delay_ns'],required_ns=max(ff['pulse_ns'],sync['pulse_ns']))]
    for row in rows: row['margin_ns']=row['available_ns']-row['required_ns']
    # A launch can be late while the capture takes zero delay. No typical or
    # minimum device delay is needed for this conservative phase interval.
    output_spread=ff['max_delay_ns']+buf+c['output_routing_and_jitter_ns']
    phase_min=3*period-output_spread
    pilot=json.loads((VROOT/'requirements.json').read_text())['pilot']
    required=sum(pilot[k] for k in ('source_tco_ns','rom_access_ns','buffer_delay_ns','setup_ns','clock_uncertainty_ns'))
    return dict(oscillator=dict(osc),oscillator_period_min_ns=period,paths=rows,phase_nominal_ns=3e9/osc['frequency_hz'],
                phase_min_ns=phase_min,pilot_required_ns=required,pilot_margin_ns=phase_min-required,
                output_pulse_min_ns=4*period-output_spread,
                passing=all(r['margin_ns']>=0 for r in rows) and phase_min>=required and
                        c['power_on_reset_after_valid_supply_ms']>=osc['startup_max_ms'],
                status='conditional bounds, not physical qualification',
                assumptions=parts['constraints'],unqualified=parts['unqualified'])


def simulate(circuit,folder,corner=0,duty=0.5,ppm=0):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'clock.sv').write_text(circuit.hdl(corner))
    pilot=json.loads((VROOT/'requirements.json').read_text())['pilot']
    (folder/'parameters.vh').write_text('\n'.join(f'`define {k.upper()} {v}' for k,v in pilot.items())+'\n')
    source=VROOT/'hdl/clock_candidate_tb.sv'
    code,log=command(['iverilog','-g2012','-s','clock_candidate_tb','-o','clock.vvp','clock.sv',source],cwd=folder)
    if code:
        (folder/'clock.log').write_text(log)
        raise RuntimeError('Counted-clock HDL compilation failed: '+log)
    code,runlog=command(['vvp','clock.vvp',f'+DUTY={duty}',f'+PPM={ppm}'],cwd=folder)
    log+=runlog
    (folder/'clock.log').write_text(log)
    return code==0 and 'DONE counted-clock' in log,log


def run():
    folder=BUILD/'clock';folder.mkdir(parents=True,exist_ok=True)
    circuit=Clock();structural=audit(circuit.sheet);loads=circuit.load();timing=budget(circuit)
    migration=validate(circuit.sheet,folder/'schematics')
    native=native_validate(circuit.sheet,folder/'native')
    rows=[]
    for corner in range(10):
        for duty,ppm in [(d,p) for d in (0.4,0.5,0.6) for p in (-100,0,100)]:
            name=f'c{corner}-d{int(duty*100)}-ppm{ppm}'
            ok,log=simulate(circuit,folder/name,corner,duty,ppm)
            counts=re.search(r'DONE counted-clock steps=(\d+) stops=(\d+) resets=(\d+) button_steps=(\d+) transitions=(\d+) transfers=(\d+)',log)
            idle=re.search(r'idle_phases=(\d+)',log)
            rows.append(dict(name=name,corner=corner,duty=duty,ppm=ppm,passed=ok,
                             coverage=dict(zip(('handshake_steps','stops','resets','button_steps','transitions','transfers'),map(int,counts.groups()))) if counts else {},
                             reset_abort_timing_collisions=log.count('RESET_ABORT'),
                             idle_phases=int(idle[1]) if idle else None,
                             log=str((folder/name/'clock.log').relative_to(BUILD))))
    sources=json.loads((VROOT/'vendor/clock/manifest.json').read_text())
    for entry in sources['files']:
        path=VROOT/'vendor/clock'/entry['file']
        if digest(path)!=entry['sha256']: raise ValueError('Clock source excerpt changed: '+str(path))
        (folder/'sources').mkdir(exist_ok=True)
        (folder/'sources'/entry['file']).write_bytes(path.read_bytes())
    write_json(folder/'parts.json',circuit.parts)
    write_json(folder/'sources/manifest.json',sources)
    (folder/'Counted-Clock.sch').write_bytes(SOURCE.read_bytes())
    decoder=Decoder();idle_cases=[]
    for row in rows:
        phase=row['idle_phases']
        if phase is None: continue
        for page in range(256):
            result=decoder.evaluate(page<<8,0,write=True,phase2=(phase>>2)&1,phase3=(phase>>3)&1)
            idle_cases.append(dict(corner=row['name'],page=page,passed=not result['ram_writing'] and not result['io_load']))
    idle_memory=dict(cases=len(idle_cases),failed=[r for r in idle_cases if not r['passed']],
                     scope='Actual final HDL phase levels applied to settled KiCad memory decode with MEM_load held active; no transient write-pulse qualification.')
    old_idle=[]
    for page in range(256):
        result=decoder.evaluate(page<<8,0,write=True,phase2=1,phase3=1)
        if result['ram_writing'] or result['io_load']: old_idle.append(page)
    idle_memory['original_high_idle_write_active_pages']=old_idle
    details=dict(source_hash=digest(SOURCE),structural=structural,loads=loads,migration=migration,native_migration=native,idle_memory=idle_memory,
                 timing=timing,simulations=rows,manufacturer_sources=sources,
                 scope='Pin-derived core, ideal oscillator boundary, asynchronous request with entry-stage metastability excluded. '
                       'Whole-cycle stop, latched single-step and continuous running are tested. Switch debounce, HALT arbitration, power supervisor and bus integration remain open.')
    write_json(folder/'candidate.json',details)
    ok=(not structural['findings'] and all(r['characterized'] for r in loads) and migration['status']=='pass' and native['status']=='pass'
        and timing['passing'] and all(r['passed'] for r in rows) and
        idle_memory['cases']==90*256 and not idle_memory['failed'] and old_idle==list(range(64,256)))
    core=evidence('clock-candidate','Counted-clock candidate core','pass' if ok else 'fail',
                    f'{sum(r["passed"] for r in rows)}/{len(rows)} corner/duty/frequency runs; '
                    f'phase lower bound {timing["phase_min_ns"]:.2f} ns; conditional pilot margin {timing["pilot_margin_ns"]:+.2f} ns.',
                    budget=timing,
                    artifacts=['clock/candidate.json','clock/parts.json','clock/Counted-Clock.sch',
                               'clock/sources/manifest.json',*[f'clock/sources/{e["file"]}' for e in sources['files']],
                               'clock/c0-d50-ppm0/clock.sv','clock/c0-d50-ppm0/clock.vcd',
                               'clock/schematics/Counted-Clock.kicad_sch','clock/schematics/Counted-Clock.xml',
                               'clock/native/Counted-Clock.kicad_sch','clock/native/Counted-Clock.xml','clock/native/comparison.json',
                               *[r['log'] for r in rows]],limitation=details['scope']+' '+timing['status']+'.')
    qualification=evidence('physical-clock','Physical clock qualification','limited' if ok else 'fail',
                           'Counted-clock candidate has sourced conditional bounds and pin-derived tests. '
                           'Input slew, jitter, PCB loads, metastability, power supervisor, debounce/HALT and backplane integration remain open.',
                           artifacts=['clock/candidate.json','clock/parts.json'],
                           limitation='The active seven-sheet baseline still contains the original unqualified RC phase generator. Candidate results do not qualify that circuit.')
    return [core,qualification]

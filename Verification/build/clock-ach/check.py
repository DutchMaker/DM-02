"""Native pin parity, oscillator contract and conditional ACH clock exercises."""
from pathlib import Path
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
SANDBOX=HERE/'sandbox'
sys.path.insert(0,str(SANDBOX/'Verification'))
from dm02 import clock
from dm02.legacy import read_sheet,connectivity
from dm02.native_migrate import validate as native_validate


def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2)+'\n')


def contract(circuit):
    oscillator=next(c for c in circuit.sheet['components'] if c['ref']=='Y1')
    assert oscillator['value']=='ACH-4.000MHZ-EK','oscillator MPN'
    assert oscillator['lib_id']=='DM02-ACH:ACH-4MHz','oscillator symbol'
    assert oscillator['footprint']=='Oscillator:Oscillator_DIP-8','oscillator footprint'
    pins={p['number']:p for p in oscillator['pins']}
    assert set(pins)=={'1','4','5','8'},'oscillator physical pins'
    for pin,name in [('4','GND'),('5','OSC_TTL'),('8','5V')]:
        assert circuit.nodes['Y1',pin]==circuit.labels[name],f'oscillator {pin} to {name}'
    nc=circuit.nets[circuit.nodes['Y1','1']]
    assert nc['nodes']==[['Y1','1']] and not nc['labels'],'NC isolation'
    assert pins['1']['kind']=='N' and pins['5']['kind']=='O','oscillator pin types'
    assert circuit.parts['oscillator']['output_pin']=='5','model output pin'
    net=circuit.nets[circuit.labels['OSC_TTL']]
    assert {tuple(n) for n in net['nodes']}=={('Y1','5'),('U3','1')},'oscillator receiver fanout'
    load=circuit.parts['devices']['SN74AHCT04N']['input_cap_pf']+circuit.parts['constraints']['local_trace_cap_pf']
    assert load<=circuit.parts['oscillator']['standard_load_pf'],'oscillator standard load exceeded'
    return dict(pin_functions={'1':'NC','4':'GND','5':'OSC_TTL','8':'5V'},receiver=['U3','1'],
        allocated_input_pf=10,allocated_other_pf=5,total_allocated_pf=load,standard_load_pf=15,
        spare_allocation_pf=15-load,physical_load_qualified=False)


def main():
    run=subprocess.run([sys.executable,str(SANDBOX/'Verification/designs/clock_candidate.py'),'--write'],capture_output=True,text=True)
    assert run.returncode==0,run.stdout+run.stderr
    circuit=clock.Clock();pin_contract=contract(circuit)
    native=native_validate(circuit.sheet,HERE/'native');assert native['status']=='pass',native
    # Functional circuit parity after the intentional oscillator terminal map.
    baseline_path=SANDBOX/'Circuits/KiCad/Power-Clock/candidates/C1-before.sch'
    shutil.copyfile(HERE/'sources/Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch',baseline_path)
    baseline=read_sheet(baseline_path)
    remap={'7':'4','8':'5','14':'8','1':'1'}
    original={frozenset((r,remap[p] if r=='Y1' else p) for r,p in n['nodes']) for n in connectivity(baseline)}
    actual={frozenset(tuple(n) for n in net['nodes']) for net in circuit.nets}
    assert original==actual,'non-oscillator connectivity changed'
    half_supply=clock.budget(circuit)
    sensitivity=copy.deepcopy(circuit)
    # Deliberately assumed digital receiver duty; not derived as a guaranteed
    # bound from the ACH sheet, whose Tr/Tf measurement levels are unspecified.
    sensitivity.parts['oscillator'].update(duty_min=.37,duty_max=.63)
    wider=clock.budget(sensitivity)
    write('timing.json',dict(half_supply_reference_only=half_supply,assumed_receiver_duty_sensitivity=wider,
        physical_qualification=False,remark='Neither analysis establishes physical receiver-threshold duty, slew or jitter.'))
    mutations=[]
    for name in ('old-output-pin','extra-oscillator-load','dip14-footprint','swap-supply-output-labels'):
        bad=copy.deepcopy(circuit)
        if name=='old-output-pin':bad.parts['oscillator']['output_pin']='8'
        elif name=='extra-oscillator-load':bad.parts['constraints']['local_trace_cap_pf']=5.1
        elif name=='dip14-footprint':next(c for c in bad.sheet['components'] if c['ref']=='Y1')['footprint']='Oscillator:Oscillator_DIP-14'
        else:bad.labels['5V'],bad.labels['OSC_TTL']=bad.labels['OSC_TTL'],bad.labels['5V']
        try:contract(bad)
        except AssertionError as error:mutations.append(dict(fault=name,detected=True,diagnostic=str(error)))
        else:raise AssertionError('Oscillator contract fault escaped '+name)
    rows=[]
    for corner in range(10):
        for duty in (.37,.45,.5,.55,.63):
            for ppm in (-30,30):
                name=f'c{corner}-d{int(duty*100)}-ppm{ppm}'
                ok,log=clock.simulate(circuit,HERE/'simulations'/name,corner,duty,ppm)
                match=re.search(r'DONE counted-clock steps=(\d+) stops=(\d+) resets=(\d+) button_steps=(\d+) transitions=(\d+) transfers=(\d+)',log)
                row=dict(name=name,corner=corner,duty=duty,ppm=ppm,passed=ok,
                    scope='hypothetical receiver-duty sensitivity' if duty in (.37,.63) else 'half-supply duty used as ideal digital stimulus',
                    counts=dict(zip(('steps','stops','resets','button_steps','transitions','transfers'),map(int,match.groups()))) if match else {})
                rows.append(row)
                if not ok:
                    write('simulations.json',rows)
                    raise AssertionError(name+' failed; see simulation log')
    write('simulations.json',rows)
    for row in json.loads((HERE/'source-manifest.json').read_text()):
        path=HERE.parents[2]/row['source']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'Normal source changed during experiment'
    write('summary.json',dict(passed=True,scope='Isolated pin-derived ACH candidate; no normal acceptance change',
        native=native,pin_contract=pin_contract,normalized_net_groups_preserved=len(actual),
        simulations=len(rows),passing_simulations=sum(r['passed'] for r in rows),faults=mutations,
        min_sensitivity_margin_ns=min(r['margin_ns'] for r in wider['paths']),
        half_supply_budget_pass=half_supply['passing'],sensitivity_budget_pass=wider['passing'],
        physical_qualification=False,fabrication_ready=False))
    print('ACH candidate:',len(rows),'simulations pass;',native['physical_pins'],'native pins agree; four contract faults rejected')


if __name__=='__main__':main()

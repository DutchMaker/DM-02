"""OS1 native oscillator boundaries and separate load/slew/duty obligations."""
from copy import deepcopy
import json
from .common import VROOT,BUILD
from . import mar_distribution as md

STUDY=BUILD/'cp1-oscillator'
CONTRACT=VROOT/'oscillator-interface.json'
require=md.require


def audit(inventory=None,contract=None):
    inventory=inventory or json.loads((md.STUDY/'final/loads.json').read_text())
    contract=contract or json.loads(CONTRACT.read_text())
    require(contract['revision']=='CP1-OS1' and contract['physical_qualification'] is False,'Invalid OS1 scope')
    require(contract['oscillator_mpn']=='ACH-4.000MHZ-EK' and contract['oscillator_rating']['output_load_pf']==15,'Unqualified oscillator option')
    pins=inventory['pins'];nets={n['net']:n for n in inventory['nets']}
    rail={pins['Y1001.8']['net']:1,pins['Y1001.4']['net']:0}
    def row(pin,raw=False):
        n=nets[pins[pin]['net']];require(n['driver_pins']==[pin],'Unexpected oscillator-path drivers')
        scenario=next(s for s in n['scenarios'] if s['driver']==pin)
        allocation=contract['raw_allocation' if raw else 'conditioned_allocation']
        count=len(scenario['load_pins'])+1
        parasitic=count*allocation['socket_pf_per_attached_pin']+allocation['trace_via_pad_pf']+allocation['probe_pf']
        fixture=15 if raw else 50
        total=scenario['ic_only_pf']+parasitic
        require(not n['contacts'],'Unexpected clock connector stub')
        require(total<fixture,'Clock planning allocation exhausted')
        return dict(driver=pin,net=n['net'],names=n['native_names'],pins=[pins[p] for p in n['pins']],
            ic_only_pf=scenario['ic_only_pf'],unknown_pin_maxima=scenario['unknown_pin_maxima'],
            attached_pin_count=count,parasitic_allocation_pf=parasitic,planning_total_pf=total,
            fixture_or_rating_pf=fixture,planning_margin_pf=fixture-total,
            actual_load_pf=None,physical_qualification=False)
    result=[]
    for front in contract['frontends']:
        osc=front['oscillator'];receiver=front['receiver'];raw=row(osc+'.5',True)
        require(pins[osc+'.5']['part']==contract['oscillator_mpn'],'Oscillator identity changed')
        require(rail.get(pins[osc+'.8']['net'])==1 and rail.get(pins[osc+'.4']['net'])==0,'Oscillator rails changed')
        require(nets[pins[osc+'.1']['net']]['pins']==[osc+'.1'],'NC oscillator pin driven')
        require({p['id'] for p in raw['pins']}=={osc+'.5',receiver},'Unexpected raw-clock receiver')
        require(pins[receiver]['part']==front['receiver_part'],'First receiver family changed')
        expected=3 if front['name']=='CPU' else 6
        require(front['timing_fixture_edge_ns']==expected,'Conflated receiver timing fixture')
        stages=[row(p) for p in front['conditioned_outputs']]
        for inp,out,kind in front['arcs']:
            require(pins[inp]['reference']==pins[out]['reference'],'Cross-package clock arc')
            require((kind=='invert')==(pins[inp]['part']=='SN74AHCT04N'),'Incorrect clock polarity')
            if kind=='buffer':
                ref=pins[inp]['reference'];require(rail.get(pins[ref+'.1']['net'])==0,'Clock buffer enable not grounded')
        # Pin-level topology assertions prevent source/root-net aliases from hiding.
        if front['name']=='CPU':
            for a,b in [('U1003.2','U1003.3'),('U1003.2','U1010.2'),('U1003.2','U1010.6'),('U1003.4','U1010.4')]:
                require(pins[a]['net']==pins[b]['net'],'Broken CPU clock root path')
            require(pins['U1003.2']['net']!=pins['U1003.4']['net'],'Collapsed opposite clock roots')
        result.append(dict(name=front['name'],raw=raw,conditioned=stages,arcs=front['arcs'],
            timing_fixture_edge_ns=expected,recommended_input_transition=front['recommended_input_transition'],
            applied_edge_ns=None,threshold_duty=None,jitter_ns=None,startup_ns=None,physical_qualification=False))
    require({r['name'] for r in result}=={'CPU','TEXT'},'Both independent clocks required')
    return dict(revision='CP1-OS1',frontends=result,contract=contract,hardware_changed=False,physical_qualification=False,
        findings=[
            'Each oscillator has exactly one 10 pF allocated receiver, not two 5 pF receivers.',
            'CPU first receiver is AHCT04: <=3 ns input timing fixture, 20 ns/V recommended transition limit. TEXT first receiver is HCT244: 6 ns timing fixture and separate much slower recommended input-transition limits.',
            'ACH 10 ns rise/fall rating has no transition-reference levels stated in the archived 2016 sheet; it proves neither receiver timing fixture.',
            '45/55 symmetry is measured at Vdd/2, while logic timing references and switching thresholds differ. Duty at a receiver and propagation asymmetry must be measured separately.',
            'CPU first inverter reverses oscillator polarity; second restores it. TEXT first buffer is non-inverting. Both oscillators remain free running during HALT.',
            'Selected EK suffix provides E temperature and K stability options only. The optional 50 pF rating and A pin-1 enable times cannot be borrowed.',
            'No published jitter bound is supplied by this source. A clean synthetic 4 MHz square wave is not a clock qualification.'
        ])


def faults(inventory=None):
    inventory=inventory or json.loads((md.STUDY/'final/loads.json').read_text());results={}
    for name in ('extra-raw-receiver','wrong-CPU-fixture','borrow-50pF-option','drive-NC-pin','passive-10pF-probe','wrong-polarity'):
        data=deepcopy(inventory);spec=json.loads(CONTRACT.read_text())
        if name=='extra-raw-receiver':
            n=next(n for n in data['nets'] if n['net']==data['pins']['Y1001.5']['net'])
            n['pins'].append('U1003.3')
        elif name=='wrong-CPU-fixture':spec['frontends'][0]['timing_fixture_edge_ns']=6
        elif name=='borrow-50pF-option':spec['oscillator_rating']['output_load_pf']=50
        elif name=='drive-NC-pin':
            next(n for n in data['nets'] if n['net']==data['pins']['Y1001.1']['net'])['pins'].append('Y1001.8')
        elif name=='passive-10pF-probe':spec['raw_allocation']['probe_pf']=10
        else:spec['frontends'][0]['arcs'][0][2]='buffer'
        try:audit(data,spec)
        except ValueError as e:results[name]=dict(detected=True,reason=str(e))
        else:raise ValueError('Undetected OS1 mutation: '+name)
    return results

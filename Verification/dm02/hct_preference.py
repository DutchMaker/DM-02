"""HP1: exact-part sourcing screen over every native MD1 logic package."""
from collections import Counter, defaultdict
import json
import re
from .common import BUILD, digest
from . import mar_distribution as md

STUDY=BUILD/'cp1-hct-preference'
require=md.require
# Manually reviewed manufacturer tables. Values retain their own test conditions;
# these are NOT qualified whole-link delay models or procurement availability.
TABLES={
    '00':dict(mpn='SN74HCT00N',source='sn74hct00',pages=[3,4,5,6],delay_ns=25,transition_ns=19),
    '04':dict(mpn='SN74HCT04N',source='sn74hct04',pages=[3,4,5,6],delay_ns=25,transition_ns=19),
    '08':dict(mpn='SN74HCT08N',source='sn74hct08',pages=[3,4,5,6],delay_ns=30,transition_ns=19),
    '32':dict(mpn='SN74HCT32N',source='sn74hct32',pages=[3,4,5,6],delay_ns=30,transition_ns=19),
    '74':dict(mpn='SN74HCT74N',source='sn74hct74',pages=[3,4,5,6,7],delay_ns=44,
        clock_q_ns=35,async_q_ns=44,setup_ns=15,hold_ns=0,reset_removal_ns=0,clock_pulse_ns=23,reset_pulse_ns=20),
    '157':dict(mpn='SN74HCT157N',source='sn74hct157',pages=[1,2,3,4,5],delay_ns=40,
        data_ns=35,select_ns=40,strobe_ns=33,transition_ns=19,
        timing_status='withheld pending clarification of PRODUCT PREVIEW footer; watermark lies in SN54 column'),
    '244':dict(mpn='SN74HCT244N',source='sn74hct244',pages=[3,4,6,7,8,9],delay_ns=42,
        enable_ns=53,disable_ns=53,transition_ns=18,temperature_c=[-55,125],
        fixture_note='Figure6-1 noteC: PRR<=1MHz, ZO=50ohm, tr=tf=6ns from0.3 to2.7V; input/output delay references1.3V. CL includes probe/fixture. Output transition10-90%. Recommended input transition500ns is a different constraint.'),
    '175':dict(mpn='CD74HCT175E',source='cd74hct175',pages=[1,2,4,5,6,7],delay_ns=44,
        clock_q_ns=41,async_q_ns=44,setup_ns=25,hold_ns=5,reset_removal_ns=5,clock_pulse_ns=25,reset_pulse_ns=25),
    '377':dict(mpn='CD74HCT377E',source='cd74hct377',pages=[1,2,4,5,6],delay_ns=48,
        clock_q_ns=48,setup_ns=15,hold_ns=3,enable_hold_ns=5,clock_pulse_ns=25,
        fixture_note='SCHS184C HCT rows, not HC rows. No reset; active-low enable, positive-edge capture. TTL input thresholds remove the HC input-threshold obligation, but output slew/timing still require qualification.')
}
MAP={**{'SN74AHCT'+f+'N':f for f in ('00','04','08','32','157','244')},
     **{'SN74AHC'+f+'N':f for f in ('08','32','74')},'CD74ACT175E':'175','SN74HC377N':'377'}


def parts(build=BUILD):
    root=build/'cp1-hct-preference/sources';retrieval=json.loads((root/'retrieval.json').read_text());out={}
    for function,data in TABLES.items():
        row=dict(voltage_v=4.5,temperature_c=[-40,85],load_pf=50,input_edge_ns=6,
            input_thresholds_v=dict(vih_min=2,vil_max=0.8),input_cap_screen_pf=10,
            min_propagation_ns=None,timing_status='table maximum at stated fixture; full OC1 link unqualified')|data
        stem=data['source'];record=retrieval[stem]
        require(digest(root/(stem+'.pdf'))==record['sha256'],'HCT manufacturer PDF differs: '+stem)
        text=(root/(stem+'.txt')).read_text()
        line=next((s.strip() for s in text.splitlines() if re.match(r'\s*'+data['mpn']+r'\s+(Active|NRND)\s+Production\s+PDIP',s)),None)
        require(line is not None,'Missing exact DIP lifecycle row: '+data['mpn'])
        row.update(provenance=record,lifecycle_line=line,lifecycle='NRND' if 'NRND' in line else 'Active',
            distributor_stock_verified=False,owned_exact_quantity=None,substitution_qualified=False)
        out[function]=row
    return out


def pin_roles(function):
    """DIP pin directions checked against manufacturer pin diagrams, not names."""
    if function in ('00','08','32'):count=14;outputs=[3,6,8,11];ground=7
    elif function=='04':count=14;outputs=[2,4,6,8,10,12];ground=7
    elif function=='74':count=14;outputs=[5,6,8,9];ground=7
    elif function=='157':count=16;outputs=[4,7,9,12];ground=8
    elif function=='175':count=16;outputs=[2,3,6,7,10,11,14,15];ground=8
    elif function=='244':count=20;outputs=[18,16,14,12,3,5,7,9];ground=10
    elif function=='377':count=20;outputs=[2,5,6,9,12,15,16,19];ground=10
    else:raise ValueError('Unknown HCT function')
    return {str(i):('power_in' if i in (count,ground) else 'tri_state' if function=='244' and i in outputs
        else 'output' if i in outputs else 'input') for i in range(1,count+1)}


def review(build=BUILD,inventory=None):
    inventory=inventory or json.loads((build/'cp1-mar-distribution/final/loads.json').read_text())
    tables=parts(build);old=json.loads((build/'cp1-hct273/component-review.json').read_text())['selected_models']
    pins=inventory['pins'];nets={r['net']:r for r in inventory['nets']};by_ref=defaultdict(list)
    for p in pins.values():
        if p['reference'].startswith('U'):by_ref[p['reference']].append(p)
    rows=[];counts=Counter()
    for ref,ps in sorted(by_ref.items()):
        part=ps[0]['part'];board=ps[0]['board'];counts[part]+=1
        if part not in MAP:continue
        function=MAP[part];table=tables[function]
        require({p['pin']:p['symbol_type'] for p in ps}==pin_roles(function),'DIP pin role mismatch: '+ref)
        links=[]
        for p in sorted(ps,key=lambda p:int(p['pin'])):
            net=nets[p['net']]
            if not (p['receiver'] or p['driver']):continue
            links.append(dict(pin=p['id'],pin_name=p['pin_name'],role=p['electrical_role'],net=p['net'],
                native_names=net['native_names'],rail=net['rail'],driver_pins=net['driver_pins'],
                receiver_pins=net['receiver_pins'],contacts=net['contacts'],
                loads=[s for s in net['scenarios'] if s['driver']==p['id']],
                peers=[dict(pin=k,part=pins[k]['part'],board=pins[k]['board'],role=pins[k]['electrical_role'])
                    for k in net['pins'] if k!=p['id'] and (pins[k]['receiver'] or pins[k]['driver'])]))
        clocks=[p['id'] for p in ps if p['pin_name'] in ('C','CP','Cp')]
        controls=[p['id'] for p in ps if p['pin_name'] in ('~{R}','~{S}','~{Mr}','~{E}','1OE','2OE','E','S')]
        if board=='MB1':
            action='candidate-first';reason='Two always-enabled local MAR buffers;16 output arcs and48 ME1 receivers. Test SN74HCT244N42ns plus zero/mixed-delay profiles in HB1.'
        elif function=='377':
            action='candidate-next';reason='TTL input thresholds address the HC377 full-supply compatibility concern. Clock-Q rises40->48ns; data/enable hold3/5ns. Recheck AL1/RG1 pipeline, register/ALU suite and complete ROM/opcode regressions.'
        elif board=='C1' or clocks:
            action='retain-pending-clock-review';reason='Clock/phase/sequencing or captured control. Changed thresholds, propagation, asynchronous release and pulse widths require per-stage min/max timing, startup/stop/step and affected full-system verification.'
        elif function=='157':
            action='retain-pending-mux-review';reason='Data/select/strobe arcs differ from12ns AHCT model. Resolve SN74 preview provenance or qualify existing CD74HCT157E alternative; recheck decode glitches, settle and hold across attached paths.'
        elif function=='244':
            action='retain-pending-distribution-review';reason='42ns data/53ns OE replaces9.5/13ns model. Inspect every connected reset/control/data fanout and earliest invalid-data/driver handover before replacing; board-local buffering alone is insufficient.'
        else:
            action='retain-pending-path-review';reason='Longer combinational delay changes decode/gating and reconvergent paths. Recheck pulses, setup/hold and handover on the listed native links; no blanket gate-family substitution.'
        rows.append(dict(reference=ref,board=board,source_reference=ps[0]['source_reference'],current_part=part,
            candidate_part=table['mpn'],function=function,pin_roles_match=True,existing_model=old[part],
            action=action,reason=reason,clock_pins=clocks,control_pins=controls,links=links,
            candidate_delay_delta_ns=table['delay_ns']-old[part]['max_delay_ns'],
            actual_load_pf=None,loaded_slew_ns=None,min_hold_margin_ns=None,substitution_qualified=False))
    families=Counter()
    for part,count in counts.items():
        family=next((f for f in ('AHCT','AHC','ACT','HCT','HC') if f in part),'memory');families[family]+=count
    require(len(by_ref)==272 and len(rows)==142,'Changed MD1 package inventory')
    return dict(revision='CP1-HP1',native_revision='CP1-MD1',dip_count=len(by_ref),families=dict(families),
        part_counts=dict(sorted(counts.items())),reviewed_non_hct=len(rows),parts=tables,packages=rows,
        actions=dict(Counter(r['action'] for r in rows)),hardware_changed=False,physical_qualification=False,
        accepted_substitutions=0,scope='Exact-part/per-reference sourcing and requalification screen. Load rows retain inherited MD1 conditions; replacement loads and full timing are not certified. Generic owned SN74HCTxxx does not establish exact suffix/count.',
        supply_scope='OC1 remains4.75..5.25V/0..50C,500kHz microcycles.4.5V data-sheet tables are conditional screening points, not proof of actual loaded timing throughout OC1.',
        sourcing='Owner reports HCT easier to obtain. Active/NRND are manufacturer lifecycle observations from retrieved addenda, not stock checks. Existing126HCT packages retain their exact CD/SN suffixes; manufacturer-prefix substitutions require separate review.')

"""HR1 exact connected driver/receiver DC and load-table screen."""
from .common import BUILD,digest
from . import hct_registers as hr

SOURCES={p:'cp1-link-loads/sources/'+p.lower().removesuffix('n')+'.txt' for p in
    ('SN74AHCT00N','SN74AHCT08N','SN74AHCT157N','SN74AHCT244N','SN74HCT245N','SN74HCT574N')}
SOURCES.update({'M27C322-100F1':'cp1-link-loads/sources/m27c322.txt',
    hr.PART:'cp1-hct-preference/sources/cd74hct377.txt'})


def review(inventory,build=BUILD):
    pins=inventory['pins'];nets={n['net']:n for n in inventory['nets']};rows=[]
    targets=sorted({p['reference'] for p in pins.values() if p['part']==hr.PART})
    hr.require(len(targets)==6,'HR1 path targets')
    for ref in targets:
        for p in sorted((p for p in pins.values() if p['reference']==ref),key=lambda p:int(p['pin'])):
            net=nets[p['net']]
            if not (p['receiver'] or p['driver']):continue
            upstream=[];downstream=[]
            if net['rail'] is None:
                for driver in net['driver_pins'] if p['receiver'] else []:
                    part=pins[driver]['part'];hr.require(part in SOURCES and part!=hr.PART,'HR1 unexpected input driver')
                    voh,vol,current=(3.84,0.33,6) if part in ('SN74HCT245N','SN74HCT574N') else (3.8,0.44,8)
                    upstream.append(dict(pin=driver,part=part,source=SOURCES[part],voltage_v=4.5,
                        test_current_ma=current,voh_min_v=voh,vol_max_v=vol,vih_min_v=2,vil_max_v=0.8,
                        high_margin_before_offsets_v=round(voh-2,2),low_margin_before_offsets_v=round(0.8-vol,2)))
                for receiver in net['receiver_pins'] if p['driver'] else []:
                    part=pins[receiver]['part'];hr.require(part in ('M27C322-100F1','SN74HCT245N'),'HR1 unexpected output receiver')
                    downstream.append(dict(pin=receiver,part=part,source=SOURCES[part],vih_min_v=2,vil_max_v=0.8,
                        high_margin_before_offsets_v=1.84,low_margin_before_offsets_v=0.47))
            rows.append(dict(pin=p['id'],board=p['board'],source_reference=p['source_reference'],pin_name=p['pin_name'],
                role=p['electrical_role'],rail=net['rail'],upstream=upstream,downstream=downstream,
                load_scenarios=net['scenarios'],contacts=net['contacts'],unknown_parasitics=net['unknown_parasitics']))
    return dict(revision='CP1-HR1',physical_qualification=False,paths=rows,
        source_hashes={path:digest(build/path) for path in SOURCES.values()},
        output_condition=dict(source='SCHS184C page4 HCT -40..85C',voltage_v=4.5,current_ma=4,voh_min_v=3.84,vol_max_v=0.33),
        input_condition=dict(source='SCHS184C page4',voltage_v=[4.5,5.5],vih_min_v=2,vil_max_v=0.8),
        timing_condition=dict(source='SCHS184C pages5-6 HCT -40..85C',voltage_v=4.5,load_pf=50,input_edge_ns=6,
            input_edge_levels_v=[0.3,2.7],delay_reference_v=1.3,clock_q_max_ns=48,setup_ns=15,data_hold_ns=3,
            enable_hold_ns=5,clock_pulse_ns=25,output_transition_max_ns=19,minimum_propagation_ns=None),
        scope='DC table-point comparison before rail/ground offsets. Actual total DC current, pin voltage ceilings, socket/layout/probe capacitance, loaded edges and full OC1 link timing remain unqualified. HCT supply-current increase at TTL input levels is separate from input leakage. Reset-time timing violations propagate unknown storage; later valid synchronous initialisation demonstrates digital recovery only, not metastability resolution.')

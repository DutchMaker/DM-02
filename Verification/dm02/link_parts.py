"""LL1 capacitance review: table maxima retain their measurement conditions."""
import json
import re
from .common import BUILD,digest

STUDY=BUILD/'cp1-link-loads'


def review():
    sources=STUDY/'sources'
    provenance=json.loads((sources/'manifest.json').read_text())
    old=json.loads((BUILD/'cp1-hct273/component-review.json').read_text())['selected_models']
    devices={k:v['source'] for k,v in old.items()}
    for n in ('00','04','08','32','74','151','153','154','157','161','244','273'):
        devices['CD74HCT'+n+'E']='cd74hct'+n
    devices['ACH-4.000MHZ-EK']='abracon-ach-2016'
    rows={}
    for name,stem in sorted(devices.items()):
        path=sources/(stem+'.txt');text=path.read_text();lines=text.splitlines()
        # Retain literal evidence, including page markers and table headers in the source.
        evidence=[];page=None
        for i,line in enumerate(lines):
            m=re.search(r'(?:PDF page |PAGE )(\d+)',line)
            if m:page=int(m[1])
            if re.search(r'\bCi\b|\bCI\b|\bCIN\b|\bCOUT\b|\bCI/O\b|\bCo\b|Input capacitance|Output Load|Input transition|Input Rise and Fall|Input tr,',line,re.I):
                evidence.append(dict(page=page,line=i+1,text='\n'.join(lines[max(0,i-1):i+3])))
        cap=10;condition='Maximum table value; supply column unspecified for capacitance; full-envelope applicability unresolved.'
        status='table-maximum-unspecified-supply';output=10;out_status='allocation-no-maximum'
        full=False;typical_output=None
        if name.startswith(('SN74AHC','SN74AHCT')) or name in ('CD74HCT04E','CD74HCT08E','CD74HCT32E','CD74HCT74E'):
            condition='Ci maximum at VCC=5 V; temperature columns include -40..85 C. No extrapolation over OC1 supply range.'
            status='table-maximum-at-5V'
        if name in ('SN74HCT245N','SN74HCT574N','SN74HC377N'):
            voltage='2..6 V' if name=='SN74HC377N' else '4.5..5.5 V'
            condition=f'Ci maximum at VCC={voltage}, -40..85 C; HCT245 applies only to DIR/OE, not A/B ports.' if name=='SN74HCT245N' else f'Ci maximum at VCC={voltage}, -40..85 C.'
            status='table-maximum-covers-OC1';full=True
        if stem in ('m27c1024','m27c322','w27c512','um61512a'):
            cap={'m27c1024':6,'m27c322':10,'w27c512':6,'um61512a':8}[stem]
            output=10 if stem=='um61512a' else 12
            condition='TA=25 C, f=1 MHz, input/output measured at 0 V; sampled, not 100% tested. Full-temperature maximum unknown.'
            if stem=='w27c512':condition='VCC=5 V, TA=25 C, f=1 MHz, VIN/VOUT=0 V. Full-envelope maximum unknown.'
            status=out_status='table-maximum-at-25C'
        if name=='SN74AHCT244N':typical_output=3
        limits=[dict(arc='data/clock/enable',load_pf=old.get(name,{}).get('timing_load_pf',50))]
        if name=='SN74HCT245N':limits=[dict(arc='data/enable',load_pf=150),dict(arc='disable',load_pf=50)]
        if name=='UM61512AK-15':limits=[dict(arc='read',load_pf=30),dict(arc='output-release',load_pf=5)]
        if name=='W27C512-45Z':limits=[dict(arc='high-speed read fixture',load_pf=30)]
        if name=='ACH-4.000MHZ-EK':
            cap=None;status='no-input';condition='ACH-4.000MHZ-EK: 4.5..5.5 V, E=-20..70 C, K=30 ppm; standard 15 pF load; 10 ns rise/fall maximum at 4 MHz.'
            limits=[dict(arc='oscillator-output',load_pf=15)]
        edge=None;edge_condition='Timing waveform condition not established by the selected excerpt; see full source before applying delay bounds.'
        if 'tr = 6 ns' in text or 'Input tr, tf = 6' in text:
            edge=6;edge_condition='Datasheet input tr/tf test condition, not measured board slew.'
        if 'tr = 3 ns' in text:edge=3;edge_condition='Datasheet input tr/tf test condition, not measured board slew.'
        if stem in ('m27c1024','m27c322'):edge=10;edge_condition='High-speed fixture <=10 ns; standard fixture <=20 ns. Do not mix load/threshold fixtures.'
        if stem=='w27c512':edge=5;edge_condition='High-speed fixture 5 ns, 30 pF; standard 10 ns, 100 pF. Prior selected model fixture retained separately.'
        recommended=None
        if name.startswith(('SN74AHC','SN74AHCT')) and name!='SN74AHCT244N':
            recommended=dict(maximum=20,unit='ns/V',supply='4.5..5.5 V')
        elif name=='CD74ACT175E':recommended=dict(maximum=10,unit='ns/V',supply='4.5..5.5 V')
        elif name in ('SN74HCT245N','SN74HCT574N'):recommended=dict(maximum=500,unit='ns',supply='4.5..5.5 V')
        if name.startswith('CD74HCT') or name=='SN74HC377N':
            recommended=dict(table_points='500 ns at 4.5 V; 400 ns at 5.5 V (HCT00/04/08/32/74), otherwise 6 V. No full-rail interpolation qualified.')
        rows[name]=dict(source='sources/'+stem+'.txt',source_sha256=digest(path),source_provenance=provenance[stem],evidence=evidence,
            input_pf=cap,input_status=status,input_conditions=condition,input_full_OC1=full,
            inactive_output_pf=output,inactive_output_status=out_status,inactive_output_full_OC1=False,
            output_typical_only_pf=typical_output,
            data_port_note='A/B ports: 10 pF allocation; Ci expressly excludes these ports.' if name=='SN74HCT245N' else None,
            output_note='20 pF Co row appears under HC types, not HCT types; not borrowed for CD74HCT244.' if name=='CD74HCT244E' else None,
            selected_fixtures=limits,fixture_scope='Earlier model/test loads, not absolute maximum loads or a delay guarantee below that load.',
            historical_default_fixture_pf=old.get(name,{}).get('timing_load_pf',50),
            timing_input_edge_ns=edge,timing_input_edge_condition=edge_condition,
            recommended_input_edge=recommended,
            selected_timing_review_point='Inherited IC screen: 4.5 V, -40..85 C for logic; memory/oscillator fixtures retain their source-specific conditions. This inventory supplies no new delay bounds.',
            physical_qualification=False)
    return rows

"""Record a bounded, pin-derived stock suitability review, without substitutions."""
from pathlib import Path
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.legacy import read_sheet,connectivity

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths={name:HERE.parent/'dip-logic/circuits'/name for name in
    ('Data-AL1.sch','Data-Fabric.sch','Data-CW1.sch','Backplane.sch')}
sheets={name:read_sheet(p) for name,p in paths.items()}
nets={name:connectivity(s) for name,s in sheets.items()}
pins={name:{(c['ref'],p['number']):dict(part=c['value'],name=p['name'],kind=p['kind'])
    for c in s['components'] for p in c['pins']} for name,s in sheets.items()}
def net(name,ref,pin):return next(n for n in nets[name] if [ref,str(pin)] in n['nodes'])
def driver(name,n):return [dict(reference=r,pin=p,**pins[name][r,p]) for r,p in n['nodes'] if pins[name][r,p]['kind'] in ('O','T')]
bp=sheets['Backplane.sch'];refs={c['value']:c['ref'] for c in bp['components']}
rows=[]
for ref in ('U6','U7'):
    for pin in ('1','3','4','7','8','11','13','14','17','18'):
        n=net('Data-AL1.sch',ref,pin);drivers=driver('Data-AL1.sch',n);route=[]
        if not drivers and n['labels']!=['GND']:
            connector,cp=next((r,p) for r,p in n['nodes'] if r.startswith('J'))
            link=net('Backplane.sch',refs['AL1_'+connector],cp)
            dest,dp=next((r,p) for r,p in link['nodes'] if r!=refs['AL1_'+connector])
            label=pins['Backplane.sch'][dest,dp]['part'];board,jack=label.split('_',1)
            source={'DF1':'Data-Fabric.sch','CW1':'Data-CW1.sch'}[board]
            upstream=net(source,jack,dp);drivers=driver(source,upstream)
            route=[dict(sheet='Backplane.sch',net=link),dict(sheet=source,net=upstream)]
        rows.append(dict(receiver=ref,pin=pin,net=n,drivers=drivers,route=route))
assert len(rows)==20
for row in rows:
    if row['net']['labels']==['GND']:continue
    expected='SN74AHCT00N' if row['pin']=='1' else 'SN74AHCT244N' if row['pin']=='11' or row['receiver']=='U6' else 'SN74HCT574N'
    assert len(row['drivers'])==1 and row['drivers'][0]['part']==expected,row
documents=[HERE/'sources'/f'{n}.txt' for n in ('sn74hc377','sn74hct00','sn74hct08','philips-74hct154')]
documents += [ROOT/'Verification/vendor'/p for p in ('clock/sn74ahct244.txt','controller/sn74ahct00.txt','controller/sn74hct574.txt')]
result=dict(scope='Static stock suitability review; no circuit substitution, timing promotion or full-supply/load qualification.',
    hc377=dict(part='SN74HC377N',datasheet='TI SCLS307D, pages 1, 3-6',
        inputs=rows,limits=dict(vcc_v=4.5,vih_min_v=3.15,vil_max_v=1.35,temperature_c=[-40,85],load_pf=50,
            clock_to_q_max_ns=40,setup_data_enable_ns=25,hold_data_enable_ns=5,clock_pulse_min_ns=25),
        finding='Data and clock reach AL1 U6/U7 through CMOS-output AHCT244 and HCT574 drivers; enable is driven by AHCT00. U7 unused data inputs are grounded. No direct EPROM-to-HC input in these paths.',
        dc_screen='At the shared 4.5 V datasheet point, AHCT244/AHCT00 VOH >=3.8 V at -8 mA and HCT574 VOH >=3.84 V at -6 mA exceed HC377 VIH 3.15 V. This is a bounded DC screen; supply extremes, output current/loading, receiver crossing, clock/data skew and timing remain unqualified.',
        disposition='Plausible reuse candidate, pending exact timing model and integrated loaded-signal checks; retain CD74HCT377E selection.'),
    gates=dict(parts=['SN74HCT00N','SN74HCT08N'],conditions='4.5 V, CL=50 pF, SN74 -40..85 C columns',
        max_delay_ns={'SN74HCT00N':25,'SN74HCT08N':30},reference_ahct_max_delay_ns=9,
        thresholds_v=dict(vih_min=2,vil_max=0.8),
        disposition='Same NAND/AND functions and DIP pin assignments, but HCT delay bounds cannot inherit AHCT timing. Recompute clock gating, pulse widths, setup/hold and reset paths before substitution. Slowing the oscillator alone does not prove hold/glitch behaviour.'),
    decoder=dict(part='74HCT154N',document='Philips 2004-10-12, ordering page and DIP24/SOT101-1 outline',
        disposition='Owned decoder option for four positions; historical DIP-24 documentation found. Manufacturer/logo and count still unknown. Retain CD74HCT154E selected identity until exact vendor/pin/timing review.'),
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [*paths.values(),*documents,ROOT/'Verification/controller-parts.json']})
(HERE/'logic-review.json').write_text(json.dumps(result,indent=2)+'\n')
print('Traced',len(rows),'HC377 input pins through native-equivalent DL1 sheets; static review only')

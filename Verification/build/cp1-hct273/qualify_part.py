"""Independent pin/identity/net comparison and HCT273 monitor qualification."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import shutil

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'candidate/Verification'))
from dm02.common import write_json,digest
from dm02.legacy import read_sheet,connectivity
from dm02.compact_hardware import Circuit


def main():
    before=HERE.parent/'compact-design/candidate/Circuits/KiCad/Compact/candidates'
    after=HERE/'candidate/Circuits/KiCad/Compact/candidates'
    changes=[]
    def nets(sheet):
        return sorted((sorted(map(tuple,n['nodes'])),sorted(n['labels'])) for n in connectivity(sheet))
    for source in sorted(before.glob('*.sch')):
        local=HERE/'candidate/Verification/build/part-baseline'/source.name
        local.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,local)
        assert digest(local)==digest(source)
        old,new=read_sheet(local),read_sheet(after/source.name)
        assert nets(old)==nets(new),source.name
        a={(c['ref'],c['unit']):c for c in old['components']}
        b={(c['ref'],c['unit']):c for c in new['components']}
        assert set(a)==set(b)
        for key,x in a.items():
            y=b[key]
            for field in ('lib_id','footprint','pins'):
                assert x[field]==y[field],(source.name,key,field)
            if x['value']!=y['value']:
                assert x['value']=='SN74HCT273N' and y['value']=='CD74HCT273E'
                changes.append(dict(board=source.stem,ref=key[0],old=x['value'],new=y['value']))
    assert {(x['board'],x['ref']) for x in changes}=={('AL1','U2'),('ME1','U11'),('ME1','U15')}
    # Datasheet SCHS174D pin-function table, transcribed independently of the generator.
    expected={'1':'~Mr','2':'Q0','3':'D0','4':'D1','5':'Q1','6':'Q2','7':'D2','8':'D3','9':'Q3','10':'GND',
              '11':'Cp','12':'Q4','13':'D4','14':'D5','15':'Q5','16':'Q6','17':'D6','18':'D7','19':'Q7','20':'VCC'}
    for x in changes:
        c=Circuit(x['board']);part=c.components[x['ref']][0]
        assert {p['number']:p['name'] for p in part['pins']}==expected
        assert part['footprint']=='Package_DIP:DIP-20_W7.62mm'
    folder=HERE/'hold-monitor';folder.mkdir(exist_ok=True)
    text=(HERE/'candidate/Verification/hdl/compact_devices.sv').read_text()
    start=text.index('module cp273 ');end=text.index('\nendmodule',start)+len('\nendmodule')
    (folder/'model.sv').write_text('`timescale 1ns/1ps\n'+text[start:end])
    (folder/'tb.sv').write_text('''`timescale 1ns/1ps
module tb;
 parameter real GAP=4,HOLD=3;
 reg [7:0] d=0;reg clk=0,clear_n=1;wire [7:0] q;
 cp273 #(42,HOLD) dut(d,clk,clear_n,q);
 initial begin #1;clear_n=0;#30;clear_n=1;#30;clk=1;#(GAP);d=1;#30;clk=0;#50;$display("DONE hold fixture");$finish;end
endmodule
''')
    runs=[]
    for gap,hold in ((2,3),(3,3),(4,3),(2,0)):
        args=['iverilog','-g2012','-s','tb','-P',f'tb.GAP={gap}','-P',f'tb.HOLD={hold}','-o','tb.vvp','model.sv','tb.sv']
        p=subprocess.run(args,cwd=folder,text=True,capture_output=True,timeout=30);assert p.returncode==0,p.stderr
        p=subprocess.run(['vvp','tb.vvp'],cwd=folder,text=True,capture_output=True,timeout=30)
        log=p.stdout+p.stderr;(folder/f'gap-{gap}-hold-{hold}.log').write_text(log)
        rejected=p.returncode!=0 and 'CP273 data hold' in log
        assert rejected==(gap<hold),log
        runs.append(dict(gap_ns=gap,hold_ns=hold,rejected=rejected,passed=True))
    loads=json.loads((HERE/'loads.json').read_text())
    outputs=[x for x in loads if any(d['part']=='CD74HCT273E' for d in x['drivers'])]
    assert len(outputs)==24 and all(x['allocated_load_pf']<=50 for x in outputs)
    receipt=dict(passed=True,revision='CP1-R2',changed_parts=changes,identical_connectivity_boards=12,
        pins_checked=60,package='PDIP-20, 7.62 mm row spacing',monitor_runs=runs,
        missing_hold_monitor_mutation_detected=runs[0]['rejected'] and not runs[3]['rejected'],
        outputs=outputs,load_scope='Allocated values only. AL1 includes unguaranteed HCT245 IO capacitance; external IO/routing remain unqualified.',
        datasheet_sha256=digest(HERE/'sources/cd74hct273.pdf'),physical_qualification=False)
    write_json(HERE/'part-qualification.json',receipt)
    print('Three part identities, 60 pins, 12 unchanged board netlists, 24 allocated output loads and hold-monitor boundaries checked')


if __name__=='__main__':main()

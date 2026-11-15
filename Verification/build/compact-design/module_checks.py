"""Standalone ALU and memory oracles on CP1 physical modules.

The fixture loops the module's source connector into its stimulus DATA bus.
BF1/DT1/BP1 are exercised separately by the integrated machine, not idealized
as part of this module test. Includes the memory's conflicting-command case.
"""
from pathlib import Path
import importlib.util,json,shutil,re
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,command,write_json,digest
from dm02.compact_hardware import Circuit,support_hdl
from dm02.alu import expected

def run(board,corner=1,quick=False):
    name='alu' if board=='AL1' else 'memory';top=name+'_hardware_tb'
    folder=BUILD/'compact'/f'{name}-module-c{corner}-quick{int(quick)}';folder.mkdir(parents=True,exist_ok=True)
    (folder/'module.sv').write_text(Circuit(board).hdl(corner));(folder/'clock.sv').write_text(Circuit('C1').hdl(corner))
    (folder/'support.sv').write_text((VROOT/'hdl/pc_devices.sv').read_text()+(VROOT/'hdl/controller_devices.sv').read_text()+support_hdl())
    if board=='AL1':
        shutil.copyfile(BUILD/'compact/fixtures/alu.bin',folder/'alu.bin')
        (folder/'vectors.hex').write_text(''.join(f'{(op<<32)|(a<<24)|(((a*73+op*19)&255)<<16)|expected(op,a,(a*73+op*19)&255):010x}\n' for op in range(32) for a in range(256)))
    else:(folder/'program.hex').write_text(''.join(f'{((a*37)^(a>>8)^0xa5)&255:02x}\n' for a in range(65536)))
    text=(VROOT/f'hdl/{name}_hardware_tb.sv').read_text()
    text=text.replace('reg osc=0,reset_n=1;initial #1 reset_n=0;',
        'reg osc=0,reset_request_n=1;wire reset_n,init_clk;initial #1 reset_request_n=0;')
    text=text.replace('always #62.5','always #125')
    text=text.replace("clock(osc,reset_n,1'b1,1'b0,phase,active,ready,state);",
        "clock(osc,reset_request_n,1'b1,1'b0,phase,active,ready,state,init_clk,reset_n);")
    text=re.sub(r'\breset_n\s*=', 'reset_request_n=',text)
    # The inherited 100 ns module inhibition check starts at the module RESET
    # pin, not at the newly inserted clock-board supervisor request input.
    text=text.replace('reset_request_n=0;#100;', 'reset_request_n=0;@(negedge reset_n);#100;')
    text=text.replace('operation,bus,a,flags,address,result);','operation,bus,a,flags,address,result,bus);')
    text=text.replace('io_input,io_data,io_address,io_strobe);','io_input,io_data,io_address,io_strobe,bus);')
    text=text.replace('@(posedge phase[2]);#200;','@(posedge phase[2]);#350;')
    text=text.replace('#50000000;','#100000000;').replace('#250000000;','#500000000;')
    (folder/'tb.sv').write_text(text)
    code,log=command(['iverilog','-g2012','-s',top,'-P',f'{top}.QUICK={int(quick)}','-o','module.vvp','module.sv','clock.sv','support.sv','tb.sv'],cwd=folder);assert code==0,log
    code,out=command(['vvp','module.vvp'],cwd=folder,timeout=1800);log+=out;(folder/'simulation.log').write_text(log)
    result=dict(board=board,corner=corner,quick=quick,passed=code==0 and ('DONE AL1' if board=='AL1' else 'DONE memory-io') in log,
        log=str((folder/'simulation.log').relative_to(HERE)),model_hashes={p.name:digest(p) for p in folder.glob('*.sv')},
        scope='Standalone physical module, fixture-looped SOURCE to DATA. Complete BF1/DT1 machine is a separate profile.')
    write_json(folder/'result.json',result);print(log,flush=True);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');a=p.parse_args()
    results=[]
    for board,corner,quick in [('AL1',1,False),('ME1',1,False),('AL1',4,True),('ME1',4,True)]:
        if a.resume and board=='AL1' and corner==1:
            folder=BUILD/'compact/alu-module-c1-quick0';x=json.loads((folder/'result.json').read_text());assert x['passed']
            assert digest(folder/'module.sv')==x['model_hashes']['module.sv']
            import hashlib
            assert hashlib.sha256(Circuit('AL1').hdl(1).encode()).hexdigest()==x['model_hashes']['module.sv']
        else:x=run(board,corner,quick)
        results.append(x)
        write_json(HERE/'module-check.json',dict(passed=all(x['passed'] for x in results),complete=len(results)==4,runs=results))
        assert x['passed']

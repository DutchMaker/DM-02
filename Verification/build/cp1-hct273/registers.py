"""Every byte and inter-register transfer on RG2, including synchronous zero init."""
from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,command,write_json,digest
from dm02.compact_hardware import Circuit,support_hdl

def run(corner=1,fault=None):
    folder=BUILD/'compact'/f'registers-c{corner}-{fault or "valid"}';folder.mkdir(parents=True,exist_ok=True)
    c=Circuit('RG1')
    if fault=='enable':c.nodes['U3','1']=c.labels['5V']
    text=c.hdl(corner)
    if fault=='init-clock':
        old=f'assign {c.n("J90",3)}=init_clk;';assert text.count(old)==1;text=text.replace(old,f'assign {c.n("J90",3)}=0;')
    (folder/'registers.sv').write_text(text);(folder/'clock.sv').write_text(Circuit('C1').hdl(corner))
    (folder/'fabric.sv').write_text(Circuit('BF1').hdl(corner))
    (folder/'support.sv').write_text((VROOT/'hdl/alu_devices.sv').read_text()+(VROOT/'hdl/controller_devices.sv').read_text()+support_hdl())
    t=(VROOT/'hdl/register_hardware_tb.sv').read_text().replace('reg osc=0,reset_n=1;initial #1 reset_n=0;',
        'reg osc=0,reset_request_n=1;wire reset_n,init_clk;initial #1 reset_request_n=0;')
    t=t.replace('always #62.5','always #125')
    t=t.replace('clock(osc,reset_n,1\'b1,1\'b0,phase,active,ready,state);',
        'clock(osc,reset_request_n,1\'b1,1\'b0,phase,active,ready,state,init_clk,reset_n);')
    t=t.replace('reset_n=1;','reset_request_n=1;').replace('reset_n=0;','reset_request_n=0;')
    t=t.replace('tri [7:0] bus;', 'tri [7:0] bus,source_bus;tri [31:0] branches;\n'
        'tran (branches[15:8],source_bus);\n'
        'compact_bus fabric(branches,{9\'h1ff,out_n,1\'b1},bus,reset_n);')
    # Vector tran is emitted bitwise for Icarus portability.
    t=t.replace('tran (branches[15:8],source_bus);','\n'.join(f'tran (branches[{8+i}],source_bus[{i}]);' for i in range(8)))
    t=t.replace('out_n,bus,registers);','out_n,bus,registers,init_clk,source_bus);')
    t=t.replace('@(posedge phase[2]);#200;','@(posedge phase[2]);#500;')
    t=t.replace('reset_request_n=0;#200;','reset_request_n=0;#750;')
    (folder/'tb.sv').write_text(t)
    code,log=command(['iverilog','-g2012','-s','register_hardware_tb','-o','registers.vvp','registers.sv','clock.sv','fabric.sv','support.sv','tb.sv'],cwd=folder)
    if code:raise RuntimeError(log)
    code,out=command(['vvp','registers.vvp'],cwd=folder,timeout=120);log+=out;(folder/'simulation.log').write_text(log)
    result=dict(corner=corner,fault=fault,passed=code!=0 and 'RG1 stored state' in log if fault else code==0 and 'DONE RG1' in log,
        log=str((folder/'simulation.log').relative_to(HERE)),model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print(log);return result
if __name__=='__main__':
    results=[run(c) for c in (0,1,5)]+[run(1,f) for f in ('enable','init-clock')]
    write_json(HERE/'register-check.json',dict(passed=all(x['passed'] for x in results),runs=results))
    assert all(x['passed'] for x in results)

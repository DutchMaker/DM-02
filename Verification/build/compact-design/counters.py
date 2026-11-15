"""Independent arithmetic/byte-load oracle for the physical HCT191 chain."""
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('compact_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,command,write_json,digest
from dm02.compact_hardware import Circuit,support_hdl

def run(corner=1,full=True,fault=False):
    folder=BUILD/'compact'/f'counter-c{corner}-full{int(full)}-fault{int(fault)}';folder.mkdir(parents=True,exist_ok=True)
    c=Circuit('SP1')
    if fault:c.nodes['U3','5']=c.labels['GND']
    (folder/'stack.sv').write_text(c.hdl(corner));(folder/'clock.sv').write_text(Circuit('C1').hdl(corner))
    (folder/'support.sv').write_text(support_hdl())
    (folder/'tb.sv').write_text((VROOT/'hdl/compact_counter_tb.sv').read_text())
    code,log=command(['iverilog','-g2012','-s','compact_counter_tb','-P',f'compact_counter_tb.FULL={int(full)}',
        '-o','counter.vvp','stack.sv','clock.sv','support.sv','tb.sv'],cwd=folder)
    if code:raise RuntimeError(log)
    code,out=command(['vvp','counter.vvp'],cwd=folder,timeout=600);log+=out;(folder/'simulation.log').write_text(log)
    result=dict(corner=corner,full=full,fault=fault,passed=(code!=0 and 'CP counter mismatch' in log) if fault else code==0 and 'DONE CP counter' in log,
        log=str((folder/'simulation.log').relative_to(HERE)),model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print(log);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--corner',type=int,default=1);p.add_argument('--quick',action='store_true');p.add_argument('--fault',action='store_true');a=p.parse_args()
    assert run(a.corner,not a.quick,a.fault)['passed']

"""Check the real-valued watchdog in Icarus before the long graphics replay."""
from pathlib import Path
import importlib.util,json,hashlib
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import command,write_json
def main():
    failed=HERE/'failed-runs/boot-watchdog-4s/simulation'
    coverage=json.loads((failed/'result.json').read_text())['coverage']
    budget=r.program_watchdog(coverage);assert budget['nominal_schedule_ns']==5680350000
    assert budget['watchdog_ns']==11361700000
    assert budget['watchdog_ns']>budget['nominal_schedule_ns']>4e9
    folder=HERE/'candidate/Verification/build/compact/program-budget-check';folder.mkdir(parents=True,exist_ok=True)
    (folder/'budget.sv').write_text('`timescale 1ns/1ps\nmodule budget_tb;\n'
        f'initial begin #({budget["watchdog_ns"]:.3f});'
        f'if($realtime!={budget["watchdog_ns"]:.3f}) $fatal(1,"Watchdog literal overflow");'
        '$display("DONE watchdog budget ns=%0.3f",$realtime);$finish;end\nendmodule\n')
    code,log=command(['iverilog','-g2012','-s','budget_tb','-o','budget.vvp','budget.sv'],cwd=folder);assert code==0,log
    code,out=command(['vvp','budget.vvp'],cwd=folder,timeout=30);log+=out
    assert code==0 and 'DONE watchdog budget ns=11361700000.000' in log,log
    (folder/'simulation.log').write_text(log)
    lines=(failed/'sram-power-on.hex').read_text().splitlines();assert len(lines)==131072
    decoded=bytes(int(x,16) for x in lines[:65536]);assert len(decoded)==65536
    result=dict(passed=True,budget=budget,simulator_log=log,decoded_sram_bytes=len(decoded),
        decoded_sram_sha256=hashlib.sha256(decoded).hexdigest(),circuit_changes=False,
        preserved_failure='failed-runs/boot-watchdog-4s/receipt.json')
    write_json(HERE/'program-budget-check.json',result);print(result)
if __name__=='__main__':main()

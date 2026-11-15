"""Demonstrate that HDL checks reject wrong drive pin, rate and phase wiring."""
from pathlib import Path
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'sandbox/Verification'))
from dm02.clock import Clock


def main():
    circuit=Clock();good=circuit.hdl(1)
    source=(HERE/'sandbox/Verification/hdl/clock_candidate_tb.sv').read_text()
    rows=[]
    for name in ('control','old-output-pin8','double-oscillator-rate','swapped-phase-pins'):
        folder=HERE/'hdl-faults'/name;folder.mkdir(parents=True,exist_ok=True)
        hdl,tb=good,source
        if name=='old-output-pin8':
            before=f'assign {circuit.n("Y1",5)}=osc;'
            assert hdl.count(before)==1
            hdl=hdl.replace(before,f'assign {circuit.n("Y1",8)}=osc;')
        elif name=='double-oscillator-rate':
            before='forever begin #(period*(1-duty)); osc=1; #(period*duty); osc=0; end'
            assert tb.count(before)==1
            tb=tb.replace(before,'forever begin #(period*(1-duty)/2); osc=1; #(period*duty/2); osc=0; end')
        elif name=='swapped-phase-pins':
            before='assign phase={'+','.join(circuit.n('J2',p) for p in (6,5,4,3))+'};'
            assert hdl.count(before)==1
            hdl=hdl.replace(before,'assign phase={'+','.join(circuit.n('J2',p) for p in (5,6,4,3))+'};')
        (folder/'clock.sv').write_text(hdl)
        (folder/'testbench.sv').write_text(tb)
        pilot=json.loads((HERE/'sandbox/Verification/requirements.json').read_text())['pilot']
        (folder/'parameters.vh').write_text('\n'.join(f'`define {k.upper()} {v}' for k,v in pilot.items())+'\n')
        compile=subprocess.run(['iverilog','-g2012','-s','clock_candidate_tb','-o','clock.vvp','clock.sv','testbench.sv'],cwd=folder,capture_output=True,text=True)
        assert compile.returncode==0,compile.stderr
        run=subprocess.run(['vvp','clock.vvp'],cwd=folder,capture_output=True,text=True,timeout=30)
        log=compile.stdout+compile.stderr+run.stdout+run.stderr
        (folder/'clock.log').write_text(log)
        passed=run.returncode==0 and 'DONE counted-clock' in log
        if name=='control':assert passed
        else:assert not passed and 'FATAL:' in log,(name,log)
        rows.append(dict(name=name,expected_pass=name=='control',passed=passed,exit=run.returncode,
            diagnostic=next((line for line in log.splitlines() if 'FATAL:' in line),'DONE counted-clock')))
    (HERE/'hdl-faults.json').write_text(json.dumps(dict(passed=True,results=rows),indent=2)+'\n')
    print('Control passes; three executable HDL faults rejected')


if __name__=='__main__':main()

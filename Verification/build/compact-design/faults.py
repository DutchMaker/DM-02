"""Negative controls must fail for the named device timing or bus reason."""
from pathlib import Path
import importlib.util,shutil
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,command,write_json,digest
from dm02.compact_hardware import support_hdl,Circuit

def device_faults():
    cases={
        'enable-low-clock':('ce=0;','CP191 enable changed with low clock'),
        'direction-low-clock':('down=1;','CP191 direction changed with low clock'),
        'load-short-pulse':('load=0;#5;load=1;','CP191 load pulse/data setup'),
        'load-data-setup':('load=0;#50;data=3;#5;load=1;','CP191 load pulse/data setup'),
        'load-data-hold':('load=0;#50;load=1;#1;data=3;','CP191 data hold'),
        'clock-pulse':('clk=1;#5;clk=0;','CP191 clock high pulse'),
        'load-recovery':('load=0;#50;load=1;#5;clk=1;','CP191 clock pulse/load recovery'),
        'count-setup':('clk=1;#50;ce=0;#5;clk=0;#25;down=1;#1;clk=1;','CP191 direction changed with low clock'),
    }
    results=[]
    for name,(stimulus,reason) in cases.items():
        folder=BUILD/'compact/faults'/name;folder.mkdir(parents=True,exist_ok=True)
        (folder/'devices.sv').write_text(support_hdl())
        tb='''`timescale 1ns/1ps
module fault_tb;
 reg [3:0] data=0;reg clk=0,load=0,ce=1,down=0,reset_n=0;
 wire [3:0] q;wire tc,rco;
 cp191 dut(data,clk,load,ce,down,q,tc,rco,reset_n);
 initial begin #100;load=1;#100;reset_n=1;#100;
 '''+stimulus+'''#100;$display("MISSED FAULT");$finish;end
endmodule
'''
        (folder/'tb.sv').write_text(tb)
        code,log=command(['iverilog','-g2012','-s','fault_tb','-o','fault.vvp','devices.sv','tb.sv'],cwd=folder);assert code==0,log
        code,out=command(['vvp','fault.vvp'],cwd=folder);log+=out;(folder/'simulation.log').write_text(log)
        results.append(dict(name=name,expected=reason,detected=code!=0 and reason in log,log=str((folder/'simulation.log').relative_to(HERE))))
    return results

def bus_fault():
    # Assemble from the CURRENT pin-derived model and fixture, then jam one
    # actual tri-state output enable active. Same-data overlaps must also fail.
    base=BUILD/'compact/c1-cases0';folder=BUILD/'compact/faults/bus-contention';folder.mkdir(parents=True,exist_ok=True)
    for p in base.iterdir():
        if p.suffix in ('.sv','.hex','.bin','.txt'):shutil.copyfile(p,folder/p.name)
    c=Circuit('AL1');c.nodes['U13','19']=c.labels['GND'];(folder/'AL1.sv').write_text(c.hdl(1))
    args=['iverilog','-g2012','-s','sequencer_tb','-o','fault.vvp']
    for key in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY'):args+=['-P',f'sequencer_tb.{key}=1']
    args += [p.name for p in folder.glob('*.sv')]
    code,log=command(args,cwd=folder);assert code==0,log
    code,out=command(['vvp','fault.vvp'],cwd=folder,timeout=60);log+=out;(folder/'simulation.log').write_text(log)
    return dict(name='bus-contention',detected=code!=0 and 'CP1 physical source contention' in log,log=str((folder/'simulation.log').relative_to(HERE)))

if __name__=='__main__':
    results=device_faults()+[bus_fault()]
    write_json(HERE/'fault-check.json',dict(passed=all(x['detected'] for x in results),results=results))
    print(results);assert all(x['detected'] for x in results)

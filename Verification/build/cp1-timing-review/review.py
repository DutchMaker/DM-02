"""Bounded CD74HCT273E substitution study; never modifies accepted CP1."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'compact-design/candidate/Verification/build/compact'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hold_monitor(text):
    old='  always @(d) ld=$realtime;'
    # Match the exact CP1 module, including its one-space indentation.
    old=old[1:]
    assert text.count(old)==1
    return text.replace(old,''' real minimum_data_hold=1.0e9;integer hold_events=0;
 always @(d) begin
   if(clear_n && lc>=0) begin
     if($realtime-lc<minimum_data_hold) minimum_data_hold=$realtime-lc;
     hold_events=hold_events+1;
     if($realtime-lc<3) $fatal(1,"CD273 data hold below 3 ns %m");
   end
   ld=$realtime;
 end
 final $display("CD273 hold %m events=%0d minimum_ns=%0.3f",hold_events,minimum_data_hold);''')


def execute(folder,args):
    start=time.monotonic()
    p=subprocess.run(args,cwd=folder,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
    return p.returncode,p.stdout,time.monotonic()-start


def unit():
    folder=HERE/'hold-monitor';folder.mkdir(exist_ok=True)
    original=(BASE/'c1-cases0/support.sv').read_text()
    model=original[original.index('module cp273 '):original.index('\nendmodule',original.index('module cp273 '))+len('\nendmodule')]
    (folder/'model.sv').write_text('`timescale 1ns/1ps\n'+hold_monitor(model))
    (folder/'tb.sv').write_text('''`timescale 1ns/1ps
module tb;
 parameter real GAP=4;
 reg [7:0] d=0;reg clk=0,clear_n=1;wire [7:0] q;
 cp273 dut(d,clk,clear_n,q);
 initial begin #1;clear_n=0;#30;clear_n=1;#30;clk=1;#(GAP);d=1;#30;clk=0;#50;$display("DONE hold fixture");$finish;end
endmodule
''')
    results=[]
    for gap in (2,3,4):
        code,log,_=execute(folder,['iverilog','-g2012','-s','tb','-P',f'tb.GAP={gap}','-o','tb.vvp','model.sv','tb.sv']);assert code==0,log
        code,out,wall=execute(folder,['vvp','tb.vvp']);log+=out
        (folder/f'gap-{gap}.log').write_text(log)
        passed=(code!=0 and 'CD273 data hold below 3 ns' in log) if gap<3 else code==0 and 'DONE hold fixture' in log
        assert passed,log
        results.append(dict(gap_ns=gap,expected='fault' if gap<3 else 'pass',detected=passed))
    return results


def profile(name,case_suite=False,standalone=False,quick=False):
    source=BASE/name;folder=HERE/name;folder.mkdir(exist_ok=True)
    hashes={}
    for p in source.iterdir():
        if p.suffix in ('.sv','.hex','.bin','.txt'):
            shutil.copyfile(p,folder/p.name);hashes[p.name]=sha(p)
    support=folder/'support.sv';support.write_text(hold_monitor(support.read_text()))
    top='memory_hardware_tb' if standalone else 'sequencer_tb'
    parameters=dict(QUICK=int(quick)) if standalone else dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,CASE_SUITE=int(case_suite),DEMO=0,OSC_DUTY=0.5,OSC_PPM=0)
    args=['iverilog','-g2012','-s',top,'-o','study.vvp']
    for k,v in parameters.items():args+=['-P',f'{top}.{k}={v}']
    args += [p.name for p in sorted(folder.glob('*.sv'))]
    code,log,_=execute(folder,args);assert code==0,log
    code,out,wall=execute(folder,['vvp','study.vvp']);log+=out;(folder/'simulation.log').write_text(log)
    marker='DONE memory-io' if standalone else 'DONE fetched-opcodes' if case_suite else 'DONE sequencer'
    return dict(profile=name,passed=code==0 and marker in log,exit_code=code,wall_seconds=wall,
                hold_fault='CD273 data hold below 3 ns' in log,
                observed_hold_lines=[line for line in log.splitlines() if line.startswith('CD273 hold')],
                input_hashes=hashes,modified_support_sha256=sha(support),log=str((folder/'simulation.log').relative_to(HERE)))


def main():
    unit_results=unit()
    if '--memory-only' in sys.argv:
        old=HERE/'results.json';previous=json.loads(old.read_text());runs=previous['runs']
        assert len(runs)==6 and all(x['passed'] for x in runs)
        for x in runs:
            assert all(sha(BASE/x['profile']/n)==h for n,h in x['input_hashes'].items())
            assert sha(HERE/x['profile']/'support.sv')==x['modified_support_sha256']
        shutil.copyfile(old,HERE/'six-profile-results.json')
    else:
        runs=[profile(name,cases) for name,cases in [('c0-cases0',False),('c1-cases0',False),('c7-cases0',False),('c0-cases1',True),('c1-cases1',True),('c7-cases1',True)]]
    runs += [profile('memory-module-c1-quick0',standalone=True),profile('memory-module-c4-quick1',standalone=True,quick=True)]
    result=dict(completed=True,adopted=False,part='CD74HCT273E',unit_checks=unit_results,runs=runs,
                all_sampled_profiles_passed=all(x['passed'] for x in runs),
                scope='Six CPU and two standalone memory/IO profiles with an added 3 ns data-hold monitor. The CPU profiles alone do not capture IO; standalone profiles exercise both IO registers. Original 42 ns propagation, 25 ns setup/recovery/clock pulse and 20 ns clear pulse retained as conservative bounds at 4.5 V, -40..85 C, 50 pF. This study does not establish minimum silicon delays, physical loading, all profiles, or full boot qualification.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2))
    for x in runs:print(x['profile'],x['passed'],x['observed_hold_lines'])


if __name__=='__main__':main()

"""MD1 affected memory and ROM/text replay, with native-pin-derived buffer arcs."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import re
import shutil
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import mar_distribution as md,text_boot_evidence,text_boot,io_cpu

require=md.require
SOURCES=['Verification/dm02/mar_distribution.py','Verification/dm02/mar_distribution_sim.py',
    'Verification/hdl/text_cells.sv','Verification/text-boot-evidence.json','Verification/targets/cp1/lock.json']


def delays(bindings,profile=1):
    require(profile in (0,1,2,3),'Unknown MD1 delay profile')
    return {r['bit']:(0 if profile==0 else 9.5 if profile==1 else
        9.5 if (r['bit']%2)==profile-2 else 0) for r in bindings}


def memory_model(original,bindings,profile=1):
    """Only the sixteen ME1 address input arcs change; all device models remain."""
    matches=list(re.finditer(r'assign n\[(\d+)\]=address\[(\d+)\];',original))
    require(len(matches)==16 and {int(m[2]) for m in matches}==set(range(16)),'ME1 address binding changed')
    by_bit={r['bit']:r for r in bindings};delay=delays(bindings,profile)
    def replace(m):
        bit=int(m[2]);r=by_bit[bit];expr=f'address[{r["source_bit"]}]' if r['enabled'] else "1'bz"
        return f'assign #({delay[bit]}) n[{m[1]}]={expr}; // MD1 {r["reference"]}.{r["input_pin"]}->{r["output_pin"]}'
    return re.sub(r'assign n\[(\d+)\]=address\[(\d+)\];',replace,original)


def collect(folder,prefix,lock,names):
    hashes={}
    for name in names:
        key=prefix+name;source=BUILD/key
        require(key in lock['artifacts'] and digest(source)==lock['artifacts'][key],'Changed MD1 replay input: '+key)
        hashes[key]=digest(source);shutil.copyfile(source,folder/name)
    return hashes


def exhaustive(folder,bindings,profile=1):
    folder=Path(folder);require(not folder.exists(),'Preserve MD1 exhaustive run');folder.mkdir(parents=True)
    delay=delays(bindings,profile)
    lines=['`timescale 1ns/1ps','module tb;reg [15:0] address;wire [15:0] result;integer i;']
    for row in bindings:
        expr=f'address[{row["source_bit"]}]' if row['enabled'] else "1'bz"
        lines.append(f'assign #({delay[row["bit"]]}) result[{row["bit"]}]={expr};')
    lines+=['initial begin for(i=0;i<65536;i=i+1)begin address=i;#20;',
        'if(result!==address)$fatal(1,"MD1 address mapping got=%h expected=%h",result,address);end',
        '$display("PASS MD1 all 65536 address words");$finish;end endmodule']
    (folder/'tb.sv').write_text('\n'.join(lines)+'\n')
    code,log=command(['iverilog','-g2012','-s','tb','-o','test.vvp','tb.sv'],cwd=folder)
    (folder/'compile.log').write_text(log);require(code==0,'MD1 exhaustive compile failed')
    code,log=command(['vvp','test.vvp'],cwd=folder,timeout=60);(folder/'simulation.log').write_text(log)
    result=dict(passed=code==0 and 'PASS MD1 all 65536 address words' in log,exit_code=code,profile=profile,
        bindings=bindings,physical_qualification=False)
    write_json(folder/'result.json',result);return result


def boot(folder,bindings,case='guarded-max',profile=1):
    folder=Path(folder);require(not folder.exists(),'Preserve MD1 boot');folder.mkdir(parents=True)
    lock=json.loads(text_boot_evidence.LOCK.read_text());prefix='cp1-text-boot/'+case+'/'
    names=[b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv','tb.sv','alu.bin','control.hex',
        'boot-rom.hex','sram-power-on.hex','payload.hex','serial-expected.hex']
    inputs=collect(folder,prefix,lock,names)
    original=(folder/'ME1.sv').read_text();(folder/'ME1.sv').write_text(memory_model(original,bindings,profile))
    args=['iverilog','-g2012','-s','sequencer_tb','-o','boot.vvp']
    for p in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY'):args+=['-P',f'sequencer_tb.{p}=1']
    args += [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv',VROOT/'hdl/text_cells.sv','tb.sv']
    code,log=command(args,cwd=folder);(folder/'compile.log').write_text(log);require(code==0,'MD1 boot compile failed: '+log)
    code,log=command(['vvp','boot.vvp'],cwd=folder,timeout=600);(folder/'simulation.log').write_text(log)
    violations=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
    match=re.search(r'PASS TX1 CPU received=(\d+) reads=(\d+) setup_ns=([\d.]+) hold_ns=([\d.]+)',log)
    passed=code==0 and 'PASS TB1 ROM reconstruction' in log and bool(match) and violations==0
    result=dict(passed=passed,exit_code=code,case=case,buffer_profile=profile,input_hashes=inputs,
        bindings=bindings,timing_violations=violations,physical_qualification=False,
        source_hashes={p:digest(ROOT/p) for p in SOURCES},
        cpu_io_setup_ns=float(match[3]) if match else None,cpu_io_hold_ns=float(match[4]) if match else None,
        rom_only_startup=True,host_boot_injected=False,
        model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print(folder.name,passed,log[-500:],flush=True);return result


def memory(folder,bindings):
    folder=Path(folder);require(not folder.exists(),'Preserve MD1 memory run');folder.mkdir(parents=True)
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text())
    prefix='cp1-hct273/candidate/Verification/build/compact/memory-module-c1-quick0/'
    inputs=collect(folder,prefix,lock,['module.sv','clock.sv','support.sv','tb.sv','program.hex'])
    (folder/'module.sv').write_text(memory_model((folder/'module.sv').read_text(),bindings))
    code,log=command(['iverilog','-g2012','-s','memory_hardware_tb','-P','memory_hardware_tb.QUICK=0',
        '-o','memory.vvp','module.sv','clock.sv','support.sv','tb.sv'],cwd=folder)
    (folder/'compile.log').write_text(log);require(code==0,'MD1 memory compile failed: '+log)
    code,log=command(['vvp','memory.vvp'],cwd=folder,timeout=1800);(folder/'simulation.log').write_text(log)
    result=dict(passed=code==0 and 'DONE memory-io' in log,exit_code=code,input_hashes=inputs,
        bindings=bindings,physical_qualification=False,quick=False,buffer_delay_ns=9.5,
        source_hashes={p:digest(ROOT/p) for p in SOURCES},model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print('memory',result['passed'],log[-500:],flush=True);return result


def run(folder):
    folder=Path(folder);require(not folder.exists(),'Preserve MD1 simulation matrix');folder.mkdir(parents=True)
    text_boot_evidence.load();candidate=md.Candidate();bindings=candidate.bindings(md.STUDY/'final/native/MD1.xml')
    exact=exhaustive(folder/'all-addresses',bindings)
    faults={f:exhaustive(folder/f,candidate.bindings(md.STUDY/'final'/f/'MD1.xml')) for f in ('swapped-address','disabled-buffer')}
    require(exact['passed'] and all(not r['passed'] for r in faults.values()),'MD1 exhaustive address fault failure')
    jobs=[('boot-'+case,case,profile) for case,profile in [('guarded-max',1),('zero',0),('mixed2',2),('mixed3',3)]]
    jobs+=[('boot-swapped','guarded-max',1),('memory',None,None)]
    def once(job):
        name,case,profile=job
        if name=='memory':return name,memory(folder/name,bindings)
        arcs=candidate.bindings(md.STUDY/'final/swapped-address/MD1.xml') if name=='boot-swapped' else bindings
        return name,boot(folder/name,arcs,case,profile)
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(once,jobs))
    write_json(folder/'matrix.json',dict(revision='CP1-MD1',results=results,exhaustive=exact,mutations=faults,
        physical_qualification=False,source_hashes={p:digest(ROOT/p) for p in SOURCES}))
    require(all(r['passed']==(name!='boot-swapped') for name,r in results.items()),'Unexpected MD1 simulation result')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)

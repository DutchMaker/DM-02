"""HB1: separate two-HCT244 candidate; MD1 source and locks stay immutable."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
from .common import BUILD, ROOT, VROOT, command, digest, write_json
from . import mar_distribution as md, mar_distribution_sim as ms, mar_distribution_evidence as mde
from . import text_boot_evidence, io_cpu

STUDY=BUILD/'cp1-hct-buffers'
CANONICAL=ROOT/'Circuits/KiCad/Integrated/candidates/HB1'
PART='SN74HCT244N'
REFERENCES=('U17001','U17002')
require=md.require


class Candidate(md.Candidate):
    def __init__(self):
        super().__init__()
        for ref in REFERENCES:self.components[ref]['value']=PART

    def documents(self,fault=None):
        # Inherit MD1 topology generation, but only replace the two MB1 values.
        docs=super().documents(fault)
        docs['MB1.kicad_sch']=docs['MB1.kicad_sch'].replace('SN74AHCT244N',PART)
        return {name.replace('MD1.kicad_sch','HB1.kicad_sch'):text.replace('MD1','HB1') for name,text in docs.items()}

    def generate(self,folder,fault=None):
        folder=Path(folder);require(not folder.exists(),'Preserve HB1 attempt');folder.mkdir(parents=True)
        for name,text in self.documents(fault).items():(folder/name).write_text(text)
        code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',folder/'HB1.xml',folder/'HB1.kicad_sch'])
        (folder/'export.log').write_text(log);require(code==0,'HB1 native export failed: '+log)
        result=self.compare(folder/'HB1.xml');write_json(folder/'comparison.json',result);return result


def loads(candidate,path):
    """Rebuild native loads with the replacement's explicit Ci condition."""
    class Inventory(md.LoadInventory):
        def classify(self,p):
            if p['part']==PART:
                # MD1 initialization has constructed self.parts before classifying.
                self.parts[PART]=dict(input_pf=10,input_status='SCLS175I section5.6:4.5..5.5V/-55..125C table maximum',
                    input_full_OC1=True,inactive_output_pf=10,inactive_output_status='allocation-no-output-maximum',
                    inactive_output_full_OC1=False,selected_fixtures=[dict(arc='data/enable/disable',load_pf=50)])
            super().classify(p)
    result=Inventory(candidate,path).audit(candidate);result['revision']='CP1-HB1'
    return result


def delays(bindings,profile):
    require(profile in (0,1,2,3),'Unknown HB1 delay profile')
    require(len(bindings)==16 and {r['bit'] for r in bindings}==set(range(16)),'Incomplete HB1 address arcs')
    return {r['bit']:(0 if profile==0 else 42 if profile==1 or r['bit']%2==profile-2 else 0) for r in bindings}


def memory_model(original,bindings,profile):
    matches=list(re.finditer(r'assign n\[(\d+)\]=address\[(\d+)\];',original))
    require(len(matches)==16 and {int(m[2]) for m in matches}==set(range(16)),'ME1 address binding changed')
    by_bit={r['bit']:r for r in bindings};delay=delays(bindings,profile)
    def replace(m):
        bit=int(m[2]);r=by_bit[bit];expr=f'address[{r["source_bit"]}]' if r['enabled'] else "1'bz"
        return f'assign #({delay[bit]}) n[{m[1]}]={expr}; // HB1 {r["reference"]}.{r["input_pin"]}->{r["output_pin"]}'
    return re.sub(r'assign n\[(\d+)\]=address\[(\d+)\];',replace,original)


def mapping_source(bindings,profile=1):
    delay=delays(bindings,profile)
    lines=['`timescale 1ns/1ps','module tb;reg [15:0] address;wire [15:0] result;integer i;']
    for r in bindings:
        expr=f'address[{r["source_bit"]}]' if r['enabled'] else "1'bz"
        lines.append(f'assign #({delay[r["bit"]]}) result[{r["bit"]}]={expr};')
    lines+=['initial begin for(i=0;i<65536;i=i+1)begin address=i;#50;',
        'if(result!==address)$fatal(1,"HB1 address mapping got=%h expected=%h",result,address);end',
        '$display("PASS HB1 all 65536 address words");$finish;end endmodule']
    return '\n'.join(lines)+'\n'


def exhaustive(folder,bindings,profile=1):
    folder=Path(folder);require(not folder.exists(),'Preserve HB1 mapping run');folder.mkdir(parents=True)
    (folder/'tb.sv').write_text(mapping_source(bindings,profile))
    code,log=command(['iverilog','-g2012','-s','tb','-o','test.vvp','tb.sv'],cwd=folder)
    (folder/'compile.log').write_text(log);require(code==0,'HB1 mapping compile failed')
    code,log=command(['vvp','test.vvp'],cwd=folder,timeout=60);(folder/'simulation.log').write_text(log)
    result=dict(passed=code==0 and 'PASS HB1 all 65536 address words' in log,exit_code=code,profile=profile,
        bindings=bindings,physical_qualification=False)
    write_json(folder/'result.json',result);return result


def simulate(folder,bindings,case='guarded-max',profile=1,memory=False):
    folder=Path(folder);require(not folder.exists(),'Preserve HB1 simulation');folder.mkdir(parents=True)
    if memory:
        lock=json.loads((VROOT/'targets/cp1/lock.json').read_text())
        prefix='cp1-hct273/candidate/Verification/build/compact/memory-module-c1-quick0/'
        names=['module.sv','clock.sv','support.sv','tb.sv','program.hex'];model='module.sv'
        args=['iverilog','-g2012','-s','memory_hardware_tb','-P','memory_hardware_tb.QUICK=0',
              '-o','test.vvp','module.sv','clock.sv','support.sv','tb.sv']
    else:
        lock=json.loads(text_boot_evidence.LOCK.read_text());prefix='cp1-text-boot/'+case+'/'
        names=[b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv','tb.sv','alu.bin','control.hex',
            'boot-rom.hex','sram-power-on.hex','payload.hex','serial-expected.hex'];model='ME1.sv'
        args=['iverilog','-g2012','-s','sequencer_tb','-o','test.vvp']
        for p in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY'):args+=['-P',f'sequencer_tb.{p}=1']
        args += [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv',VROOT/'hdl/text_cells.sv','tb.sv']
    inputs=ms.collect(folder,prefix,lock,names)
    (folder/model).write_text(memory_model((folder/model).read_text(),bindings,profile))
    code,log=command(args,cwd=folder);(folder/'compile.log').write_text(log);require(code==0,'HB1 compile failed: '+log)
    code,log=command(['vvp','test.vvp'],cwd=folder,timeout=1800 if memory else 600)
    (folder/'simulation.log').write_text(log)
    violations=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
    match=re.search(r'PASS TX1 CPU received=(\d+) reads=(\d+) setup_ns=([\d.]+) hold_ns=([\d.]+)',log)
    passed=code==0 and (('DONE memory-io' in log) if memory else ('PASS TB1 ROM reconstruction' in log and bool(match) and violations==0))
    result=dict(passed=bool(passed),exit_code=code,case=case,profile=profile,input_hashes=inputs,bindings=bindings,
        timing_violations=violations,physical_qualification=False,quick=False if memory else None,
        cpu_io_setup_ns=float(match[3]) if match else None,cpu_io_hold_ns=float(match[4]) if match else None,
        rom_only_startup=not memory,buffer_delays_ns=delays(bindings,profile),
        model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print(folder.name,passed,log[-500:],flush=True);return result


def run(folder):
    mde.load();folder=Path(folder);require(not folder.exists(),'Preserve HB1 study');folder.mkdir(parents=True)
    candidate=Candidate();native=candidate.generate(folder/'native');require(native['passed'],'HB1 native check failed')
    mutations={f:candidate.generate(folder/f,f) for f in md.FAULTS}
    require(all(not r['passed'] for r in mutations.values()),'Undetected HB1 native fault')
    bindings=candidate.bindings(folder/'native/HB1.xml');write_json(folder/'bindings.json',bindings)
    write_json(folder/'loads.json',loads(candidate,folder/'native/HB1.xml'))
    mapping={str(p):exhaustive(folder/f'all-addresses-{p}',bindings,p) for p in range(4)}
    faults={f:exhaustive(folder/('mapping-'+f),candidate.bindings(folder/f/'HB1.xml')) for f in ('swapped-address','disabled-buffer')}
    jobs=[('boot-'+case,case,p) for case,p in [('guarded-max',1),('zero',0),('mixed2',2),('mixed3',3)]]
    jobs+=[('boot-swapped','guarded-max',1),('memory','guarded-max',1)]
    def once(job):
        name,case,p=job
        arcs=candidate.bindings(folder/'swapped-address/HB1.xml') if name=='boot-swapped' else bindings
        return name,simulate(folder/name,arcs,case,p,memory=name=='memory')
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(once,jobs))
    summary=dict(revision='CP1-HB1',native=native,native_faults=mutations,mapping=mapping,mapping_faults=faults,
        results=results,physical_qualification=False,promoted_into_R2=False,
        delay_scope='0/42ns and alternating0/42ns sampled digital sensitivity. Zero is a stress bound, not manufacturer minimum; no loaded slew, population guarantee or physical hold qualification.')
    write_json(folder/'summary.json',summary)
    require(all(r['passed'] for r in mapping.values()) and all(not r['passed'] for r in faults.values()),'HB1 mapping results failed')
    require(all(r['passed']==(name!='boot-swapped') for name,r in results.items()),'HB1 simulation results failed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)

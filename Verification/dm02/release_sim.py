"""RR1 short native-control experiments and instrumented, pinned MD1 boot."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
import json
from pathlib import Path
import re
import shutil
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import release_requirements as rr,mar_distribution_evidence as mde,io_cpu

require=rr.require
SOURCES=['Verification/dm02/release_requirements.py','Verification/dm02/release_sim.py',
         'Verification/hdl/release_watch.sv','Verification/hdl/text_cells.sv',
         'Verification/operating-contract.json','Verification/mar-distribution-evidence.json']
CASES={
    'max-blank100':dict(profile='max',blank=100),
    'zero-blank100':dict(profile='zero',blank=100),
    'read-slow-blank100':dict(profile='read-slow',blank=100),
    'write-slow-blank100':dict(profile='write-slow',blank=100),
    'read-slow-no-blank':dict(profile='read-slow',blank=0,expected='RR1 drive overlap'),
    'write-slow-no-blank':dict(profile='write-slow',blank=0,reverse=True,expected='RR1 drive overlap'),
    'same-data-overlap':dict(profile='read-slow',blank=0,same=True,expected='RR1 drive overlap'),
    'late-sram-release':dict(profile='max',blank=100,release=200,expected='RR1 drive overlap'),
    'early-read-capture':dict(profile='max',blank=100,early=True,expected='RR1 invalid read capture'),
}


def event_summary(path):
    rows=list(csv.DictReader(Path(path).read_text().splitlines()));last_off={'ram':None,'writer':None}
    previous={'ram':False,'writer':False};gaps={'read_to_write':[],'write_to_read':[]}
    counts={'ram':0,'writer':0};writes=0;last_we='1'
    reset_edges=0;last_reset=None
    # Keep every timestamp; delta-cycle control hazards must remain observable.
    for row in rows:
        if any(row[k] not in ('0','1') for k in ('reset_n','ram_oe_n','ram_we_n','writer_oe_n')):continue
        t=float(row['time_ns']);state={'ram':row['ram_oe_n']=='0' and row['ram_we_n']=='1',
                                     'writer':row['writer_oe_n']=='0'}
        if row['reset_n']=='0' and last_reset=='1':reset_edges+=1
        last_reset=row['reset_n']
        if row['ram_we_n']=='0' and last_we=='1':writes+=1
        last_we=row['ram_we_n']
        for name in state:
            if previous[name] and not state[name]:last_off[name]=t
        for name,other,direction in [('ram','writer','write_to_read'),('writer','ram','read_to_write')]:
            if state[name] and not previous[name]:
                counts[name]+=1
                if last_off[other] is not None:gaps[direction].append(t-last_off[other])
        previous=state
    return dict(event_rows=len(rows),activations=counts,write_pulses=writes,reset_assertions=reset_edges,
        handovers={k:dict(count=len(v),minimum_requested_gap_ns=min(v) if v else None) for k,v in gaps.items()},
        scope='Sampled control-pin gaps before independent zero-enable/release envelopes; no physical timing guarantee.')


def fixture(graph,case):
    blank=case['blank'];release=case.get('release',10)
    data="8'hA5" if case.get('same') else "8'h5A"
    early=1 if case.get('early') else 150
    # Explicit stable address 4000; no physical load model is inferred from this fixture.
    ports=['read_n','write_n','reset_n','ph2','ph3']+["1'b"+str(int(i==14)) for i in range(8,16)]+['roe','we','woe']
    start='write_n=0;' if case.get('reverse') else 'read_n=0;'
    order=('write_n=1;','read_n=0;') if case.get('reverse') else ('read_n=1;','write_n=0;')
    return f'''`timescale 1ns/1ps
module tb;
 reg read_n=1,write_n=1,reset_n=0,ph2=0,ph3=0;
 wire roe,we,woe;tri [7:0] dq;
 release_controls control({','.join(ports)});
 release_watch #({release},13) watch(reset_n,read_n,write_n,roe,we,woe,1'b1);
 wire ram_active,writer_active;
 assign #(0,{release}) ram_active=!roe && we;
 assign #(0,13) writer_active=!woe;
 // Functional read-valid delay is separate from low-Z activation.
 wire [7:0] read_value;
 assign #(15) read_value=(!roe && we)?8'hA5:8'bx;
 assign dq=ram_active?read_value:8'bz;
 assign dq=writer_active?{data}:8'bz;
 initial begin
  #100;reset_n=1;#100;{start}#200;
  {order[0]}#{blank};{order[1]}#200;
  read_n=1;write_n=1;#200;
  read_n=0;#{early};
  if(dq!==8'hA5)$fatal(1,"RR1 invalid read capture");
  #100;read_n=1;#{blank};write_n=0;#150;ph2=1;#100;
  if(we!==0 || dq!=={data})$fatal(1,"RR1 invalid write capture");
  ph2=0;#100;write_n=1;#200;
  // Reset during active read, then active write: abort has no data-retention promise.
  read_n=0;#200;reset_n=0;#200;
  if(roe!==1 || woe!==1 || we!==1)$fatal(1,"RR1 reset inhibition");
  read_n=1;reset_n=1;#200;write_n=0;#200;ph2=1;#100;reset_n=0;#200;
  if(roe!==1 || woe!==1 || we!==1)$fatal(1,"RR1 write reset inhibition");
  $display("PASS RR1 read/write/capture/reset fixture");$finish;
 end
endmodule
'''


def finish(folder,code,log,expected,inputs,model_files):
    (folder/'simulation.log').write_text(log)
    success=code==0 and expected in log if expected.startswith('PASS') else code!=0 and expected in log
    result=dict(expectation_met=success,exit_code=code,expected=expected,
        events=event_summary(folder/'release-events.csv'),input_hashes=inputs,
        model_hashes={n:digest(folder/n) for n in model_files},
        source_hashes={n:digest(ROOT/n) for n in SOURCES},physical_qualification=False)
    write_json(folder/'result.json',result);return result


def short(folder,graph,case):
    folder=Path(folder);require(not folder.exists(),'Preserve RR1 short run');folder.mkdir(parents=True)
    (folder/'controls.sv').write_text(graph.hdl(case['profile']));(folder/'tb.sv').write_text(fixture(graph,case))
    shutil.copyfile(VROOT/'hdl/release_watch.sv',folder/'release_watch.sv')
    names=['controls.sv','release_watch.sv','tb.sv']
    code,log=command(['iverilog','-g2012','-s','tb','-o','test.vvp',*names],cwd=folder)
    (folder/'compile.log').write_text(log);require(code==0,'RR1 compile: '+log)
    code,log=command(['vvp','test.vvp'],cwd=folder)
    return finish(folder,code,log,case.get('expected','PASS RR1'),{},names)


def boot_probe(release=10):
    return f'''
 release_watch #({release},13) rr_watch(ME1_RESET_n,mem_n,load_n[10],
     physical_memory.memory.n[132],physical_memory.memory.n[133],physical_memory.memory.n[140],fabric.n[69]);
'''


def boot(folder,case='guarded-max',release=10,retain_data=False):
    folder=Path(folder);require(not folder.exists(),'Preserve RR1 boot');folder.mkdir(parents=True)
    lock=json.loads(mde.LOCK.read_text());prefix='cp1-mar-distribution/simulation-1/boot-'+case+'/'
    names=[b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv','tb.sv','alu.bin','control.hex',
        'boot-rom.hex','sram-power-on.hex','payload.hex','serial-expected.hex']
    inputs={}
    for name in names:
        key=prefix+name;require(key in lock['artifacts'] and digest(BUILD/key)==lock['artifacts'][key],'Changed MD1 boot input')
        inputs[key]=digest(BUILD/key);shutil.copyfile(BUILD/key,folder/name)
    tb=(folder/'tb.sv').read_text();require(tb.count('module sequencer_tb;')==1,'RR1 top binding changed')
    require(tb.count('endmodule')==1,'RR1 top module boundary changed')
    tb=tb.replace('endmodule',boot_probe(release)+'\nendmodule')
    (folder/'tb.sv').write_text(tb)
    bf=(folder/'BF1.sv').read_text()
    if retain_data:
        # Sensitivity only: permanently enabled final stage. Internal trunk is unchanged.
        bf,n=re.subn(r'(bufif0 #\([^\n]+\) U105_\d+ \([^\n]+),n\[69\]\);',r"\1,1'b0);",bf)
        require(n==8,'RR1 U105 mapping changed')
        bf,n=re.subn(r'(wire cp_active_U105;assign #\([^\n]+\) cp_active_U105=)~n\[69\];',r"\g<1>1'b1;",bf)
        require(n==1,'RR1 U105 activity mapping changed');(folder/'BF1.sv').write_text(bf)
    shutil.copyfile(VROOT/'hdl/release_watch.sv',folder/'release_watch.sv')
    models=[b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv','release_watch.sv','tb.sv']
    args=['iverilog','-g2012','-s','sequencer_tb','-o','boot.vvp']
    for p in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY'):args+=['-P',f'sequencer_tb.{p}=1']
    code,log=command(args+models+[VROOT/'hdl/text_cells.sv'],cwd=folder)
    (folder/'compile.log').write_text(log);require(code==0,'RR1 boot compile: '+log)
    code,log=command(['vvp','boot.vvp'],cwd=folder,timeout=600)
    expected='RR1 drive overlap' if release>1000 else 'PASS TX1 CPU received=5'
    result=finish(folder,code,log,expected,inputs,models)
    if expected.startswith('PASS'):
        require('PASS TB1 ROM reconstruction' in log and not sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log))),'RR1 boot oracle/timing failure')
    print(folder.name,result['expectation_met'],result['events']['handovers'],flush=True)
    return result


def run(folder):
    folder=Path(folder);require(not folder.exists(),'Preserve RR1 iteration');folder.mkdir(parents=True)
    mde.load();graph=rr.Graph();write_json(folder/'audit.json',graph.audit())
    write_json(folder/'native-faults.json',rr.mutations(graph.inventory))
    short_results={name:short(folder/name,graph,case) for name,case in CASES.items()}
    write_json(folder/'short-matrix.json',short_results)
    require(all(r['expectation_met'] for r in short_results.values()),'Unexpected RR1 short result')
    jobs=[('boot-'+case,dict(case=case)) for case in ('guarded-max','zero','mixed2','mixed3')]
    jobs += [('boot-DATA-always-driven',dict(retain_data=True)),('boot-late-release',dict(release=5000))]
    def once(job):return job[0],boot(folder/job[0],**job[1])
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(once,jobs))
    write_json(folder/'boot-matrix.json',results)
    require(all(r['expectation_met'] for r in results.values()),'Unexpected RR1 boot result')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)

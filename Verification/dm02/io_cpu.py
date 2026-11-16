"""Compose pinned R2 CPU HDL and BR1 for a fetched, SRAM-preloaded IO diagnostic."""
import argparse
import json
from pathlib import Path
import re
import shutil
import time
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import io_bridge,io_bridge_evidence

BOARDS=('C1','CW1','SQ1','PC1','AL1','RG1','SP1','MA1','ME1','BF1','DT1')
STUDY=BUILD/'cp1-io-cpu'


def require(condition,message):
    if not condition:raise ValueError(message)


def diagnostic(present=0):
    # Literal instruction encoding, independently cross-checked against source.
    from .microcode import reference
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
    for opcode,name in ((0x17,'MOV A,value'),(0x1e,'MOV A,address'),(0x23,'MOV address,A'),(0xe2,'HALT')):
        require(spec[opcode]['name']==name,'Diagnostic opcode contract changed')
    code=bytearray();expected=[]
    def store(address):code.extend([0x23,address>>8,address&255])
    for values,addresses in (
        ((0xa5,0x5a,0x96),(0xff03,0xff10,0xff20,0xff30,0xff11,0xfe03,0xff01)),
        ((0x3c,0xc3,0x69),(0xff30,0xff20,0xff10,0xff03,0xff11,0xfe03,0xff01))):
        for slot,value in enumerate(values,1):
            code.extend([0x17,value]);store(0xff00+slot*16)
        # Oracle uses explicit fixture semantics, not a microcode execution trace.
        replies={0xff03:0 if present&1 else 0x81,0xfe03:0x3c}
        replies.update({0xff00+slot*16:0 if present&(1<<slot) else value for slot,value in enumerate(values,1)})
        for address in addresses:
            code.extend([0x1e,address>>8,address&255]);store(0xff00)
            expected.append(replies.get(address,0))
    code.append(0xe2)
    image=bytearray(65536);image[:len(code)]=code;image[0xfe03]=0x3c
    return image,bytes(expected),len(code)


def compose_bench(original,fault=None):
    marker=' reg [7:0] peripheral_data;'
    require(original.count(marker)==1,'CPU bench prefix changed')
    text=original.split(marker)[0]
    old='mar,data_bus,8\'b0,io_data,io_address,io_strobe'
    require(text.count(old)==1,'CPU IO return binding changed')
    text=text.replace(old,'mar,data_bus,bridge_result,io_data,io_address,io_strobe')
    require(text.count('250/(1+OSC_PPM/1.0e6)')==2,'CPU oscillator definition changed')
    text=text.replace('250/(1+OSC_PPM/1.0e6)','OSC_PERIOD_NS/(1+OSC_PPM/1.0e6)')
    probe=(VROOT/'hdl/io_cpu_probe.sv').read_text()
    if fault=='disconnected-return':probe=probe.replace('bridge_result,slot_waddr','unused_return,slot_waddr').replace(
        'wire [7:0] bridge_result;','wire [7:0] unused_return;wire [7:0] bridge_result=0;')
    declarations,body=probe.split(' bridge_dut ',1)
    text=text.replace('module sequencer_tb;','module sequencer_tb;\n'+declarations,1)
    # Retain the original physical-driver contention monitor verbatim.
    physical=original[original.index(' wire [13:0] physical_sources='):]
    return text+' bridge_dut '+body+physical


def profile(folder,corner=1,bridge_profile=1,present=0,endpoint_ns=40,period_ns=250,fault=None,duty=0.5,ppm=0):
    folder=Path(folder);require(not folder.exists(),'Preserve existing profile: '+str(folder))
    folder.mkdir(parents=True)
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in (
        VROOT/'dm02/io_cpu.py',VROOT/'hdl/io_cpu_probe.sv',ROOT/'Code/Microcode/microcode.src',
        VROOT/'dm02/microcode.py',VROOT/'dm02/common.py',VROOT/'targets/cp1/lock.json',io_bridge_evidence.LOCK)}
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text())
    bridge_lock,_=io_bridge_evidence.load()
    prefix=f'cp1-hct273/candidate/Verification/build/compact/c{corner}-cases0/'
    inputs={}
    for name in [b+'.sv' for b in BOARDS]+['support.sv','tb.sv','alu.bin','control.hex']:
        source=BUILD/(prefix+name)
        require(digest(source)==lock['artifacts'][prefix+name],'Changed locked CPU input: '+name)
        inputs[prefix+name]=digest(source)
        if name!='tb.sv':shutil.copyfile(source,folder/name)
    original=(BUILD/(prefix+'tb.sv')).read_text()
    (folder/'tb.sv').write_text(compose_bench(original,fault))
    boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
    circuit=io_bridge.Circuit(BUILD/'cp1-bridge/native',boundary)
    if fault in ('stale-read-address','return-slot-alias'):circuit=circuit.fault(fault)
    (folder/'bridge.sv').write_text(circuit.hdl(bridge_profile))
    image,expected,size=diagnostic(present)
    (folder/'program.hex').write_text(''.join(f'{b:02x}\n' for b in image))
    (folder/'diagnostic.bin').write_bytes(image[:size])
    (folder/'echo-expected.hex').write_text(''.join(f'{b:02x}\n' for b in expected))
    args=['iverilog','-g2012','-s','sequencer_tb','-o','cpu.vvp']
    parameters=dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,
        ENDPOINT_NS=endpoint_ns,OSC_PERIOD_NS=period_ns,PRESENT_N=present,OSC_DUTY=duty,OSC_PPM=ppm)
    for name,value in parameters.items():args+=['-P',f'sequencer_tb.{name}={value}']
    args += [b+'.sv' for b in BOARDS]+['support.sv','bridge.sv','tb.sv']
    code,log=command(args,cwd=folder)
    (folder/'compile.log').write_text(log)
    require(code==0,'CPU bridge compilation failed: '+log)
    start=time.monotonic();code,log=command(['vvp','cpu.vvp'],cwd=folder,timeout=180)
    (folder/'simulation.log').write_text(log)
    match=re.search(r'PASS CPU bridge echoes=(\d+) reads=(\d+) cycles=(\d+) setup_ns=([\d.]+) hold_ns=([\d.]+)',log)
    result=dict(passed=code==0 and bool(match) and 'PASS CPU bridge reset' in log,exit_code=code,
        corner=corner,bridge_profile=bridge_profile,present_n=present,endpoint_ns=endpoint_ns,
        oscillator_period_ns=period_ns,duty=duty,ppm=ppm,fault=fault,wall_seconds=time.monotonic()-start,
        input_hashes=inputs,bridge_lock_sha256=digest(io_bridge_evidence.LOCK),
        model_hashes={p.name:digest(p) for p in folder.glob('*.sv')},
        fixture_hashes={n:digest(folder/n) for n in ('program.hex','control.hex','alu.bin','echo-expected.hex','diagnostic.bin')},
        physical_qualification=False,boot_injected=True,source_hashes=source_hashes)
    if match:result['observations']=dict(zip(('echoes','reads','cycles','min_setup_ns','min_hold_ns'),map(float,match.groups())))
    write_json(folder/'result.json',result)
    require(all(digest(ROOT/n)==h for n,h in source_hashes.items()),'Source changed during CPU bridge profile')
    print(folder.name,result['passed'],log[-500:],flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--corner',type=int,default=1)
    parser.add_argument('--bridge-profile',type=int,default=1)
    parser.add_argument('--present',type=int,default=0)
    parser.add_argument('--endpoint-ns',type=float,default=40)
    parser.add_argument('--period-ns',type=float,default=250)
    parser.add_argument('--fault',choices=['disconnected-return','stale-read-address','return-slot-alias'])
    args=parser.parse_args();profile(args.output,args.corner,args.bridge_profile,args.present,args.endpoint_ns,args.period_ns,args.fault)

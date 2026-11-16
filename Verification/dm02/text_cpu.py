"""R2 + BR1 + TX1 fetched bounded-polling diagnostic; preloaded memory only."""
import json
from pathlib import Path
import re
import shutil
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import io_cpu,io_bridge,io_bridge_evidence,text_card

TRANSCRIPT=b'TX1\r\n'


def diagnostic():
    from .microcode import reference
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
    names={v['name']:(op,v['size']) for op,v in spec.items()}
    code=bytearray();labels={};fixups=[]
    def emit(name,value=0):
        op,size=names[name];code.append(op)
        if isinstance(value,str):fixups.append((len(code),value));value=0
        code.extend(value.to_bytes(size-1,'big'))
    # Independently addressed slot 6 fixture is written/read while TX1 exists.
    emit('MOV A,value',0xa5);emit('MOV address,A',0xff10)
    emit('MOV A,address',0xff10);emit('CMP value',0xa5);emit('JNZ address','error')
    for i,value in enumerate(TRANSCRIPT):
        emit('MOV B,value',255);labels[f'poll{i}']=len(code)
        emit('MOV A,address',0xff03);emit('CMP value',0x81);emit('JZ address',f'ready{i}')
        emit('CMP value',0x80);emit('JNZ address','error')
        emit('DEC B');emit('JNZ address',f'poll{i}');emit('JMP address','error')
        labels[f'ready{i}']=len(code)
        emit('MOV A,value',value);emit('MOV address,A',0xff00)
    emit('MOV A,value',0x5a);emit('MOV address,A',0xff10);emit('HALT')
    labels['error']=len(code);emit('MOV A,value',0xee);emit('MOV address,A',0xff10);emit('HALT')
    for offset,label in fixups:code[offset:offset+2]=labels[label].to_bytes(2,'big')
    return code


def bench(original):
    # Reuse verified R2 pin bindings, then replace the entire behavioral probe.
    old=io_cpu.compose_bench(original)
    prefix=old.split(' bridge_dut ',1)[0]
    physical=old[old.index(' wire [13:0] physical_sources='):]
    return prefix+(VROOT/'hdl/text_cpu_probe.sv').read_text()+physical


def run(circuit,folder,corner=1,bridge_profile=1,text_profile=1,absent=False,period_ns=250,ppm=0):
    folder=Path(folder);text_card.require(not folder.exists(),'Preserve TX1 CPU run');folder.mkdir(parents=True)
    source_hashes={n:digest(ROOT/n) for n in text_card.SOURCES+[
        'Verification/dm02/text_cpu.py','Verification/hdl/text_cpu_probe.sv','Verification/dm02/io_cpu.py',
        'Verification/hdl/io_cpu_probe.sv','Verification/targets/cp1/lock.json','Verification/bridge-evidence.json',
        'Code/Microcode/microcode.src']}
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text());io_bridge_evidence.load()
    prefix=f'cp1-hct273/candidate/Verification/build/compact/c{corner}-cases0/'
    inputs={}
    for name in [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','tb.sv','alu.bin','control.hex']:
        src=BUILD/(prefix+name);text_card.require(digest(src)==lock['artifacts'][prefix+name],'Changed R2 input')
        inputs[prefix+name]=digest(src)
        if name!='tb.sv':shutil.copyfile(src,folder/name)
    (folder/'tb.sv').write_text(bench((BUILD/(prefix+'tb.sv')).read_text()))
    boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
    (folder/'bridge.sv').write_text(io_bridge.Circuit(BUILD/'cp1-bridge/native',boundary).hdl(bridge_profile))
    (folder/'text.sv').write_text(circuit.hdl(text_profile))
    code=diagnostic();image=code+bytes(65536-len(code))
    (folder/'diagnostic.bin').write_bytes(code)
    (folder/'program.hex').write_text(''.join(f'{b:02x}\n' for b in image))
    (folder/'serial-expected.hex').write_text(''.join(f'{b:02x}\n' for b in TRANSCRIPT))
    parameters=dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,
        ABSENT=int(absent),OSC_PERIOD_NS=period_ns,OSC_PPM=ppm)
    args=['iverilog','-g2012','-s','sequencer_tb','-o','cpu.vvp']
    for name,value in parameters.items():args+=['-P',f'sequencer_tb.{name}={value}']
    args += [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv',VROOT/'hdl/text_cells.sv','tb.sv']
    status,log=command(args,cwd=folder);(folder/'compile.log').write_text(log)
    text_card.require(status==0,'TX1 CPU compile failed: '+log)
    status,log=command(['vvp','cpu.vvp'],cwd=folder,timeout=600);(folder/'simulation.log').write_text(log)
    timing=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
    result=dict(passed=status==0 and 'PASS TX1 CPU' in log and timing==0,exit_code=status,timing_violations=timing,
        corner=corner,bridge_profile=bridge_profile,text_profile=text_profile,absent=absent,period_ns=period_ns,ppm=ppm,
        input_hashes=inputs,source_hashes=source_hashes,physical_qualification=False,autonomous_rom_boot=False,
        artifact_hashes={p.name:digest(p) for p in folder.iterdir() if p.is_file()})
    match=re.search(r'PASS TX1 CPU received=(\d+) reads=(\d+) setup_ns=([\d.]+) hold_ns=([\d.]+) halted_ns=([\d.]+) final_stop_ns=([\d.]+)',log)
    if match:result['observations']=dict(zip(('received','reads','setup_ns','hold_ns','halted_ns','final_stop_ns'),map(float,match.groups())))
    write_json(folder/'result.json',result);print(folder.name,result['passed'],log[-900:],flush=True)
    text_card.require(all(digest(ROOT/n)==sha for n,sha in source_hashes.items()),'Source changed during TX1 CPU run')
    return result

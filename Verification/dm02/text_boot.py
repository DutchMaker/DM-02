"""ROM-only startup into the TX1 diagnostic, with CPU-deposited SRAM payload."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
from .common import ROOT,VROOT,BUILD,digest,write_json,command
from . import text_card,text_cpu,text_evidence,io_cpu,io_bridge,io_bridge_evidence

ENTRY=0x4000
STUDY=BUILD/'cp1-text-boot'
require=text_card.require
SOURCES=['Verification/dm02/text_boot.py','Verification/hdl/text_boot_probe.sv',
    'Verification/dm02/text_cpu.py','Verification/dm02/io_cpu.py','Verification/hdl/text_cpu_probe.sv',
    'Verification/hdl/io_cpu_probe.sv','Verification/hdl/text_cells.sv','Verification/text-evidence.json',
    'Verification/bridge-evidence.json','Verification/targets/cp1/lock.json',
    'Verification/dm02/control.py','Verification/dm02/microcode.py','Code/Microcode/microcode.src']


def image(seed=0xa5):
    from .microcode import reference
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
    payload=bytearray(text_cpu.diagnostic());offset=0;relocations=[]
    while offset<len(payload):
        ins=spec[payload[offset]]
        if ins['name'] in ('JMP address','JNZ address','JZ address'):
            target=int.from_bytes(payload[offset+1:offset+3],'big')
            require(target<len(payload),'Diagnostic branch leaves image')
            payload[offset+1:offset+3]=(ENTRY+target).to_bytes(2,'big')
            relocations.append(dict(offset=offset,target=ENTRY+target))
        offset+=ins['size']
    require(offset==len(payload),'Malformed diagnostic instruction stream')
    for op,name in ((0x42,'SP address'),(0x17,'MOV A,value'),(0x23,'MOV address,A'),(0xc3,'JMP address')):
        require(spec[op]['name']==name,'ROM loader opcode changed')
    # A small straight-line ROM loader makes every deposited address explicit.
    # The complete program fits the actual decoded 16 KiB ROM window.
    loader=bytearray([0x42,0xfe,0xf0]);listing=['0000: SP $FEF0']
    for i,value in enumerate(payload):
        address=ENTRY+i;at=len(loader)
        loader.extend([0x17,value,0x23,address>>8,address&255])
        listing.extend([f'{at:04x}: MOV A,#{value:02x}',f'{at+2:04x}: MOV ${address:04x},A'])
    listing.append(f'{len(loader):04x}: JMP ${ENTRY:04x}');loader.extend([0xc3,ENTRY>>8,ENTRY&255])
    require(len(loader)<0x4000,'ROM window exceeded')
    rom=bytes(loader)+bytes([255])*(65536-len(loader))
    poison=bytes(((a*37)^(a>>8)^seed)&255 for a in range(65536))
    return dict(rom=rom,poison=poison,payload=bytes(payload),loader=bytes(loader),
                listing='\n'.join(listing)+'\n',relocations=relocations)


def oracle(data):
    """Execute actual ROM bytes with the separate architectural ISA semantics."""
    from .control import State,instruction
    from .microcode import reference
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
    class Loader(State):
        def put(self,address,value):
            require(ENTRY<=address<ENTRY+len(data['payload']),'Loader writes outside payload')
            self.events.append((address,value));super().put(address,value)
    state=Loader(pc=0);state.memory=dict(enumerate(data['rom'][:ENTRY]+data['poison'][ENTRY:]));state.events=[]
    instructions=0
    while state.pc!=ENTRY and instructions<10000:
        op=state.get(state.pc);state.pc+=1
        ins=spec[op];instruction(ins['name'],ins['size'],state);instructions+=1
        require(not state.halted,'Loader halted before RAM entry')
    expected=[(ENTRY+i,b) for i,b in enumerate(data['payload'])]
    require(state.pc==ENTRY and state.events==expected,'Architectural loader reconstruction failed')
    require(bytes(state.get(ENTRY+i) for i in range(len(data['payload'])))==data['payload'],'Architectural payload differs')
    return dict(passed=True,instructions=instructions,writes=len(state.events),entry=state.pc,
        stack_pointer=state.sp,payload_sha256=hashlib.sha256(data['payload']).hexdigest())


def once(text,old,new):
    require(text.count(old)==1,'Boot transformation anchor changed: '+old)
    return text.replace(old,new,1)


def models(original_memory,original_support):
    memory=once(original_memory,'initial $readmemh("program.hex",memory);','initial $readmemh("boot-rom.hex",memory);')
    memory=once(memory,'initial $readmemh("program.hex",memory,0,65535);','initial $readmemh("sram-power-on.hex",memory);')
    support=once(original_support,'initial $readmemh("program.hex",memory,0,65535);','initial $readmemh("sram-power-on.hex",memory);')
    return memory,support


def bench(original,size):
    text=text_cpu.bench(original)
    # All added memory references are observations; no CPU/ROM/SRAM state writes.
    declarations,body=(VROOT/'hdl/text_boot_probe.sv').read_text().split(' always @',1)
    text=once(text,'module sequencer_tb;',f'module sequencer_tb;\nparameter PAYLOAD_BYTES={size};\n'+declarations)
    text=once(text,' wire [13:0] physical_sources=',' always @'+body+
              '\n wire [13:0] physical_sources=')
    text=once(text,'#2000;reset_request_n=1;', '#25000000;reset_request_n=1;')
    text=once(text,'if(!success || writes!=5)', 'if(!boot_verified)$fatal(1,"TB1 missing verified boot");\n   if(!success || writes!=5)')
    text=once(text,'#50000000;', '#100000000;')
    return text


def run(folder,corner=1,bridge_profile=1,text_profile=1,seed=0xa5,fault=None):
    folder=Path(folder);require(not folder.exists(),'Preserve prior TB1 run');folder.mkdir(parents=True)
    source_hashes={n:digest(ROOT/n) for n in SOURCES}
    text_evidence.load();io_bridge_evidence.load()
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text())
    prefix=f'cp1-hct273/candidate/Verification/build/compact/c{corner}-cases0/'
    inputs={}
    for name in [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','tb.sv','alu.bin','control.hex']:
        src=BUILD/(prefix+name);require(digest(src)==lock['artifacts'][prefix+name],'Changed R2 input')
        inputs[prefix+name]=digest(src)
        if name!='tb.sv':shutil.copyfile(src,folder/name)
    data=image(seed);proof=oracle(data)
    write_json(folder/'oracle.json',proof);(folder/'loader.lst').write_text(data['listing'])
    rom=bytearray(data['rom'])
    if fault=='wrong-loader-byte':rom[4]^=1
    elif fault=='wrong-loader-address':rom[7]^=1
    elif fault=='skip-loader':rom[:3]=bytes([0xc3,ENTRY>>8,ENTRY&255])
    elif fault is not None:raise ValueError(fault)
    for name,raw in [('boot-rom',rom),('sram-power-on',data['poison']),('payload',data['payload'])]:
        (folder/(name+'.bin')).write_bytes(raw)
        (folder/(name+'.hex')).write_text(''.join(f'{b:02x}\n' for b in raw))
    (folder/'serial-expected.hex').write_text(''.join(f'{b:02x}\n' for b in text_cpu.TRANSCRIPT))
    memory,support=models((folder/'ME1.sv').read_text(),(folder/'support.sv').read_text())
    (folder/'ME1.sv').write_text(memory);(folder/'support.sv').write_text(support)
    (folder/'tb.sv').write_text(bench((BUILD/(prefix+'tb.sv')).read_text(),len(data['payload'])))
    c=text_card.Circuit(text_card.STUDY/'iteration-2/native/TX1')
    (folder/'text.sv').write_text(c.hdl(text_profile))
    boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
    (folder/'bridge.sv').write_text(io_bridge.Circuit(BUILD/'cp1-bridge/native',boundary).hdl(bridge_profile))
    args=['iverilog','-g2012','-s','sequencer_tb','-o','boot.vvp']
    for p in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY'):args+=['-P',f'sequencer_tb.{p}=1']
    args += [b+'.sv' for b in io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv',VROOT/'hdl/text_cells.sv','tb.sv']
    code,log=command(args,cwd=folder);(folder/'compile.log').write_text(log);require(code==0,'TB1 compile failed: '+log)
    code,log=command(['vvp','boot.vvp'],cwd=folder,timeout=600);(folder/'simulation.log').write_text(log)
    timing=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
    result=dict(passed=code==0 and 'PASS TB1 ROM reconstruction' in log and 'PASS TX1 CPU received=5' in log and timing==0,
        exit_code=code,timing_violations=timing,corner=corner,bridge_profile=bridge_profile,text_profile=text_profile,
        seed=seed,fault=fault,source_hashes=source_hashes,input_hashes=inputs,physical_qualification=False,
        rom_only_startup=True,host_boot_injected=False,payload_bytes=len(data['payload']),loader_bytes=len(data['loader']),
        hashes={p.name:digest(p) for p in folder.iterdir() if p.is_file()})
    write_json(folder/'result.json',result)
    require(all(digest(ROOT/n)==h for n,h in source_hashes.items()),'TB1 source changed during run')
    print(folder.name,result['passed'],log[-600:],flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--corner',type=int,default=1)
    p.add_argument('--seed',type=lambda x:int(x,0),default=0xa5);p.add_argument('--fault',choices=['wrong-loader-byte','wrong-loader-address','skip-loader'])
    a=p.parse_args();run(a.output,corner=a.corner,seed=a.seed,fault=a.fault)

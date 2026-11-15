"""BL1 executable ROM loader for the unchanged RAM graphics image.

Reverse RLE feeds descending PUSH writes. The CPU initializes its own SRAM
workspace and enters the application without a host bootstrap jump.
"""
from collections import Counter,ChainMap
from copy import copy
from itertools import groupby
import hashlib
import re
import struct
from dm02.common import ROOT,BUILD,digest,write_json
from dm02.microcode import reference
from dm02.programs import Machine
from dm02.control import instruction,execute,differences

ENTRY=0x4000;STREAM=0x100;POINTER=0xfef8;COUNT=0xfefa


def build(folder):
    folder.mkdir(parents=True,exist_ok=True)
    binary=ROOT/'Code/Emulator/programs/emulator_demo.bin';original=binary.read_bytes();payload=original[ENTRY:]
    assert original[:ENTRY]==bytes(ENTRY) and payload and ENTRY+len(payload)<POINTER
    encoded=bytearray();runs=0
    for value,group in groupby(reversed(payload)):
        length=len(list(group))
        while length:
            count=min(length,255);encoded.extend([count,value]);length-=count;runs+=1
    encoded.append(0);reconstructed=bytearray();position=0
    while encoded[position]:
        count,value=encoded[position:position+2];reconstructed.extend([value]*count);position+=2
    assert position==len(encoded)-1 and bytes(reversed(reconstructed))==payload
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text());names={i['name']:(op,i['size']) for op,i in spec['instructions'].items()}
    code=bytearray();labels={};fixups=[];listing=[]
    def label(name):
        assert name not in labels;labels[name]=len(code)
    def emit(name,operand=None):
        op,size=names[name];address=len(code);code.append(op)
        if isinstance(operand,str):fixups.append((len(code),operand,size-1));value=0
        else:value=operand
        if size>1:code.extend(int(value).to_bytes(size-1,'big'))
        else:assert operand is None
        listing.append(dict(address=address,instruction=name,operand=operand,size=size))
    def increment_bc(tag):
        emit('INC C');emit('JNZ address',tag);emit('INC B');label(tag)
    emit('SP address',len(original)-1)
    emit('MOV B,value',STREAM>>8);emit('MOV C,value',STREAM&255);emit('MOV address,BC',POINTER)
    label('record');emit('MOV BC,address',POINTER);emit('MOV A,(BC)');emit('CMP value',0);emit('JZ address','done')
    emit('MOV address,A',COUNT);increment_bc('value')
    emit('MOV A,(BC)');increment_bc('saved_pointer');emit('MOV address,BC',POINTER)
    emit('MOV B,address',COUNT)
    label('repeat');emit('PUSH A');emit('DEC B');emit('JNZ address','repeat');emit('JMP address','record')
    label('done');emit('JMP address',ENTRY)
    for at,name,width in fixups:code[at:at+width]=labels[name].to_bytes(width,'big')
    assert len(code)<=STREAM and STREAM+len(encoded)<=0x4000
    rom=bytearray([255]*65536);rom[:len(code)]=code;rom[STREAM:STREAM+len(encoded)]=encoded
    (folder/'boot-rom.bin').write_bytes(rom);(folder/'boot-rom.hex').write_text(''.join(f'{v:02x}\n' for v in rom))
    (folder/'loader-target.hex').write_text(''.join(f'{v:02x}\n' for v in original+bytes(65536-len(original))))
    (folder/'loader.lst').write_text('\n'.join(f'{r["address"]:04x}: {r["instruction"]} '+(str(r['operand']) if r['operand'] is not None else '') for r in listing)+'\n')
    result=dict(entry=ENTRY,payload_end=len(original)-1,payload_bytes=len(payload),rle_records=runs,rle_bytes=len(encoded),
                loader_bytes=len(code),rom_used_bytes=STREAM+len(encoded),physical_rom_bytes=len(rom),
                program_sha256=digest(binary),payload_sha256=hashlib.sha256(payload).hexdigest(),rom_sha256=digest(folder/'boot-rom.bin'),
                labels=labels,listing=listing,workspace=dict(pointer=POINTER,count=COUNT),expected_loader_sram_writes=len(payload)+3*runs+2,
                scope='64 KiB AT27C512R image; only 0000..3FFF is decoded as ROM. CPU reconstructs the unchanged graphics '
                      'payload at 4000..payload_end, then jumps to 4000. FEF8..FEFA are CPU-initialized loader workspace. '
                      'Physical programming/readback and actual device startup remain unverified.')
    write_json(folder/'image.json',result);return result


def fixtures(folder,seed=0xa5,full_demo=False):
    image=build(folder);rom=(folder/'boot-rom.bin').read_bytes()
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    raw=b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8));alu=struct.unpack('<2097152H',raw)
    swapped=bytearray(len(raw));swapped[0::2]=raw[1::2];swapped[1::2]=raw[0::2];(folder/'alu.bin').write_bytes(swapped)
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    sram=bytes(((a*37)^(a>>8)^seed)&255 for a in range(131072))
    (folder/'sram-power-on.hex').write_text(''.join(f'{v:02x}\n' for v in sram))
    memory=rom[:0x4000]+sram[0x4000:65536];(folder/'program.hex').write_text(''.join(f'{v:02x}\n' for v in memory))
    cycles=instructions=0;ops=Counter();boot_complete=False;boot_state=None
    with (folder/'expected.txt').open('w') as trace_file,(folder/'io-expected.txt').open('w') as io:
        class BootMachine(Machine):
            io_count=0;ram_writes=0
            def put(self,address,value):
                super().put(address,value)
                if 0x4000<=address<0xff00:self.ram_writes+=1
                if address>=0xff00:io.write(f'{address&255:02x} {value&255:02x}\n');self.io_count+=1
        state=BootMachine(memory[:0xff00]);assert not state.boot_injected
        def row(kind,op,t,word,before,after,bus=None):
            nonlocal cycles
            packed=sum(after['registers'][r]<<(8*(4-i)) for i,r in enumerate('ABCHL'))
            values=[kind,op,t,word,before,after['pc'],after['flags'],after['sp'],after['mar'],packed,bus or 0,int(bus is not None)]
            trace_file.write(' '.join(f'{v:x}' for v in values)+'\n');cycles+=1
        while not state.halted and instructions<1000000:
            if state.pc==ENTRY and not boot_complete:
                actual=bytes(state.memory[a] for a in range(ENTRY,image['payload_end']+1))
                assert hashlib.sha256(actual).hexdigest()==image['payload_sha256']
                assert state.ram_writes==image['expected_loader_sram_writes']
                assert state.io_count==0 and state.ignored_rom_writes==0
                boot_state=dict(instructions=instructions,microcycles=cycles,ram_writes=state.ram_writes,final=state.snapshot())
                boot_complete=True
                if not full_demo:break
            pc=state.pc;op=state.get(pc);ins=spec['instructions'].get(op)
            if ins is None:raise ValueError(f'Unknown opcode {op:02x} at {pc:04x}')
            state.mar=pc;row(0,op,0,0,pc,dict(**state.snapshot(),mar=state.mar))
            state.pc=(pc+1)&65535;row(1,op,0,0,pc,dict(**state.snapshot(),mar=state.mar),op)
            state.writes={};want=copy(state) if not boot_complete else None
            if want is not None:
                want.r=state.r.copy();want.memory=ChainMap({},state.memory);want.writes={}
                instruction(ins['name'],ins['size'],want)
            trace=execute(words,alu,op,state,'circuit','output')
            if want is not None:
                delta=differences(state,want)
                if delta:raise ValueError(f'BL1 loader oracle disagreement {pc:04x} {ins["name"]}: {delta}')
            for i,s in enumerate(trace):
                after=trace[i+1] if i+1<len(trace) else dict(**state.snapshot(),mar=state.mar)
                row(2,op,s['t'],int(s['word'],16),s['pc'],after,s['bus'])
            instructions+=1;ops[f'{op:02x}']+=1
    assert boot_complete and (state.halted if full_demo else state.pc==ENTRY)
    output=dict(text=bytes(state.text).decode('latin1'),pixels_checked=0,pixel_errors=0,pixel_sha256=hashlib.sha256(state.pixels).hexdigest())
    if full_demo:
        bitmap=[int(x,16) for x in re.findall(r'\$([0-9a-f]{2})',(ROOT/'Code/Assembler/programs/emulator_demo/emulator_demo_data.asm').read_text(),re.I)]
        assert bitmap and len(bitmap)<=16384 and set(bitmap)<={0,1}
        expected=bytearray(48000)
        for i,value in enumerate(bitmap):expected[(i//128)*240+i%128]=255*value
        output.update(pixels_checked=48000,pixel_errors=sum(a!=b for a,b in zip(state.pixels,expected)))
        assert output['text']=='Hello world\r:-)' and output['pixel_errors']==0,output
    result=dict(image=image,seed=seed,full_demo=full_demo,instructions=instructions,microcycles=cycles,io_events=state.io_count,
                ram_writes=state.ram_writes,boot=boot_state,final=state.snapshot(),opcode_counts=dict(ops),boot_injected=state.boot_injected,output=output,
                scope='ROM-only initialization with deterministic poisoned SRAM. Every loader instruction is checked against '
                      'the architectural oracle. Payload hash, exact SRAM write count and absence of loader IO/ROM writes '
                      'are checked before application entry.')
    write_json(folder/'coverage.json',result);return result

"""Compiled demos through all pin-derived candidates, observed at ME1 IO pins."""
from collections import Counter
import hashlib
import re
import struct
from .common import ROOT,BUILD,digest,evidence,write_json
from .programs import Machine
from .control import execute
from .microcode import reference


def fixtures(folder,name):
    folder.mkdir(parents=True,exist_ok=True)
    binary=ROOT/f'Code/Emulator/programs/{name}.bin'
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    raw=b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8))
    alu=struct.unpack('<2097152H',raw)
    swapped=bytearray(len(raw));swapped[0::2]=raw[1::2];swapped[1::2]=raw[0::2];(folder/'alu.bin').write_bytes(swapped)
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    with (folder/'io-expected.txt').open('w') as io,(folder/'expected.txt').open('w') as trace_file:
        class ObservedMachine(Machine):
            io_count=0
            def put(self,address,value):
                super().put(address,value)
                if (address&65535)>=0xff00:
                    io.write(f'{address&255:02x} {value&255:02x}\n');self.io_count+=1
        state=ObservedMachine(binary.read_bytes())
        (folder/'program.hex').write_text(''.join(f'{state.memory.get(a,0):02x}\n' for a in range(65536)))
        instructions=cycles=0;ops=Counter()
        def row(kind,op,t,word,before,after,bus=None):
            nonlocal cycles
            packed=sum(after['registers'][r]<<(8*(4-i)) for i,r in enumerate('ABCHL'))
            values=[kind,op,t,word,before,after['pc'],after['flags'],after['sp'],after['mar'],packed,bus or 0,int(bus is not None)]
            trace_file.write(' '.join(f'{v:x}' for v in values)+'\n');cycles+=1
        while not state.halted and instructions<1000000:
            pc=state.pc;op=state.get(pc)
            if op not in spec['instructions']:raise ValueError('Undefined demo opcode')
            state.mar=pc;row(0,op,0,0,pc,dict(**state.snapshot(),mar=state.mar))
            state.pc=(pc+1)&65535;row(1,op,0,0,pc,dict(**state.snapshot(),mar=state.mar),op)
            trace=execute(words,alu,op,state,'circuit','output')
            for i,s in enumerate(trace):
                after=trace[i+1] if i+1<len(trace) else dict(**state.snapshot(),mar=state.mar)
                row(2,op,s['t'],int(s['word'],16),s['pc'],after,s['bus'])
            instructions+=1;ops[f'{op:02x}']+=1
        if not state.halted:raise ValueError('Demo fixture instruction limit')
    result=dict(name=name,binary_sha256=digest(binary),instructions=instructions,microcycles=cycles,io_events=state.io_count,
                opcode_counts=dict(ops),boot_injected=state.boot_injected,final=state.snapshot(),
                scope='Compiled-control expected trace. Independent acceptance is exact text and source bitmap; the all-opcode suite separately checks instruction semantics.')
    write_json(folder/'coverage.json',result);return result


def render(folder,name):
    # Only connector-observed address/data pairs enter this host display.
    state=Machine(b'\xe2');events=0
    for line in (folder/'io-observed.txt').read_text().splitlines():
        port,value=(int(v,16) for v in line.split())
        if not 0<=port<=255 or not 0<=value<=255:raise ValueError('Invalid observed IO byte')
        state.put(0xff00|port,value);events+=1
    text=bytes(state.text).decode('latin1');pixel_errors=0;checked=0
    if name=='emulator_demo':
        source=ROOT/'Code/Assembler/programs/emulator_demo/emulator_demo_data.asm'
        bitmap=[int(x,16) for x in re.findall(r'\$([0-9a-f]{2})',source.read_text(),re.I)]
        if not bitmap or len(bitmap)>16384 or set(bitmap)-{0,1}:raise ValueError('Unexpected source bitmap')
        expected=bytearray(48000)
        for i,value in enumerate(bitmap):expected[(i//128)*240+i%128]=255*value
        pixel_errors=sum(a!=b for a,b in zip(state.pixels,expected));checked=48000
    (folder/'display.pgm').write_bytes(b'P5\n240 200\n255\n'+state.pixels)
    (folder/'text.txt').write_text(text)
    return dict(passed=text=='Hello world\r:-)' and pixel_errors==0,text=text,io_events=events,pixels_checked=checked,
                pixel_errors=pixel_errors,pixel_sha256=hashlib.sha256(state.pixels).hexdigest())


def simulate(folder,fixture,corner=1,memory=None):
    from .alu_hardware import Circuit as Alu,simulate as fetched
    from .register_hardware import Circuit as Registers
    from .address_hardware import AddressPath
    from .memory_hardware import Circuit as Memory
    return fetched(Alu(),folder,corner,fixture,True,registers=Registers(),address_path=AddressPath(),memory=memory or Memory(),demo=True)


def run():
    folder=BUILD/'hardware-programs';folder.mkdir(parents=True,exist_ok=True);results=[]
    artifacts=['hardware-programs/summary.json']
    for name in ('hello_world','emulator_demo'):
        dest=folder/name;coverage=fixtures(dest/'fixtures',name)
        r=simulate(dest/'maximum',dest/'fixtures');r.pop('log')
        output=render(dest/'maximum',name) if r['passed'] else None
        passed=r['passed'] and output['passed'] and output['io_events']==coverage['io_events']
        results.append(dict(name=name,passed=passed,coverage=coverage,simulation=r,output=output))
        artifacts.extend(f'hardware-programs/{name}/'+p for p in ('fixtures/coverage.json','maximum/alu.log'))
        if output:artifacts.extend(f'hardware-programs/{name}/maximum/'+p for p in ('io-observed.txt','display.pgm','text.txt'))
    scope=('C1/SQ1/CW1/PC1/AL1/RG1/SP1/MA1/ME1 maximum-delay models execute compiled binaries from reset through HALT. '
           'Every fetched/control cycle is compared; IO address/data and 40 ns setup/hold are checked at the ME1 connector. '
           'Host rendering consumes only observed IO events. Fixture-loaded program/zero RAM and bootstrap jump where required; '
           'no hardware loader or display circuit. DATA loading, SRAM turnaround, obsolete ALU ROM and clock/reset remain unqualified.')
    write_json(folder/'summary.json',dict(results=results,scope=scope))
    passed=all(r['passed'] for r in results)
    return evidence('hardware-programs','Compiled demos on pin-derived machine','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in results)}/2 demos; {sum(r["coverage"]["microcycles"] for r in results):,} fetched/control cycles; '
                    'exact text and 48,000 display pixels checked at external IO.',artifacts=artifacts,limitation=scope)

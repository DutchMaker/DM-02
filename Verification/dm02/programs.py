"""Run committed demos through compiled control words and bounded host IO."""
from collections import Counter, deque
from functools import lru_cache
import hashlib
import re
import struct
from .common import ROOT, BUILD, digest, evidence, write_json
from .control import State, execute
from .microcode import reference
from .memory import Decoder


class Machine(State):
    def __init__(self,binary,decoder=None):
        super().__init__(pc=0,registers={r:0 for r in 'ABCHL'},sp=0)
        self.decoder=decoder or Decoder()
        if self.decoder.routes()['errors']: raise ValueError('Memory pin routes do not match byte-addressed host model')
        self.ignored_rom_writes=0
        if len(binary)>0xff00: raise ValueError('Program overlaps host IO')
        self.memory=dict(enumerate(binary))
        self.boot_injected=self.get(0)==0
        if self.boot_injected: self.memory.update({0:0xc3,1:0x40,2:0})
        self.text=[]; self.pixels=bytearray(240*200); self.x=self.y=self.io_data=0
        self.color_high=self.color_low=0; self.io_writes=Counter()

    @lru_cache(maxsize=512)
    def selection(self,high,read):
        # Each access assumes MAR has settled to this address. The independent
        # decoder audit checks every external bus high byte; use zero here.
        return self.decoder.evaluate(high<<8,0,read=read,write=not read,phase2=1)

    def get(self,address):
        address &= 65535
        if address>=0xff00: raise ValueError(f'Unmodelled IO read {address:04x}')
        selected=self.selection(address>>8,True)
        if not selected['memory_to_cpu'] or selected['rom_driving']==selected['ram_driving']:
            raise ValueError(f'Memory read bus selection invalid at {address:04x}')
        return self.memory.get(address,0)

    def put(self,address,value):
        address &= 65535; value &= 255
        selected=self.selection(address>>8,False)
        if selected['rom_driving'] or selected['ram_driving']:
            raise ValueError('Memory drives during CPU write')
        if selected['ram_writing']:
            if not selected['cpu_to_memory'] or selected['io_load']: raise ValueError('RAM write bus selection invalid')
            return super().put(address,value)
        if not selected['io_load']:
            if address>=0x4000: raise ValueError('RAM/IO write silently dropped')
            self.ignored_rom_writes+=1
            return
        if selected['cpu_to_memory'] or selected['memory_to_cpu']: raise ValueError('Memory buffer enabled during IO')
        self.io_writes[f'{address:04x}']+=1
        if address==0xff00: self.text.append(value)
        elif address==0xff01: self.io_data=value
        elif address==0xff02:
            if value==1: self.color_high=self.io_data
            elif value==2: self.color_low=self.io_data
            elif value==4: self.x=self.io_data
            elif value==8: self.y=self.io_data
            elif value==16:
                if self.color_high!=255 or self.color_low!=255:
                    raise ValueError('Only white-pixel demo colour is modelled')
                if self.x>=240 or self.y>=200: raise ValueError('Pixel outside host display')
                self.pixels[self.y*240+self.x]=255
            else: raise ValueError(f'Unmodelled display command {value:02x}')
        else: raise ValueError(f'Unmodelled IO write {address:04x}')


def run():
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    alu=struct.unpack('<2097152H',b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8)))
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    bitmap_path=ROOT/'Code/Assembler/programs/emulator_demo/emulator_demo_data.asm'
    bitmap=[int(x,16) for x in re.findall(r'\$([0-9a-f]{2})',bitmap_path.read_text(),re.I)]
    if not bitmap or len(bitmap)>16384 or set(bitmap)-{0,1}: raise ValueError('Unexpected demo bitmap format')
    expected=bytearray(48000)
    for i,value in enumerate(bitmap): expected[(i//128)*240+i%128]=255*value
    results=[]
    decoder=Decoder()
    for name in ('hello_world','emulator_demo'):
        path=ROOT/f'Code/Emulator/programs/{name}.bin'; machine=Machine(path.read_bytes(),decoder)
        steps=tstates=0; coverage=Counter(); tail=deque(maxlen=32); error=None
        try:
            while not machine.halted and steps<1000000:
                pc=machine.pc; opcode=machine.get(pc)
                if opcode not in spec['instructions']: raise ValueError(f'Undefined opcode {opcode:02x} at {pc:04x}')
                tail.append(dict(pc=pc,opcode=opcode,flags=machine.f,sp=machine.sp))
                machine.pc=(pc+1)&65535  # Ideal fetch; electrical fetch timing excluded.
                trace=execute(words,alu,opcode,machine,'circuit','output')
                tstates+=len(trace); coverage[f'{opcode:02x}']+=1; steps+=1
            if not machine.halted: raise ValueError('Instruction limit reached')
        except ValueError as err: error=str(err)
        text=bytes(machine.text).decode('latin1')
        pixel_errors=sum(a!=b for a,b in zip(machine.pixels,expected)) if name=='emulator_demo' else 0
        ok=error is None and machine.halted and text=='Hello world\r:-)' and pixel_errors==0
        results.append(dict(name=name,status='pass' if ok else 'fail',binary_sha256=digest(path),
            halted=machine.halted,instructions=steps,microinstructions=tstates,opcode_counts=dict(coverage),
            text=text,pixels_checked=48000 if name=='emulator_demo' else 0,pixel_errors=pixel_errors,
            pixel_sha256=hashlib.sha256(machine.pixels).hexdigest(),io_writes=dict(machine.io_writes),
            final=machine.snapshot(),boot_injected=machine.boot_injected,ignored_rom_writes=machine.ignored_rom_writes,
            error=error,last_instructions=list(tail)))
    result=dict(results=results,bitmap_sha256=digest(bitmap_path),
        scope='Compiled ROM + generated ALU + extracted Logisim PC and KiCad memory decode. Ideal opcode fetch/word latch; flags commit at ALU output; settled MAR at each access. ROM write protection, zero-initialized RAM and host text/white-pixel IO. Includes bootstrap jumps; no timed memory bus, power qualification or display circuit.')
    write_json(BUILD/'microcode/programs.json',result)
    good=all(r['status']=='pass' for r in results)
    return evidence('control-programs','Compiled-control demo execution','pass' if good else 'fail',
        f'{sum(r["instructions"] for r in results):,} instructions / {sum(r["microinstructions"] for r in results):,} microinstructions; '
        + ('both demos halt with exact text and 48,000 checked pixels.' if good else 'demo output differs; inspect execution evidence.'),
        artifacts=['microcode/programs.json'],limitation=result['scope'])

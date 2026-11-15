"""Replay compiled microinstructions through the KiCad-derived ALU HDL."""
import struct
from .common import ROOT, BUILD, digest, evidence, write_json
from .microcode import reference
from .control import execute, fixture
from .alu_circuit import Datapath, simulate


def vectors(words,alu_words,spec):
    rows=[];cases=[];microsteps=0;simultaneous=0
    states=[(0x1201,0x00,0x4567),(0x12fe,0x7f,0x45ff),(0x12ff,0x80,0x4500),
            (0xffff,0xff,0xffff),(0x0000,0x01,0x0000),(0x3401,0x55,0x8000)]
    for opcode,ins in spec['instructions'].items():
        for flags in range(16):
            for pc,seed,target in states:
                state=fixture(pc,flags,seed,target);start=len(rows)
                # Fixture setup uses connector-driven A_load/F_load cycles;
                # the design receives no direct register-state injection.
                rows.append(state.r['A']|(1<<13)|(1<<14))
                rows.append(flags|(1<<13)|(1<<16)|(flags<<23)|(1<<30))
                for step in execute(words,alu_words,opcode,state,'circuit','output'):
                    word=int(step['word'],16);data=bool(word&0x8000)
                    out=(word>>11)&15 if data else 0
                    load=(word>>7)&15 if data else 0
                    operation=(word>>1)&31 if data and word&64 else 0
                    funcs=[] if data and word&64 else ([(word>>1)&15] if data else [(word>>11)&15,(word>>1)&15])
                    if out==6 and load==7: raise ValueError('Simultaneous raw and bus flag captures need a defined priority')
                    commands=0
                    for f in funcs:
                        if f in (9,10,11,12): commands|=1<<{9:3,10:2,11:1,12:0}[f]
                    bus=step['bus'] or 0
                    row=bus|(operation<<8)|(int(out not in (0,6,7))<<13)
                    row|=int(load==1)<<14|int(load==6)<<15|int(load==7)<<16
                    row|=int(out==6)<<17|int(out==7)<<18|commands<<19
                    row|=step['post_flags']<<23|int(out!=0)<<27|1<<30
                    if load==6:
                        address=(operation<<16)|(step['registers']['A']<<8)|bus
                        row|=1<<31|address<<32
                    rows.append(row);microsteps+=1
                    simultaneous+=int(out==6 and load==1)
                cases.append(dict(opcode=opcode,instruction=ins['name'],pc=pc,flags=flags,seed=seed,
                                  target=target,start=start,end=len(rows)))
    return rows,dict(cases=cases,microsteps=microsteps,simultaneous_a_flags=simultaneous)


def stimulus(count,rom='../circuit/rom.hex'):
    return f'''initial begin : sequences
  reg [63:0] sequence_words [0:{count-1}];
  reg [63:0] item;
  $readmemh("{rom}",rom);
  $readmemh("sequences.hex",sequence_words);
  for(k=0;k<{count};k=k+1) begin
    item=sequence_words[k];
    a_load_n=!item[14]; alu_load_n=!item[15]; f_load_n=!item[16];
    alu_out_n=!item[17]; f_out_n=!item[18]; commands=~item[22:19];
    operation=item[12:8]; data_in=item[7:0]; drive=item[13];
    external_address=k^16'h5aa5; #2;
    if(item[27] && data_bus !== item[7:0])
      $fatal(1,"sequence %0d bus: got %h expected %h",k,data_bus,item[7:0]);
    if(!drive && !item[17] && !item[18] && data_bus !== 8'bz)
      $fatal(1,"sequence %0d bus release",k);
    tick;
    if(item[30] && flags !== item[26:23])
      $fatal(1,"sequence %0d flags: got %h expected %h",k,flags,item[26:23]);
    if(item[31] && rom_address !== item[52:32])
      $fatal(1,"sequence %0d captured operands",k);
  end
  $display("DONE sequences={count}"); $finish;
end'''


def run():
    folder=BUILD/'alu/sequences';folder.mkdir(parents=True,exist_ok=True)
    rom=BUILD/'microcode/microcode.rom';banks=[BUILD/f'alu/alu{i}.rom' for i in range(8)]
    words=struct.unpack('<65536H',rom.read_bytes())
    alu_words=struct.unpack('<2097152H',b''.join(p.read_bytes() for p in banks))
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    rows,details=vectors(words,alu_words,spec)
    (folder/'sequences.hex').write_text(''.join(f'{row:016x}\n' for row in rows))
    ok,log=simulate(Datapath(),folder,stimulus(len(rows)),f'DONE sequences={len(rows)}')
    scope=('Compiled control words replayed through the KiCad-derived ALU, including simultaneous A/flag capture. '
           'The host supplies other register/memory bus values and ideal PH3 cycles; the controller executor supplies '
           'expected bus/flags and is separately checked against the instruction oracle. No physical controller, '
           'memory timing, latch/decode transients, reset sequencing or whole-machine qualification.')
    details.update(rows=len(rows),source_hashes={str(p.relative_to(ROOT)):digest(p) for p in [rom,*banks]},scope=scope)
    write_json(folder/'coverage.json',details)
    return evidence('alu-sequences','Compiled-control ALU circuit sequences','pass' if ok else 'fail',
                    f'{len(details["cases"]):,} cases across 227 opcodes; {details["microsteps"]:,} microinstructions; '
                    f'{details["simultaneous_a_flags"]:,} simultaneous A/flag captures.',
                    artifacts=['alu/sequences/coverage.json','alu/sequences/sequences.hex','alu/sequences/slice.sv',
                               'alu/sequences/slice.log'],limitation=scope)

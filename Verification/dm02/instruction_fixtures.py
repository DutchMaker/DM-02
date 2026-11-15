"""Fetched opcode cases with software initialization and independent state checks."""
from copy import deepcopy
import struct
from .common import ROOT,BUILD,write_json
from .control import State,execute,instruction,differences
from .microcode import reference


def generate(folder,quick=False):
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    names={v['name']:op for op,v in spec['instructions'].items()}
    words=struct.unpack('<65536H',(BUILD/'microcode/microcode.rom').read_bytes())
    alu=struct.unpack('<2097152H',b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8)))
    cases=[];rows=[];covered=set();targets=0;executed=0
    selected=list(spec['instructions'])
    if quick:selected=[names[n] for n in ('NOP','ADD value','CALL address','RET','MOV BC,(address)','HALT')]
    for opcode in selected:
        for flags in (0,15):
            code=bytearray()
            def emit(name,value=0):
                op=names[name];size=spec['instructions'][op]['size'];code.append(op)
                if size>1:code.extend(value.to_bytes(size-1,'big'))
            emit('SP address',0x9000);emit('MOV A,value',flags|0xf0);emit('PUSH A');emit('POP F')
            for reg,value in [('A',0x7f),('B',0x82),('C',0),('H',0x83),('L',0)]:emit('MOV '+reg+',value',value)
            target_pc=len(code);ins=spec['instructions'][opcode]
            emit(ins['name'],0x8200 if ins['size']==3 else 0x81)
            initial=dict(enumerate(code));initial.update({0x9001:0xfe,0x9002:0x34,0x8200:0x83,0x8201:0})
            def fresh():
                s=State(pc=0,flags=0,registers={r:0 for r in 'ABCHL'},sp=0);s.memory=dict(initial);return s
            # Find the post-target PC, then place a HALT there before recording
            # the real case. Re-execution catches any alias introduced by it.
            s=fresh()
            for _ in range(10):
                pc=s.pc;op=s.get(pc);s.pc=(pc+1)&65535;execute(words,alu,op,s,'circuit','output')
            halt_pc=s.pc if opcode!=names['HALT'] else target_pc
            if opcode!=names['HALT']:initial[halt_pc]=names['HALT']
            s=fresh();start=len(rows);target_seen=False
            while not s.halted:
                pc=s.pc;op=s.get(pc);op_ins=spec['instructions'][op];covered.add(op)
                if pc==target_pc:
                    if op!=opcode or s.f!=flags:raise ValueError('Opcode fixture initialization failed')
                    target_seen=True
                def row(kind,t,word,before,after,bus=None):
                    packed=sum(after['registers'][r]<<(8*(4-i)) for i,r in enumerate('ABCHL'))
                    values=[kind,op,t,word,before,after['pc'],after['flags'],after['sp'],after['mar'],packed,bus or 0,int(bus is not None)]
                    rows.append(' '.join(f'{v:x}' for v in values)+'\n')
                s.mar=pc;row(0,0,0,pc,dict(**s.snapshot(),mar=s.mar))
                s.pc=(pc+1)&65535;row(1,0,0,pc,dict(**s.snapshot(),mar=s.mar),op)
                want=deepcopy(s);instruction(op_ins['name'],op_ins['size'],want)
                trace=execute(words,alu,op,s,'circuit','output')
                delta=differences(s,want)
                if delta:raise ValueError(f'Fetched opcode oracle disagreement {opcode:02x}: {delta}')
                for i,t in enumerate(trace):
                    after=trace[i+1] if i+1<len(trace) else dict(**s.snapshot(),mar=s.mar)
                    row(2,t['t'],int(t['word'],16),t['pc'],after,t['bus'])
                executed+=1
                if len(rows)-start>150:raise ValueError('Fetched opcode case did not terminate')
            if not target_seen:raise ValueError('Target opcode was not fetched')
            cases.append(f'{len(rows)-start:x} {len(code):x} {halt_pc:x} '+ ' '.join(f'{b:02x}' for b in code)+'\n')
            targets+=1
    (folder/'cases.txt').write_text(''.join(cases));(folder/'instructions.txt').write_text(''.join(rows))
    result=dict(cases=targets,target_opcodes=len(selected),flag_profiles=[0,15],instructions=executed,microcycles=len(rows),
                observed_opcodes=sorted(covered),scope='Hardware fetch; software initialization of A/flags and registers; patterned memory with explicit stack/pointer fixtures. The consuming profile states which peripheral circuits are pin-derived.')
    write_json(folder/'instructions-coverage.json',result);return result

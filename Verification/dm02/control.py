"""Bounded execution of compiled control words against instruction semantics.

This is an untimed hypothesis model. Phase order and ALU flag capture are swept,
not inferred from the unfinished controller. Architectural expectations preserve
registers unless the instruction names a destination; this contract needs review.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import struct
from .common import ROOT, BUILD, digest, evidence, write_json
from .microcode import reference
from .logisim_pc import ProgramCounter

REGS=('A','B','C','H','L')
OPERANDS=(None,'A','B','C','H','L','ALU','F','MAR_H','MAR_L','MEM','PC_H','PC_L','STK_H','STK_L')
CONDITIONS={'C':(0,1),'Z':(2,1),'N':(3,1),'O':(1,1),
            'NC':(0,0),'NZ':(2,0),'P':(3,0),'NO':(1,0)}
ASSUMPTIONS=[
    'Entry PC points to the first operand after an ideal opcode fetch; fetch itself is outside the model.',
    'Each control word is latched for its t-state; its ROM address uses the live low four flag bits.',
    'PC/STK-to-MAR transfer precedes bus sampling and uses the pre-increment counter value.',
    'PC profiles: counter functions before capture, after capture, or simultaneous nibble updates extracted from Logisim. No profile qualifies physical hardware.',
    'ALU_load records the settled ROM word in this executor. The KiCad circuit instead stores operands/operation. Output-phase flag capture matches its logical wiring; the load-phase profile remains a sensitivity experiment. Physical timing is unqualified.',
    'Packed F uses C,O,Z,N in bits 0..3 and zero in bits 4..7, matching the KiCad data-path slice, guarded Logisim reference and emulator. ROM DZ is not stored.',
    'Flat writable 64 KiB memory wraps at 16 bits; ROM protection, IO, electrical delays and intra-word decode hazards are excluded.',
    'Instruction contract follows the documented address-building scratch convention: HL holds effective addresses and taken branch targets; MOV address,HL uses BC. V=0 outside signed arithmetic.',
    'CALL stores the first operand PC, high byte first; RET adds two after popping. Separate byte-level fixtures compare the emulator to compiled control execution.'
]


@lru_cache(maxsize=1)
def pc_circuit():
    return ProgramCounter()


class State:
    def __init__(self, pc=0x1201, flags=0, registers=None, sp=0x9000):
        self.r=dict(zip(REGS,(0x7f,0x61,0xff,0x72,0xff))) if registers is None else dict(registers)
        self.pc=pc; self.sp=sp; self.mar=0; self.f=flags&15
        self.alu=None; self.halted=False; self.memory={}; self.writes={}

    def get(self,address):
        address &= 65535
        return self.memory.get(address,((address*37)^(address>>8)^0xa5)&255)

    def put(self,address,value):
        address &= 65535; value &= 255
        self.memory[address]=value; self.writes[address]=value

    def word(self,address):
        return self.get(address)*256+self.get(address+1)

    def pair(self,name):
        return self.r[name[0]]*256+self.r[name[1]]

    def snapshot(self):
        return dict(registers=dict(self.r),pc=self.pc,sp=self.sp,flags=self.f,halted=self.halted)


def execute(words,alu_words,opcode,state,phase='before',flag_capture='output'):
    """Execute at most 16 latched words, decoding numeric fields independently."""
    if phase not in ('before','after','circuit') or flag_capture not in ('load','output'):
        raise ValueError('Unknown execution profile')
    trace=[]
    for t in range(16):
        address=(opcode<<8)|(t<<4)|(state.f&15); word=words[address]
        trace.append(dict(t=t,address=f'{address:04x}',word=f'{word:04x}',mar=state.mar,alu=state.alu,**state.snapshot()))
        data=bool(word&0x8000)
        old_pc=state.pc
        out=(word>>11)&15 if data else 0
        load=(word>>7)&15 if data else 0
        alu=bool(data and word&64)
        controls=[] if alu else ([(word>>1)&15] if data else [(word>>11)&15,(word>>1)&15])
        if (word&1 or (not data and word&0x07e0) or
                (data and not alu and word&0x20) or out==15 or load==15 or any(c>12 for c in controls)):
            raise ValueError(f'Invalid control word {word:04x}')
        # Transfers sample the old counter, even in a word containing PC_inc.
        if 6 in controls: state.mar=state.pc
        if 7 in controls: state.mar=state.sp

        def functions():
            for c in controls:
                if c==2: state.halted=True
                elif c==3: state.sp=(state.sp+1)&65535
                elif c==4: state.sp=(state.sp-1)&65535
                elif c==5 and phase!='circuit': state.pc=(state.pc+1)&65535
                elif c==8: state.mar=(state.mar+1)&65535
                elif c==9: state.f |= 4
                elif c==10: state.f |= 1
                elif c==11: state.f &= ~4
                elif c==12: state.f &= ~1

        if phase in ('before','circuit'): functions()
        bus=None
        if out:
            name=OPERANDS[out]
            if name in REGS: bus=state.r[name]
            elif name=='MEM': bus=state.get(state.mar)
            elif name=='F': bus=state.f
            elif name=='ALU':
                if state.alu is None: raise ValueError('ALU output before result capture')
                bus=state.alu&255
                if flag_capture=='output': state.f=(state.alu>>8)&15
            else:
                counter,part=name.split('_')
                value=getattr(state,{'PC':'pc','STK':'sp','MAR':'mar'}[counter])
                bus=(value>>8 if part=='H' else value)&255
        if load:
            if bus is None: raise ValueError('Load from undriven bus')
            name=OPERANDS[load]
            if name in REGS: state.r[name]=bus
            elif name=='MEM': state.put(state.mar,bus)
            elif name=='F': state.f=bus&15
            elif name=='ALU':
                if not alu: raise ValueError('ALU load without operation encoding')
                state.alu=alu_words[(((word>>1)&31)<<16)|(state.r['A']<<8)|bus]
                if flag_capture=='load': state.f=(state.alu>>8)&15
            else:
                counter,part=name.split('_'); attr={'PC':'pc','STK':'sp','MAR':'mar'}[counter]
                value=getattr(state,attr)
                if phase!='circuit' or attr!='pc':
                    setattr(state,attr,(value&255)|(bus<<8) if part=='H' else (value&0xff00)|bus)
        if phase=='circuit' and (5 in controls or load in (11,12)):
            state.pc=pc_circuit().step(old_pc,bus or 0,5 in controls,load_low=load==12,load_high=load==11)
        if phase=='after': functions()
        trace[-1].update(bus=bus,post_flags=state.f)
        if 1 in controls or state.halted: return trace
    raise ValueError(f'Opcode {opcode:02x} did not terminate within 16 t-states')


def instruction(name,size,state):
    """Architectural oracle: no control words, compiler encodings or ALU oracle."""
    mnemonic,_,args=name.partition(' ')
    operand_pc=state.pc; immediate=state.word(operand_pc)
    state.pc=(state.pc+size-1)&65535
    flag_mask=255
    def location(arg):
        if arg=='address': return immediate
        if arg=='(address)': return state.word(immediate)
        if arg in ('(BC)','(HL)'): return state.pair(arg[1:-1])
        raise ValueError(arg)
    def value(arg,width=1):
        if arg in REGS: return state.r[arg]
        if arg=='F': return state.f
        if arg in ('BC','HL'): return state.pair(arg)
        if arg=='value': return immediate if width==2 else state.get(operand_pc)
        address=location(arg)
        return state.word(address) if width==2 else state.get(address)
    def store(arg,result,width=1):
        if arg in REGS: state.r[arg]=result&255
        elif arg=='F': state.f=result&15
        elif arg in ('BC','HL'): state.r[arg[0]]=result>>8; state.r[arg[1]]=result&255
        else:
            address=location(arg)
            if width==2: state.put(address,result>>8); state.put(address+1,result)
            else: state.put(address,result)
    def push(byte):
        state.put(state.sp,byte); state.sp=(state.sp-1)&65535
    def pop():
        state.sp=(state.sp+1)&65535; return state.get(state.sp)
    def taken(suffix):
        bit,want=CONDITIONS[suffix]; return (state.f>>bit)&1==want

    if mnemonic=='MOV':
        dst,src=args.split(','); width=2 if dst in ('BC','HL') or src in ('BC','HL') else 1
        result=value(src,width)
        # Assembly-language.md explicitly documents these scratch registers.
        if 'address' in args:
            scratch='BC' if dst=='address' and src=='HL' else 'HL'
            scratch_value=state.word(immediate) if '(address)' in args else immediate
            store(scratch,scratch_value)
        store(dst,result,width)
    elif mnemonic=='SP': state.sp=immediate
    elif mnemonic=='PUSH':
        n=value(args)
        if args in ('BC','HL'): push(n>>8)
        push(n&255)
    elif mnemonic=='POP':
        n=pop()
        if args in ('BC','HL'): n |= pop()<<8
        store(args,n)
    elif mnemonic in ('NOP','HALT'): state.halted=mnemonic=='HALT'
    elif mnemonic in ('FSET','FCLR'):
        bit={'C':1,'Z':4}[args]
        state.f=state.f|bit if mnemonic=='FSET' else state.f&~bit
    elif mnemonic=='JMP' or mnemonic.startswith('J'):
        if mnemonic=='JMP' or taken(mnemonic[1:]):
            store('HL',immediate); state.pc=immediate
    elif mnemonic=='CALL' or mnemonic in ('CC','CZ','CN','CO','CNC','CNZ','CP','CNO'):
        if mnemonic=='CALL' or taken(mnemonic[1:]):
            # Shared ABI: operand PC, with RET adding two.
            push(operand_pc>>8); push(operand_pc&255); store('HL',immediate); state.pc=immediate
    elif mnemonic in ('RET','RC','RZ','RN','RO','RNC','RNZ','RP','RNO'):
        if mnemonic=='RET' or taken(mnemonic[1:]):
            low=pop(); state.pc=((pop()<<8)+low+2)&65535
    else:
        a=state.r['A']; b=value(args); carry=0; overflow=0
        if args in ('address','(address)'):
            address=location(args); state.r['H']=address>>8; state.r['L']=address&255
        signed=lambda x:x if x<128 else x-256
        if mnemonic in ('ADD','ADC','SUB','SBC','CMP','INC','DEC'):
            x,y=a,b; cin=state.f&1 if mnemonic in ('ADC','SBC') else 0
            subtract=mnemonic in ('SUB','SBC','CMP','DEC')
            if mnemonic in ('INC','DEC'): x,y=b,1
            raw=x-y-cin if subtract else x+y+cin
            sr=signed(x)-signed(y)-cin if subtract else signed(x)+signed(y)+cin
            n=raw&255; carry=int(raw<0 or raw>255); overflow=int(not -128<=sr<=127)
        else:
            if mnemonic=='AND': n=a&b
            elif mnemonic=='OR': n=a|b
            elif mnemonic=='XOR': n=a^b
            elif mnemonic=='NOT': n=b^255
            elif mnemonic=='SHL': n=(a<<b)&255; carry=((a<<b)>>8)&1
            elif mnemonic=='SHR': n=a>>b
            elif mnemonic=='ASR': n=(signed(a)>>b)&255
            elif mnemonic=='ROL': k=b%8; n=((a<<k)|(a>>(8-k)))&255
            elif mnemonic=='ROR': k=b%8; n=((a>>k)|(a<<(8-k)))&255
            else: raise ValueError(f'Unsupported instruction {name}')
        state.f=carry|(overflow<<1)|(int(n==0)<<2)|(int(n>=128)<<3)
        if mnemonic!='CMP':
            destination=args if mnemonic in ('INC','DEC') or mnemonic=='NOT' and args in REGS else 'A'
            store(destination,n)
    return flag_mask


def differences(actual,want,mask=255):
    result={}
    for name in REGS:
        if actual.r[name]!=want.r[name]: result[name]=dict(actual=actual.r[name],expected=want.r[name])
    for name in ('pc','sp','halted'):
        if getattr(actual,name)!=getattr(want,name): result[name]=dict(actual=getattr(actual,name),expected=getattr(want,name))
    if (actual.f^want.f)&mask: result['flags']=dict(actual=actual.f,expected=want.f,mask=mask)
    # Compare write addresses as well as final data, catching unintended writes
    # even when they happen to store the pre-existing byte.
    if actual.writes!=want.writes: result['memory']=dict(actual=actual.writes,expected=want.writes)
    return result


def fixture(pc,flags,seed,target):
    state=State(pc,flags,{r:(seed+i*53)&255 for i,r in enumerate(REGS)})
    state.memory[pc]=target>>8; state.memory[(pc+1)&65535]=target&255
    state.memory[0x9001]=0xfe; state.memory[0x9002]=0x34
    return state


def audit(words,alu_words,spec):
    profiles=[]; all_examples=[]
    # Operand PC values exercise opcode/operand fetch wrap and the PC_L carry
    # ambiguity at operand PC xxFE (PC is xxFF at target-low capture).
    vectors=[(0x1201,0x00,0x4567),(0x12fe,0x7f,0x45ff),(0x12ff,0x80,0x4500),
             (0xffff,0xff,0xffff),(0x0000,0x01,0x0000),(0x3401,0x55,0x8000)]
    for phase in ('before','after','circuit'):
        for flag_capture in ('load','output'):
            rows=[]; examples=[]; fields=Counter(); failures=0
            for opcode,ins in spec['instructions'].items():
                failed=0; row_fields=Counter(); row_examples={}
                for flags in range(16):
                    for pc,seed,target in vectors:
                        initial=fixture(pc,flags,seed,target); actual=deepcopy(initial); want=deepcopy(initial)
                        mask=instruction(ins['name'],ins['size'],want)
                        trace=execute(words,alu_words,opcode,actual,phase,flag_capture)
                        diff=differences(actual,want,mask)
                        if diff:
                            failed+=1; fields.update(diff.keys()); row_fields.update(diff.keys())
                            signature=tuple(diff)
                            if signature not in row_examples:
                                row_examples[signature]=dict(opcode=f'{opcode:02x}',instruction=ins['name'],initial=initial.snapshot(),
                                    initial_memory=initial.memory,operand=target,differences=diff,trace=trace,
                                    actual=actual.snapshot(),expected=want.snapshot())
                failures+=failed
                rows.append(dict(opcode=f'{opcode:02x}',instruction=ins['name'],cases=96,failed=failed,fields=dict(row_fields)))
                examples.extend(row_examples.values())
            # Nested calls use the same stack ABI at both ends; target PC and
            # return PC are checked independently at each step.
            roundtrips=[]
            for pc,seed,target in vectors:
                state=fixture(pc,0,seed,target); initial_sp=state.sp
                execute(words,alu_words,0xcc,state,phase,flag_capture)
                outer_target=state.pc
                nested_pc=(target+1)&65535
                state.pc=(state.pc+1)&65535  # Ideal fetch of nested CALL.
                state.memory[state.pc]=0x67; state.memory[(state.pc+1)&65535]=0x89
                execute(words,alu_words,0xcc,state,phase,flag_capture)
                inner_target=state.pc
                execute(words,alu_words,0xd5,state,phase,flag_capture); inner_return=state.pc
                execute(words,alu_words,0xd5,state,phase,flag_capture)
                ok=(outer_target==target and inner_target==0x6789 and inner_return==(nested_pc+2)&65535
                    and state.pc==(pc+2)&65535 and state.sp==initial_sp)
                roundtrips.append(dict(operand_pc=pc,target=target,outer_target=outer_target,inner_target=inner_target,
                                       inner_return=inner_return,outer_return=state.pc,final_sp=state.sp,passed=ok))
            profiles.append(dict(phase=phase,flag_capture=flag_capture,cases=len(rows)*96,failed=failures,
                                 mismatch_fields=dict(fields),rows=rows,roundtrips=roundtrips))
            all_examples.append(dict(phase=phase,flag_capture=flag_capture,examples=examples))
    return dict(assumptions=ASSUMPTIONS,profiles=profiles),all_examples


def control_flow(words):
    """All targets and all operand-PC low bytes under extracted PC semantics."""
    checked=0; failures=0; examples=[]
    def check(op,pc,target,flags):
        nonlocal checked,failures
        state=fixture(pc,flags,0x7f,target)
        name='JMP' if op==0xc3 else 'CALL' if op==0xcc else None
        if name is None:
            suffix=list(CONDITIONS)[(op-0xc4) if op<=0xcb else (op-0xcd)]
            bit,want=CONDITIONS[suffix]; taken=(flags>>bit)&1==want
        else: taken=True
        execute(words,{},op,state,'circuit')
        expected_pc=target if taken else (pc+2)&65535
        call=op>=0xcc and taken
        expected_sp=0x8ffe if call else 0x9000
        checked+=1
        good=state.pc==expected_pc and state.sp==expected_sp
        if call:
            good &= state.writes=={0x9000:pc>>8,0x8fff:pc&255}
        else: good &= not state.writes
        if not good:
            failures+=1
            if len(examples)<8: examples.append(dict(op=op,operand_pc=pc,target=target,flags=flags,
                actual_pc=state.pc,expected_pc=expected_pc,actual_sp=state.sp,expected_sp=expected_sp))
    # This opcode location previously caused an old-low-byte carry into PC_H.
    for target in range(65536):
        for op in (0xc3,0xcc): check(op,0x12fe,target,0)
    targets=(0,1,0xff,0x100,0x7fff,0x8000,0xff00,0xffff)
    for low in range(256):
        for flags in range(16):
            for op in range(0xc3,0xd5): check(op,0xff00|low,targets[low%len(targets)],flags)
    # Reinstate the original combined load+increment to qualify this checker.
    mutant=list(words)
    for op,t in ((0xc3,5),(0xcc,10)):
        for flags in range(16): mutant[(op<<8)|(t<<4)|flags] |= 10
    caught=[]
    for op in (0xc3,0xcc):
        state=fixture(0x12fe,0,0x7f,0x4567)
        execute(mutant,{},op,state,'circuit')
        caught.append(state.pc==0x4667)
    result=dict(cases=checked,failures=failures,examples=examples,restored_increment_mutations_detected=caught,
                scope='JMP/CALL every 16-bit target at operand PC 12FE; all 18 jump/call opcodes at all 256 operand-PC low bytes and 16 flags; flat memory, ideal fetch, extracted Logisim PC updates.')
    write_json(BUILD/'microcode/control-flow.json',result)
    return evidence('control-flow','Compiled jump/call boundary coverage','pass' if not failures and all(caught) else 'fail',
                    f'{checked:,} target/flag/PC cases; {failures:,} failures; original PC_inc defect detected in both mutation checks.',
                    artifacts=['microcode/control-flow.json'],limitation=result['scope'])


def run():
    from .abi import run as abi_run
    folder=BUILD/'microcode'; folder.mkdir(parents=True,exist_ok=True)
    rom=folder/'microcode.rom'
    words=struct.unpack('<65536H',rom.read_bytes())
    banks=[BUILD/'alu'/f'alu{i}.rom' for i in range(8)]
    alu_words=struct.unpack('<2097152H',b''.join(p.read_bytes() for p in banks))
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    result,examples=audit(words,alu_words,spec)
    result['input_hashes']={str(p.relative_to(ROOT)):digest(p) for p in (rom,*banks)}
    write_json(folder/'execution.json',result); write_json(folder/'execution-traces.json',examples)
    total=sum(p['cases'] for p in result['profiles'])
    summaries=[dict(phase=p['phase'],flag_capture=p['flag_capture'],cases=p['cases'],failed=p['failed'],
                    pc_mismatches=p['mismatch_fields'].get('pc',0),roundtrips_passed=sum(r['passed'] for r in p['roundtrips']),
                    roundtrips=len(p['roundtrips'])) for p in result['profiles']]
    failed=any(p['failed'] or not all(r['passed'] for r in p['roundtrips']) for p in result['profiles'])
    execution=evidence('control','Compiled control-word execution','fail' if failed else 'limited',
                    f'{total:,} cases across 227 opcodes and six phase/flag profiles; {sum(p["failed"] for p in result["profiles"]):,} architectural disagreements.',
                    profiles=summaries,
                    artifacts=['microcode/execution.json','microcode/execution-traces.json'],
                    limitation='Untimed model with explicit scratch-register contract and unresolved physical function/flag timing; flat memory excludes physical IO and ROM protection.')
    return [execution,control_flow(words),abi_run(words)]

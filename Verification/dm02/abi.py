"""Byte-level emulator/control-ROM ABI comparison; flat memory boundary."""
import json
from .common import BUILD,VROOT,command,evidence,write_json
from .control import State,execute


def run(words):
    folder=BUILD/'microcode/abi';folder.mkdir(parents=True,exist_ok=True)
    fixtures=[]
    def case(op,state):
        # The controller begins after ideal opcode fetch; the emulator fetches.
        pc=(state.pc-1)&65535;state.memory[pc]=op
        initial=dict(pc=pc,sp=state.sp,flags=state.f,registers=dict(state.r),memory=sorted(state.memory.items()))
        execute(words,[],op,state,phase='circuit',flag_capture='output')
        fixtures.append(dict(id=f'{op:02x}-{len(fixtures)}',**initial,
                             expected=dict(state.snapshot(),writes=sorted(state.writes.items()))))
    call_positions=[(pc,0x9000) for pc in (0x1201,0x12ff,0x1300,0xffff,0)]+[(0x1201,sp) for sp in (0,1,0xffff)]
    for op in range(0xcc,0xd5):
        for flags in range(16):
            for pc,sp in call_positions:
                state=State(pc=pc,flags=flags,sp=sp)
                state.memory[pc]=0x45;state.memory[(pc+1)&65535]=0x67
                case(op,state)
    for op in range(0xd5,0xde):
        for flags in range(16):
            for saved in (0,1,0xff,0x100,0x12fe,0x12ff,0xfffd,0xfffe,0xffff):
                for sp in (0x8ffe,0xfffe,0xffff,0):
                    state=State(pc=0x2001,flags=flags,sp=sp)
                    state.memory[(sp+1)&65535]=saved&255;state.memory[(sp+2)&65535]=saved>>8
                    case(op,state)
    for sp in (0x8fff,0xfffe,0xffff,0):
        for byte in range(256):
            state=State(pc=0x2001,flags=15,sp=sp);state.memory[(sp+1)&65535]=byte
            case(0x52,state)
        for flags in range(16): case(0x4a,State(pc=0x2001,flags=flags,sp=sp))
    fixture=folder/'fixtures.json';write_json(fixture,fixtures)
    rows=[]
    for mutation in ('none','old-flags','old-call-return'):
        output=folder/(mutation+'.json')
        code,log=command(['node',VROOT/'emulator-abi.cjs',fixture,output,mutation])
        if code: raise RuntimeError('Emulator ABI comparison failed to execute: '+log)
        row=json.loads(output.read_text())
        if row['cases']!=len(fixtures): raise ValueError('ABI comparison omitted fixtures')
        rows.append(row)
    passed=rows[0]['failed']==0 and all(r['failed']>0 for r in rows[1:])
    result=dict(cases=len(fixtures),runs=rows,
                scope='Real emulator vs compiled control words and extracted Logisim PC. '
                      'PUSH/POP F, all call/return conditions, raw stack bytes and 16-bit wrapping. '
                      'Flat writable memory, ideal opcode fetch, no IO/protection/timing; overlapping CALL code/stack storage is excluded.')
    write_json(folder/'summary.json',result)
    return evidence('emulator-abi','Emulator/control-ROM stack ABI','pass' if passed else 'fail',
                    f'{len(fixtures):,} byte-level cases; {rows[0]["failed"]} mismatches; both historical ABI mutations detected.',
                    artifacts=['microcode/abi/summary.json','microcode/abi/fixtures.json'],limitation=result['scope'])

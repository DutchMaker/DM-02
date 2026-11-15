"""Cross-check the controller, documentation, emulator and mathematical ALU IDs."""
import re
from .common import ROOT, BUILD, evidence, write_json

ALU_IDS=['ZERO','A','B','-A','-B','A+1','B+1','A-1','B-1','A+B','A+B+1',
         'A-B','A-B_S','B-A','A-B-1','B-A-1','A*B_L','A*B_H','A/B','A%B',
         'A<<B','A>>B_L','A>>B_A','A_ROL_B','A_ROR_B','A_AND_B','A_OR_B',
         'A_XOR_B','NOT_A','NOT_B','A+B_BCD','A-B_BCD']


def unique(entries):
    result={}
    for key,value in entries:
        if key in result: raise ValueError(f'Duplicate encoding: {key}')
        result[key]=value
    return result


def run():
    source=(ROOT/'Code/Microcode/microcode.src').read_text()
    alu=source.split('.alu\n',1)[1].split('.end',1)[0]
    controller=unique((int(bits,2),name.strip()) for bits,name in re.findall(r'^([01]{5}):(.+)$',alu,re.M))
    docs=(ROOT/'Documentation/ALU-and-flags.md').read_text()
    documented=unique((int(bits,2),name) for name,bits in re.findall(r'\|\s*ALU_(\S+)\s*\|\s*`([01]{5})`',docs))
    rows=[dict(op=i,oracle=name,controller=controller.get(i),documentation=documented.get(i),
               status='pass' if name==controller.get(i)==documented.get(i) else 'fail') for i,name in enumerate(ALU_IDS)]
    instructions=source.split('.instructions\n',1)[1].split('.end',1)[0]
    micro=unique((int(op,16),(int(size),name.strip())) for op,size,name in re.findall(r'^([0-9A-F]{2}):(\d+):(.+)$',instructions,re.M))
    js=(ROOT/'Code/Emulator/js/instructions.js').read_text()
    emulator=unique((int(op,16),(int(size),name.strip())) for op,size,name in re.findall(r'\[\s*0x([0-9A-Fa-f]+)\s*,\s*(\d+)\s*,\s*"([^"]+)"',js))
    differences=[dict(op=op,controller=micro.get(op),emulator=emulator.get(op)) for op in sorted(micro.keys()|emulator.keys()) if micro.get(op)!=emulator.get(op)]
    complete=set(micro)==set(emulator)==set(range(227)) and set(controller)==set(documented)==set(range(32))
    result=dict(complete=complete,alu=rows,instruction_count=len(micro),instruction_differences=differences)
    write_json(BUILD/'encoding.json',result)
    ok=complete and not differences and all(r['status']=='pass' for r in rows)
    return evidence('encoding','Opcode encoding consistency','pass' if ok else 'fail',
                    '32 ALU definitions checked across documentation, controller and oracle; 227 instruction definitions compared.',
                    rows=rows,artifacts=['encoding.json'],limitation='Definition consistency only; does not prove that all instructions execute correctly in hardware.')

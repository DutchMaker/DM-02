"""Generate FD1 candidate sheets using normal repository symbols and parsing.

Staged under build while the full verification run holds source inputs fixed.
The AL1 slot name identifies the connector contract; its circuit is AL2.
"""
from pathlib import Path
import re
from dm02.common import ROOT,BUILD
from dm02.legacy import read_sheet
from dm02.clock import Clock
from dm02.controller_hardware import Circuit as Word
from dm02.sequencer import Circuit as Sequencer
from dm02.pc_hardware import Circuit as Pc
from dm02.alu_flash import Circuit as Flash
from dm02.register_hardware import Circuit as Registers
from dm02.address_hardware import Circuit as Address
from dm02.memory_hardware import Circuit as Memory
from designs.address_candidate import Board

FACTORIES={'C1':Clock,'CW1':Word,'SQ1':Sequencer,'PC1':Pc,'AL1':Flash,'RG1':Registers,
           'SP1':lambda sheet=None:Address('stack',sheet),'MA1':lambda sheet=None:Address('mar',sheet),'ME1':Memory}
RESET_PINS={'C1':3,'CW1':5,'SQ1':7,'PC1':4,'AL1':5,'RG1':4,'SP1':5,'MA1':5,'ME1':6}
LEAVES={0:['SQ1','ME1'],1:['CW1','SQ1','AL1','SP1','MA1'],2:['SQ1','ME1'],
        3:['SQ1','PC1','AL1','RG1','SP1','MA1','ME1']}
RECEIVERS=['AL1','PC1','SQ1','RG1','SP1','MA1','ME1']
SOURCES={'AL1':{'U13':1,'U14':6,'U15':7},'PC1':{'U5':12,'U6':11},
         'RG1':{'U7':2,'U12':3,'U17':4,'U22':5},'SP1':{'U20':14,'U22':13},
         'MA1':{'U40':9,'U41':8},'ME1':{'U9':10}}
INPUT_PINS=[2,4,6,8,17,15,13,11]
OUTPUT_PINS=[18,16,14,12,3,5,7,9]


def relabel(text,sheet,changes):
    lines=text.splitlines()
    for ref,pin,label in changes:
        points=[p for c in sheet['components'] if c['ref']==ref for p in c['pins'] if p['number']==str(pin)]
        assert len(points)==1,(ref,pin);point=points[0];matches=[]
        for i,line in enumerate(lines):
            f=line.split()
            if f[:2]==['Text','Label'] and tuple(map(int,f[2:4]))==(point['x'],point['y']):matches.append(i+1)
        assert len(matches)==1,(ref,pin,matches)
        lines[matches[0]]=label
    return '\n'.join(lines)+'\n'


def append(text,board,offset):
    extra=board.text();extra=extra[extra.index('$Comp'):extra.index('$EndSCHEMATC')]
    def move(line):
        f=line.split()
        if not f:return line
        if f[0]=='P':return f'P {int(f[1])+offset} {f[2]}'
        if f[:2] in (['Text','Label'],['NoConn','~']):f[2]=str(int(f[2])+offset);return ' '.join(f)
        if f[0]=='F':return re.sub(r' H (\d+) ',lambda m:f' H {int(m[1])+offset} ',line)
        if len(f)==3 and all(re.fullmatch(r'-?\d+',v) for v in f):return f'\t{f[0]} {int(f[1])+offset} {f[2]}'
        return line
    extra='\n'.join(move(line) for line in extra.splitlines())+'\n'
    text=re.sub(r'\$Descr \S+ \d+ \d+','$Descr User 90000 46811',text,count=1)
    return text.replace('$EndSCHEMATC',extra+'$EndSCHEMATC')


def reset_board(name,c):
    text=(ROOT/c.sheet['source']).read_text();net=c.nets[c.nodes['J1',str(RESET_PINS[name])]]
    pins={(p['ref'],x['number']):(p,x) for p in c.sheet['components'] for x in p['pins']}
    targets=[tuple(n) for n in net['nodes'] if n[0].startswith('U') and pins[tuple(n)][1]['kind']=='I']
    groups=[targets[i:i+4] for i in range(0,len(targets),4)];roots=(len(groups)+3)//4
    assert roots>0 and roots+len(groups)<=8 and len(net['labels'])==1
    changes=[(ref,pin,f'RD_LEAF{i}') for i,group in enumerate(groups) for ref,pin in group]
    d=Board('FD1 local reset','RD1');d.ref=899
    ins=[net['labels'][0]]*roots+[f'RD_ROOT{i//4}' for i in range(len(groups))]
    outs=[f'RD_ROOT{i}' for i in range(roots)]+[f'RD_LEAF{i}' for i in range(len(groups))]
    d.buf(ins+['GND']*(8-len(ins)),outs+[None]*(8-len(outs)))
    d.part('Device:C','C900','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    return append(relabel(text,c.sheet,changes),d,34000)


def private_sources(name,c):
    text=(ROOT/c.sheet['source']).read_text();changes=[];d=Board('FD1 private source links','DF2')
    for ref,source in SOURCES[name].items():
        assert c.parts['devices'][c.components[ref][0]['value']]['function']=='244'
        for bit,pin in enumerate(OUTPUT_PINS):
            assert f'DATA{bit}' in c.nets[c.nodes[ref,str(pin)]]['labels']
            changes.append((ref,pin,f'DF_SOURCE{source}_{bit}'))
        changes.extend([(ref,1,'GND'),(ref,19,'GND')])
        d.connector(f'J{900+source}',['5V','GND']+[f'DF_SOURCE{source}_{b}' for b in range(8)])
    return append(relabel(text,c.sheet,changes),d,48000)


def controller_export(c):
    d=Board('FD1 buffered selector export','DF2');d.ref=900
    d.buf([f'WORD{b}' for b in range(11,16)]+['ACTIVE','GND','GND'],[f'DF_CONTROL{b}' for b in range(6)]+[None]*2)
    d.part('Device:C','C901','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    d.connector('J900',['5V','GND']+[f'DF_CONTROL{b}' for b in range(6)])
    return append((ROOT/c.sheet['source']).read_text(),d,48000)


def clock_tree():
    d=Board('DM-02 phase distribution candidate','CD1',[
        'Two AHCT244 stages from each phase root to dedicated board links.',
        'Maximum allocated branch delay 19 ns; interval review uses a 4 MHz target.',
        'Exact oscillator, physical routing/load and slew remain unqualified.'])
    roots=[];ins=[];outs=[]
    for phase,names in LEAVES.items():
        roots.extend((f'PH{phase}',f'ROOT{phase}_{i}') for i in range((len(names)+3)//4))
        for i,name in enumerate(names):ins.append(f'ROOT{phase}_{i//4}');outs.append(f'{name}_PH{phase}')
    d.buf([a for a,b in roots]+['GND']*(8-len(roots)),[b for a,b in roots]+[None]*(8-len(roots)))
    for i in range(2):d.buf(ins[8*i:8*i+8],outs[8*i:8*i+8])
    d.connector('J1',['5V','GND']+[f'PH{i}' for i in range(4)])
    d.connector('J2',['5V','GND']+outs);return d.finish()


def reset_tree():
    d=Board('DM-02 reset distribution candidate','RD1',[
        'Qualified fast-edged reset input; supervisor and Schmitt conditioning external.',
        'Two central and two local stages; at most four receivers per local leaf.',
        'Reset removal, arbitrary abort, supply ramps and interrupted writes unqualified.'])
    d.buf(['RESET_n']*3+['GND']*5,[f'ROOT{i}' for i in range(3)]+[None]*5);names=list(FACTORIES)
    for start in (0,8):
        ins=[f'ROOT{i//3}' for i in range(start,min(start+8,9))];outs=[names[i]+'_RESET_n' for i in range(start,min(start+8,9))]
        d.buf(ins+['GND']*(8-len(ins)),outs+[None]*(8-len(outs)))
    d.connector('J1',['5V','GND','RESET_n']);d.connector('J2',['5V','GND']+[name+'_RESET_n' for name in names])
    return d.finish()


def selector():
    d=Board('DM-02 physical DATA selector','DF2',[
        'Buffered CW WORD11..15 and ACTIVE select source 1..14 or idle zero.',
        'FETCH1 overrides execute selection with memory source 10.',
        'Private continuously driven source links; physical loading still conditional.'])
    d.gate('08','ACTIVE','FORMAT','ENABLE')
    d.mux('ENABLE',['GND']*4,[f'WORD{b}' for b in range(4)],[f'EXEC{b}' for b in range(4)])
    d.mux('FETCH1',[f'EXEC{b}' for b in range(4)],['GND','5V','GND','5V'],[f'SELECT{b}' for b in range(4)])
    d.connector('J1',['5V','GND']+[f'WORD{b}' for b in range(4)]+['FORMAT','ACTIVE','FETCH1'])
    d.connector('J2',['5V','GND']+[f'SELECT{b}' for b in range(4)]);return d.finish()


def fabric():
    d=Board('DM-02 private DATA fabric','DF2',[
        'Four-level 16:1 mux; private continuous sources 1..14, selectors 0/15 zero.',
        'Two-stage fanout gives each receiving board a private DATA link.',
        'FD1 connects this fabric to AL2 and six other receive branches.'])
    bits=lambda name:[f'{name}{b}' for b in range(8)]
    selections=[(f'SELECT{level}',f'S{level}_{group}') for level,count in enumerate((4,2,1,1)) for group in range(count)]
    d.buf([a for a,b in selections],[b for a,b in selections])
    stage=[['GND']*8]+[bits(f'SOURCE{s}_') for s in range(1,15)]+[['GND']*8]
    for level in range(4):
        following=[]
        for pair in range(len(stage)//2):
            out=bits(f'MUX{level}_{pair}_');following.append(out)
            for half in range(2):
                start=half*4;branch=(pair*2+half)//4
                d.mux(f'S{level}_{branch}',stage[2*pair][start:start+4],stage[2*pair+1][start:start+4],out[start:start+4])
        stage=following
    for group in range(2):d.buf(stage[0],bits(f'ROOT{group}_'))
    for i,name in enumerate(RECEIVERS):d.buf(bits(f'ROOT{i//4}_'),bits(name+'_DATA'))
    for s in range(1,15):d.connector(f'J{s}',['5V','GND']+bits(f'SOURCE{s}_'))
    for i,name in enumerate(RECEIVERS):d.connector(f'J{21+i}',['5V','GND']+bits(name+'_DATA'))
    d.connector('J30',['5V','GND']+[f'SELECT{b}' for b in range(4)]);return d.finish()


def generate(dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);outputs={}
    for name,factory in FACTORIES.items():
        path=dest/f'Reset-{name}.sch';path.write_text(reset_board(name,factory()));c=factory(read_sheet(path))
        if name in SOURCES:
            path=dest/f'Data-{name}.sch';path.write_text(private_sources(name,c))
        elif name=='CW1':
            path=dest/'Data-CW1.sch';path.write_text(controller_export(c))
        outputs[name]=path
    for name,filename,draw in [('CD1','Clock-Distribution.sch',clock_tree),('RD1','Reset-Distribution.sch',reset_tree),
                               ('DF1','Data-Fabric.sch',fabric),('SEL','Data-Selector.sch',selector)]:
        path=dest/filename;path.write_text(draw());outputs[name]=path
    return outputs


if __name__=='__main__':
    print('\n'.join(f'{name}: {path.relative_to(ROOT)}' for name,path in generate(BUILD/'integration-staging/circuits').items()))

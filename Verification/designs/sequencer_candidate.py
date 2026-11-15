"""Draw SQ1 fetch, instruction storage, t-state and complete-cycle HALT interface."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from dm02.legacy import library

DEST=ROOT/'Circuits/KiCad/Controller/candidates/Sequencer.sch'


def drawing():
    lines=['EESchema Schematic File Version 4','EELAYER 29 0','EELAYER END',
           '$Descr A1 33110 23386','Sheet 1 1','Title "DM-02 fetch/sequencer candidate"',
           'Date "2026-11-14"','Rev "SQ1"','Comp "DM-02"',
           'Comment1 "PH3 retains end/HALT; PH0 advances address; PH1 freezes mode before PH2."',
           'Comment2 "C1 + CW1 + PC1 interface. Resume is debounced, idle-only; STEP connects directly to C1."',
           'Comment3 "Documentation/Sequencer.md; Verification/sequencer-parts.json"','Comment4 ""','$EndDescr']
    serial=0;parts=[]
    def part(lib,ref,value,unit,nets,footprint):
        nonlocal serial
        serial+=1;x=2000+((serial-1)%10)*3100;y=1900+((serial-1)//10)*2200
        pins=[p for p in library(lib.split(':')[0])[lib.split(':')[1]]['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,1)]
        if set(nets)!={p['number'] for p in pins}:raise ValueError('Incomplete '+ref)
        parts.append((lib,ref,value,unit,nets,footprint,x,y,pins))
    dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    so=lambda n:f'Package_SO:SOIC-{n}_3.9x{9.9 if n==16 else 8.7}mm_P1.27mm'
    def reg(ref,clock,reset,ds,qs,nqs=None):
        nets={'1':reset,'9':clock,'16':'5V','8':'GND'}
        for i,(d,q,nq) in enumerate([(4,2,3),(5,7,6),(12,10,11),(13,15,14)]):
            nets.update({str(d):ds[i],str(q):qs[i],str(nq):nqs[i] if nqs else None})
        part('74xx:74LS175',ref,'CD74AC175M96',1,nets,so(16))
    # Mode coding: 00 fetch address, 01 fetch opcode, 10 execute.
    reg('U1','CAPTURE','RESET_n',['NEXT_F1','NEXT_E','CONTINUE','GND'],['STAGE_F1','STAGE_E','STAGE_CONT',None])
    reg('U2','ADVANCE','RESET_n',['STAGE_F1','STAGE_E','GND','GND'],['STATE_F1','STATE_E',None,None])
    reg('U3','MODE_CLOCK','RESET_n',['STATE_F1','STATE_E','GND','GND'],['MODE_F1','MODE_E',None,None],['MODE_F1_n','MODE_E_n',None,None])
    part('74xx:74LS161','U4','CD74HCT161M96',1,
         {'1':'RESET_n','2':'ADVANCE','3':'GND','4':'GND','5':'GND','6':'GND','7':'5V','8':'GND',
          '9':'STAGE_CONT','10':'5V','11':'T3','12':'T2','13':'T1','14':'T0','15':None,'16':'5V'},so(16))
    reg('U5','CAPTURE','HALT_RESET_n',['HALT_NEXT','GND','GND','GND'],['HALTED',None,None,None],['HALTED_n',None,None,None])
    nets={'1':'GND','10':'GND','11':'CAPTURE','20':'5V'}
    nets.update({str(2+b):f'IR_D{b}' for b in range(8)})
    nets.update({str(19-b):f'OP{b}' for b in range(8)})
    part('74xx:74HCT574','U6','SN74HCT574N',1,nets,dip(20))
    def buffer(ref,uses):
        nets={'1':'GND','19':'GND','20':'5V','10':'GND'}
        for i,(a,b) in enumerate(zip([2,4,6,8,17,15,13,11],[18,16,14,12,3,5,7,9])):
            src,dst=uses[i] if i<len(uses) else ('GND',None);nets[str(a)]=src;nets[str(b)]=dst
        part('74xx:74HCT244',ref,'SN74AHCT244N',1,nets,dip(20))
    buffer('U7',[('PH0','ADVANCE'),('PH1','MODE_CLOCK'),('PH3','CAPTURE'),
                 ('MODE_F1','IR_SELECT_LO'),('MODE_F1','IR_SELECT_HI'),
                 ('MODE_F1_n','IR_KEEP_LO'),('MODE_F1_n','IR_KEEP_HI'),('CW_VALID','VALID')])
    gates={'08':[],'00':[],'04':[]}
    def gate(kind,*nets):gates[kind].append(nets)
    # No state advance during the initial invalid CW1 word cycle.
    gate('08','MODE_F1_n','MODE_E_n','MODE_F0')
    gate('08','MODE_F0','VALID','NEXT_F1')
    gate('08','MODE_F1','VALID','F1_VALID')
    gate('08','MODE_E','VALID','E_VALID')
    gate('00','CW_END_n','CW_HALT_n','END')
    gate('04','END','END_n')
    gate('08','E_VALID','END_n','CONTINUE')
    gate('04','F1_VALID','F1_VALID_n')
    gate('04','CONTINUE','CONTINUE_n')
    gate('00','F1_VALID_n','CONTINUE_n','NEXT_E')
    gate('04','CW_END','CW_END_n');gate('04','CW_HALT','CW_HALT_n')
    gate('00','HALTED_n','CW_HALT_n','HALT_NEXT')
    gate('04','RESUME','RESUME_n');gate('08','RESET_n','RESUME_n','HALT_RESET_n')
    gate('08','RUN','HALTED_n','REQUEST')
    gate('08','PH2','RESET_n','WINDOW')
    gate('08','NEXT_F1','WINDOW','FETCH0')
    gate('08','F1_VALID','WINDOW','FETCH1')
    gate('08','MODE_E','PH2','CW_PH2')
    gate('04','FETCH0','FETCH0_n');gate('04','FETCH1','FETCH1_n')
    gate('08','CW_PC_ADDRESS_n','FETCH0_n','PC_ADDRESS_n')
    gate('08','CW_MEM_n','FETCH1_n','MEM_n')
    gate('04','CW_INC','CW_INC_n');gate('00','CW_INC_n','FETCH1_n','PC_INC')
    # IR clock is never gated: a NAND mux selects the data bus or stored opcode.
    for b in range(8):
        group='LO' if b<4 else 'HI'
        gate('00',f'DATA{b}',f'IR_SELECT_{group}',f'IR_BUS{b}_n')
        gate('00',f'OP{b}',f'IR_KEEP_{group}',f'IR_OLD{b}_n')
        gate('00',f'IR_BUS{b}_n',f'IR_OLD{b}_n',f'IR_D{b}')
    ref=8
    for kind,uses in gates.items():
        width=6 if kind=='04' else 4
        value={'08':'SN74AHCT08DR','00':'SN74AHCT00DR','04':'SN74AHCT04N'}[kind]
        lib='74xx:74HCT04' if kind=='04' else '74xx:74LS'+kind
        for start in range(0,len(uses),width):
            name=f'U{ref}';ref+=1
            for unit in range(1,width+1):
                use=uses[start+unit-1] if start+unit<=len(uses) else (('GND',None) if kind=='04' else ('GND','GND',None))
                pins=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[unit-1]
                part(lib,name,value,unit,{str(p):n for p,n in zip(pins,use)},dip(14) if kind=='04' else so(14))
            part(lib,name,value,width+1,{'14':'5V','7':'GND'},dip(14) if kind=='04' else so(14))
    connectors=[['5V','GND','PH0','PH1','PH2','PH3','RESET_n','RUN','RESUME','CW_VALID',
                 'CW_END','CW_HALT','CW_INC','CW_PC_ADDRESS_n','CW_MEM_n'],
                ['5V','GND']+[f'DATA{b}' for b in range(8)],
                ['5V','GND']+[f'T{b}' for b in range(4)]+[f'OP{b}' for b in range(8)],
                ['5V','GND','CW_PH2','REQUEST','HALTED','FETCH0','FETCH1','MODE_E','PC_INC','PC_ADDRESS_n','MEM_n']]
    for i,names in enumerate(connectors,1):
        count=len(names);part(f'Connector_Generic:Conn_01x{count:02}',f'J{i}',f'J{i}',1,
                             {str(p):n for p,n in enumerate(names,1)},f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')
    for i in range(1,ref):part('Device:C',f'C{i}','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    for i,(lib,ref,value,unit,nets,footprint,x,y,pins) in enumerate(parts):
        lines.extend(['$Comp',f'L {lib} {ref}',f'U {unit} 1 {0x69D00000+i:08X}',f'P {x} {y}',
                      f'F 0 "{ref}" H {x+100} {y+300} 50 0000 L CNN',f'F 1 "{value}" H {x+100} {y+200} 50 0000 L CNN',
                      f'F 2 "{footprint}" H {x} {y} 50 0001 C CNN',f'\t{unit} {x} {y}','\t1 0 0 -1','$EndComp'])
        for p in pins:
            px,py=x+p['x'],y-p['y'];net=nets[p['number']]
            if net is None:lines.append(f'NoConn ~ {px} {py}')
            else:lines.extend([f'Text Label {px} {py} 0 39 ~ 0',net])
    lines.append('$EndSCHEMATC');return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('Sequencer drawing differs')
    print(DEST)

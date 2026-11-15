"""Draw the discrete PC candidate; verification reads the resulting KiCad sheet."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from dm02.legacy import library

DEST=ROOT/'Circuits/KiCad/Registers-StackPointer/candidates/Program-Counter.sch'


def drawing():
    lines=['EESchema Schematic File Version 4','EELAYER 29 0','EELAYER END',
           '$Descr A2 23386 16535','Sheet 1 1','Title "DM-02 program counter candidate"',
           'Date "2026-11-14"','Rev "PC1"','Comp "DM-02"',
           'Comment1 "Four HCT161 counters; falling-edge carry staging; PH3 rising-edge updates"',
           'Comment2 "Reset inhibits data/address drivers. Controller and backplane integration pending."',
           'Comment3 "Verification/pc-parts.json; Documentation/Program-counter.md"','Comment4 ""','$EndDescr']
    serial=0
    def part(lib,ref,value,unit,x,y,nets,footprint):
        nonlocal serial
        serial+=1
        lines.extend(['$Comp',f'L {lib} {ref}',f'U {unit} 1 {0x69B00000+serial:08X}',f'P {x} {y}',
                      f'F 0 "{ref}" H {x+100} {y+300} 50 0000 L CNN',
                      f'F 1 "{value}" H {x+100} {y+200} 50 0000 L CNN',
                      f'F 2 "{footprint}" H {x} {y} 50 0001 C CNN',f'\t{unit} {x} {y}',
                      '\t1 0 0 -1','$EndComp'])
        ns,name=lib.split(':');pins=[p for p in library(ns)[name]['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,1)]
        if set(nets)!={p['number'] for p in pins}: raise ValueError('Incomplete pin assignment: '+ref)
        for p in pins:
            px,py=x+p['x'],y-p['y'];net=nets[p['number']]
            if net is None:lines.append(f'NoConn ~ {px} {py}')
            else:lines.extend([f'Text Label {px} {py} 0 39 ~ 0',net])
    dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    so16='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'
    def note(x,y,text):lines.extend([f'Text Notes {x} {y} 0 60 ~ 0',text])
    note(900,600,'PC1: pin-derived module candidate, not a complete controller or qualified PCB')
    for nibble in range(4):
        nets={'1':'~RESET','2':'PC_CLOCK','7':'PC_inc' if not nibble else f'ENABLE{nibble}',
              '8':'GND','9':'~PC_L_load' if nibble<2 else '~PC_H_load','10':'5V','15':f'TERM{nibble}','16':'5V'}
        nets.update({str(3+b):f'DATA{b+4*(nibble%2)}' for b in range(4)})
        nets.update({str(14-b):f'PC{b+4*nibble}' for b in range(4)})
        part('74xx:74LS161',f'U{nibble+1}','CD74HCT161M96',1,6000+3800*nibble,2200,nets,so16)
    note(5000,4200,'TC is local nibble terminal count: CET tied high; staged prefix carry drives CEP with PC_inc')
    buffer_inputs=[2,4,6,8,17,15,13,11];buffer_outputs=[18,16,14,12,3,5,7,9]
    def buffer(ref,x,y,ins,outs,oe0,oe1):
        nets={'1':oe0,'19':oe1,'20':'5V','10':'GND'}
        nets.update({str(p):n for p,n in zip(buffer_inputs,ins)})
        nets.update({str(p):n for p,n in zip(buffer_outputs,outs)})
        part('74xx:74HCT244',ref,'SN74AHCT244N',1,x,y,nets,dip(20))
    for ref,base,dest,oe,x,y in [('U5',0,'DATA','LOW_OE_n',6000,5500),('U6',8,'DATA','HIGH_OE_n',9800,5500),
                                ('U7',0,'A','ADDR_OE_n',13600,5500),('U8',8,'A','ADDR_OE_n',17400,5500)]:
        buffer(ref,x,y,[f'PC{base+b}' for b in range(8)],
               [f'{dest}{b+(base if dest=="A" else 0)}' for b in range(8)],oe,oe)
    buffer('U9',2400,6500,['CLOCK_PH3','CLOCK_PH3']+['GND']*6,['PC_CLOCK','STAGE_ROOT']+[None]*6,'GND','GND')
    for unit,(a,b) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)],1):
        inp,out=[('STAGE_ROOT','CARRY_CLOCK'),('~RESET','RESET_ACTIVE')][unit-1] if unit<=2 else ('GND',None)
        part('74xx:74HCT04','U10','SN74AHCT04N',unit,2400,8500+unit*650,{str(a):inp,str(b):out},dip(14))
    part('74xx:74HCT04','U10','SN74AHCT04N',7,2400,13900,{'14':'5V','7':'GND'},dip(14))
    part('74xx:74LS175','U11','CD74AC175M96',1,6000,9000,
         {'1':'~RESET','9':'CARRY_CLOCK','16':'5V','8':'GND',
          '4':'TERM0','5':'PREFIX1','12':'PREFIX2','13':'GND',
          '2':'CARRY1','7':'CARRY2','10':'CARRY3','15':None,'3':None,'6':None,'11':None,'14':None},so16)
    for ref,lib,value,uses,x in [
        ('U12','74xx:74LS08','SN74AHCT08DR',[('TERM0','TERM1','PREFIX1'),('PREFIX1','TERM2','PREFIX2'),
                                        ('PC_inc','CARRY1','ENABLE1'),('PC_inc','CARRY2','ENABLE2')],10000),
        ('U13','74xx:74LS08','SN74AHCT08DR',[('PC_inc','CARRY3','ENABLE3')],14000),
        ('U14','74xx:74LS32','SN74AHCT32N',[('~PC_L_out','RESET_ACTIVE','LOW_OE_n'),
                                        ('~PC_H_out','RESET_ACTIVE','HIGH_OE_n'),
                                        ('~PC_MAR_transfer','RESET_ACTIVE','ADDR_OE_n')],18000)]:
        for unit,(a,b,z) in enumerate([(1,2,3),(4,5,6),(9,10,8),(12,13,11)],1):
            i,j,o=uses[unit-1] if unit<=len(uses) else ('GND','GND',None)
            part(lib,ref,value,unit,x,7800+unit*900,{str(a):i,str(b):j,str(z):o},
                 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm' if ref in ('U12','U13') else dip(14))
        part(lib,ref,value,5,x,13000,{'14':'5V','7':'GND'},
             'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm' if ref in ('U12','U13') else dip(14))
    for ref,count,x,y,nets in [('J1',10,2300,2500,['5V','GND','CLOCK_PH3','~RESET','PC_inc','~PC_L_load','~PC_H_load','~PC_L_out','~PC_H_out','~PC_MAR_transfer']),
                              ('J2',10,21000,2500,['5V','GND']+[f'DATA{b}' for b in range(8)]),
                              ('J3',18,21000,6500,['5V','GND']+[f'A{b}' for b in range(16)])]:
        part(f'Connector_Generic:Conn_01x{count:02}',ref,ref,1,x,y,{str(i):n for i,n in enumerate(nets,1)},
             f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')
    for i in range(14):
        part('Device:C',f'C{i+1}','100nF',1,1300+i*1500,15100,{'1':'5V','2':'GND'},
             'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    lines.append('$EndSCHEMATC');return '\n'.join(lines)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('PC drawing differs; review before regenerating')
    print(DEST)

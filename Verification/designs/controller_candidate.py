"""Draw the CW1 ROM/latch/decode slice. Verification reads its KiCad pins."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from dm02.legacy import library

DEST=ROOT/'Circuits/KiCad/Controller/candidates/Control-Word.sch'


def drawing():
    lines=['EESchema Schematic File Version 4','EELAYER 29 0','EELAYER END',
           '$Descr A2 23386 16535','Sheet 1 1','Title "DM-02 control-word slice candidate"',
           'Date "2026-11-14"','Rev "CW1"','Comp "DM-02"',
           'Comment1 "ROM address = opcode:tstate:live flags. PH1 latch; PH2 decode window; PH3 receiver capture."',
           'Comment2 "Fetch/sequencer/HALT arbitration are external boundaries. Reset inhibits until first word capture."',
           'Comment3 "Verification/controller-parts.json; Documentation/Control-word.md"','Comment4 ""','$EndDescr']
    serial=0
    def part(lib,ref,value,unit,x,y,nets,footprint):
        nonlocal serial
        serial+=1
        lines.extend(['$Comp',f'L {lib} {ref}',f'U {unit} 1 {0x69C00000+serial:08X}',f'P {x} {y}',
                      f'F 0 "{ref}" H {x+100} {y+300} 50 0000 L CNN',
                      f'F 1 "{value}" H {x+100} {y+200} 50 0000 L CNN',
                      f'F 2 "{footprint}" H {x} {y} 50 0001 C CNN',f'\t{unit} {x} {y}',
                      '\t1 0 0 -1','$EndComp'])
        ns,name=lib.split(':');pins=[p for p in library(ns)[name]['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,1)]
        if set(nets)!={p['number'] for p in pins}:raise ValueError('Incomplete pin assignment: '+ref)
        for p in pins:
            px,py=x+p['x'],y-p['y'];net=nets[p['number']]
            if net is None:lines.append(f'NoConn ~ {px} {py}')
            else:lines.extend([f'Text Label {px} {py} 0 39 ~ 0',net])
    dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    def note(x,y,text):lines.extend([f'Text Notes {x} {y} 0 60 ~ 0',text])
    note(900,600,'CW1: two 64K x 8 OTP ROMs replace the architectural 64K x 16 ROM; little-endian low/high banks')
    address_pins=[10,9,8,7,6,5,4,3,25,24,21,23,2,26,27,1]
    data_pins=[11,12,13,15,16,17,18,19]
    for i in range(2):
        nets={'14':'GND','28':'5V','20':'GND','22':'GND'}
        nets.update({str(p):f'ROM_A{b}' for b,p in enumerate(address_pins)})
        nets.update({str(p):f'ROM_D{8*i+b}' for b,p in enumerate(data_pins)})
        part('Memory_EPROM:27C512',f'U{i+1}','AT27C512R-70PU',1,4300+4000*i,2400,nets,'Package_DIP:DIP-28_W15.24mm')
        nets={'1':'GND','10':'GND','11':'WORD_CLOCK','20':'5V'}
        nets.update({str(2+b):f'ROM_D{8*i+b}' for b in range(8)})
        nets.update({str(19-b):f'WORD{8*i+b}' for b in range(8)})
        part('74xx:74HCT574',f'U{i+3}','SN74HCT574N',1,4300+4000*i,5700,nets,dip(20))
    for i,(base,en,prefix) in enumerate([(11,'DATA_n','OUT'),(7,'DATA_n','LOAD'),(11,'WORD15','FA'),(1,'ALU_FORMAT','FB')]):
        nets={'12':'GND','24':'5V','18':'INHIBIT','19':en}
        nets.update({str(23-b):f'WORD{base+b}' for b in range(4)})
        for b,p in enumerate([1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17]):
            nets[str(p)]=f'{prefix}{b}_n' if 1<=b<=(14 if i<2 else 12) else None
        part('74xx:74LS154',f'U{i+5}','CD74HCT154M96',1,12300+2800*i,2600,nets,'Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm')
    nets={'1':'GND','19':'GND','20':'5V','10':'GND'}
    for p,name in zip([2,4,6,8,17,15,13,11],['CLOCK_PH1']+['GND']*7):nets[str(p)]=name
    for p,name in zip([18,16,14,12,3,5,7,9],['WORD_CLOCK']+[None]*7):nets[str(p)]=name
    part('74xx:74HCT244','U9','SN74AHCT244N',1,2200,8700,nets,dip(20))
    part('74xx:74LS175','U10','CD74AC175M96',1,5700,8700,
         {'1':'~RESET','9':'WORD_CLOCK','16':'5V','8':'GND','4':'5V','5':'GND','12':'GND','13':'GND',
          '2':'VALID','7':None,'10':None,'15':None,'3':None,'6':None,'11':None,'14':None},
         'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')
    for ref,lib,value,uses,x in [
        ('U11','74xx:74LS08','SN74AHCT08DR',[('VALID','~RESET','READY'),('READY','CLOCK_PH2','ACTIVE'),
                                         ('WORD15','WORD6','ALU_FORMAT'),('ACTIVE','ALU_FORMAT','ALU_ENABLE')],9000),
        *[(f'U{13+i}','74xx:74LS00','SN74AHCT00DR',[(f'FA{1+4*i+b}_n',f'FB{1+4*i+b}_n',f'FUN{1+4*i+b}') for b in range(4)],14500+i*3000) for i in range(3)]]:
        for unit,(a,b,z) in enumerate([(1,2,3),(4,5,6),(9,10,8),(12,13,11)],1):
            p,q,r=uses[unit-1]
            part(lib,ref,value,unit,x,7000+unit*950,{str(a):p,str(b):q,str(z):r},'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm')
        part(lib,ref,value,5,x,12300,{'14':'5V','7':'GND'},'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm')
    for unit,(a,b) in enumerate([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)],1):
        p,q=[('WORD15','DATA_n'),('ACTIVE','INHIBIT'),('FUN6','~PC_MAR_transfer')][unit-1] if unit<=3 else ('GND',None)
        part('74xx:74HCT04','U12','SN74AHCT04N',unit,11700,7000+unit*700,{str(a):p,str(b):q},dip(14))
    part('74xx:74HCT04','U12','SN74AHCT04N',7,11700,12300,{'14':'5V','7':'GND'},dip(14))
    connectors=[('J1',2000,1800,['5V','GND','CLOCK_PH1','CLOCK_PH2','~RESET','VALID']),
                ('J2',2000,4600,['5V','GND']+[f'ROM_A{b}' for b in range(16)]),
                ('J3',12400,5400,['5V','GND']+[f'OUT{b}_n' for b in range(1,15)]),
                ('J4',15300,5400,['5V','GND']+[f'LOAD{b}_n' for b in range(1,15)]),
                ('J5',18300,5400,['5V','GND']+[f'FUN{b}' for b in range(1,13)]),
                ('J6',21400,5400,['5V','GND']+[f'WORD{b}' for b in range(1,6)]+['~PC_MAR_transfer','ALU_ENABLE'])]
    for ref,x,y,nets in connectors:
        count=len(nets)
        part(f'Connector_Generic:Conn_01x{count:02}',ref,ref,1,x,y,{str(i):n for i,n in enumerate(nets,1)},
             f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')
    for i in range(15):
        part('Device:C',f'C{i+1}','100nF',1,1500+i*1400,14800,{'1':'5V','2':'GND'},
             'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    note(900,13800,'Decoder outputs 0 and 15 are unconnected; zero/unused opcodes are not a hardware fail-stop policy.')
    lines.append('$EndSCHEMATC');return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('Controller drawing differs; review before regenerating')
    print(DEST)

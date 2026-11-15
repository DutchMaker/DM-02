"""Deterministic drawing of the counted-clock candidate; --write updates it.

The checked-in KiCad sheet is the verification input. This drawing helper is
not imported by the pin-derived simulator.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from dm02.legacy import library

DEST=ROOT/'Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch'


def drawing():
    lines=['EESchema Schematic File Version 4','LIBS:74xx','EELAYER 29 0','EELAYER END',
           '$Descr A3 16535 11693','Sheet 1 1','Title "DM-02 counted-clock candidate"',
           'Date "2026-11-14"','Rev "C1-ACH"','Comp "DM-02"',
           'Comment1 "4 MHz / 8; opposite-edge staging; request/ack interface"',
           'Comment2 "Candidate core: front-panel, supervisor and backplane integration pending"',
           'Comment3 "See Verification/clock-parts.json and Documentation/Counted-clock.md"',
           'Comment4 ""','$EndDescr']
    count=0

    def part(lib,ref,value,unit,x,y,nets,footprint):
        nonlocal count
        count+=1
        lines.extend(['$Comp',f'L {lib} {ref}',f'U {unit} 1 {0x69A00000+count:08X}',f'P {x} {y}',
                      f'F 0 "{ref}" H {x+150} {y+300} 50 0000 L CNN',
                      f'F 1 "{value}" H {x+150} {y+200} 50 0000 L CNN',
                      f'F 2 "{footprint}" H {x} {y} 50 0001 C CNN',
                      f'\t{unit}    {x} {y}','\t1    0    0    -1','$EndComp'])
        ns,name=lib.split(':')
        pins=[p for p in library(ns)[name]['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,1)]
        if {p['number'] for p in pins}!=set(nets): raise ValueError((ref,unit,'incomplete pin map'))
        for p in pins:
            px,py=x+p['x'],y-p['y'];net=nets[p['number']]
            if net is None: lines.append(f'NoConn ~ {px} {py}')
            else: lines.extend([f'Text Label {px} {py} 0    39   ~ 0',net])

    def note(x,y,text): lines.extend([f'Text Notes {x} {y} 0    60   ~ 0',text])
    dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    def ff(ref,unit,x,y,d,clk,r,q,nq=None):
        pins=({'1':r,'2':d,'3':clk,'4':'5V','5':q,'6':nq} if unit==1 else
              {'13':r,'12':d,'11':clk,'10':'5V','9':q,'8':nq})
        part('74xx:74HC74',ref,'SN74AHC74N',unit,x,y,pins,dip(14))
    def power(lib,ref,value,unit,x,y,n):
        part(lib,ref,value,unit,x,y,{str(n):'5V',str(n//2):'GND'},dip(n))

    note(800,700,'C1-ACH experiment: 500 kHz full cycle; PH1/PH3 lag PH0/PH2 by three oscillator periods')
    note(800,950,'RUN high = continuous cycles; rising debounced STEP while idle = one complete cycle')
    part('DM02-ACH:ACH-4MHz','Y1','ACH-4.000MHZ-EK',1,1800,2000,
         {'1':None,'4':'GND','5':'OSC_TTL','8':'5V'},'Oscillator:Oscillator_DIP-8')
    for unit,inp,out,x,y in [(1,'OSC_TTL','ROOT_P',3400,1600),(2,'ROOT_P','ROOT_N',3400,2300),
                            (3,'RUN','RUN_n',3400,3000),(4,'RUN_n','RUN_CMOS',3400,3700),
                            (5,'RESET_IN_n','RESET_IN',3400,4400),(6,'RESET_IN','RESET_RAW_n',3400,5100)]:
        pinpairs=[(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)];a,b=pinpairs[unit-1]
        part('74xx:74HCT04','U3','SN74AHCT04N',unit,x,y,{str(a):inp,str(b):out},dip(14))
    power('74xx:74HCT04','U3','SN74AHCT04N',7,3400,6400,14)
    # One buffered branch per edge feeds every register on that edge.
    part('74xx:74HCT244','U10','SN74AHCT244N',1,5400,1900,
         {'1':'GND','19':'GND','20':'5V','10':'GND','2':'ROOT_P','18':'CLK_P',
          '4':'ROOT_N','16':'CLK_N','6':'GND','14':None,'8':'GND','12':None,
          '17':'GND','3':None,'15':'GND','5':None,'13':'GND','7':None,'11':'GND','9':None},dip(20))
    # Output bank U1 loads only the opposite-edge staging bank U2.
    for ref,x,y,clk,r,ds,prefix in [('U1',12000,2300,'CLK_P','RESET_P_n',[f'S{i}' for i in range(4)],'Q'),
                                  ('U2',9300,2300,'CLK_N','RESET_N_n',['NEXT0','Q0','Q1','Q2'],'S')]:
        pins={'1':r,'9':clk,'16':'5V','8':'GND'}
        for i,(d,q,nq) in enumerate([(4,2,3),(5,7,6),(12,10,11),(13,15,14)]):
            pins.update({str(d):ds[i],str(q):prefix+str(i),str(nq):prefix+str(i)+'_n' if ref=='U1' else None})
        part('74xx:74LS175',ref,'CD74AC175M96',1,x,y,pins,'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')
    note(7400,1100,'U2 captures next state on CLK_N; U1 publishes it on CLK_P')
    # Johnson sequence: 0,1,3,7,15,14,12,8,0. Only 0 can wait.
    for ref,lib,value,uses,x in [('U4','74xx:74LS32','SN74AHC32N',
                                [('Q0','REQUEST_SYNC','ADVANCE'),('Q0','Q3','ACTIVE_RAW'),
                                 ('RUN_CMOS','STEP_PENDING','REQUEST_CMOS')],5500),
                               ('U5','74xx:74LS08','SN74AHC08N',
                                [('ADVANCE','Q3_n','NEXT0'),('Q0_n','Q3_n','IDLE_RAW'),
                                 ('IDLE_RAW','RESET_N_n','STEP_CLEAR_n')],7400)]:
        for unit,(a,b,z) in enumerate([(1,2,3),(4,5,6),(9,10,8),(12,13,11)],1):
            inp0,inp1,out=uses[unit-1] if unit<=len(uses) else ('GND','GND',None)
            part(lib,ref,value,unit,x,3900+unit*650,{str(a):inp0,str(b):inp1,str(z):out},dip(14))
        power(lib,ref,value,5,x,7900,14)
    note(8800,4200,'Asynchronous assertion; reset release crosses opposite edges')
    ff('U6',1,9400,5000,'5V','CLK_P','RESET_RAW_n','RESET_STAGE0')
    ff('U6',2,11600,5000,'RESET_STAGE0','CLK_N','RESET_RAW_n','RESET_P_n')
    ff('U7',1,13800,5000,'RESET_P_n','CLK_P','RESET_RAW_n','RESET_N_n')
    ff('U7',2,13800,6300,'5V','STEP_CMOS','STEP_CLEAR_n','STEP_PENDING')
    power('74xx:74HC74','U6','SN74AHC74N',3,9500,7200,14)
    power('74xx:74HC74','U7','SN74AHC74N',3,11500,7200,14)
    note(8800,8000,'Request synchronizer: metastability MTBF still requires device/system qualification')
    ff('U8',1,9500,8800,'REQUEST_CMOS','CLK_N','RESET_N_n','REQUEST_STAGE0')
    ff('U8',2,11500,8800,'REQUEST_STAGE0','CLK_P','RESET_P_n','REQUEST_SYNC')
    power('74xx:74HC74','U8','SN74AHC74N',3,13800,8800,14)
    part('74xx:74HCT244','U9','SN74AHCT244N',1,14400,2300,
         {'1':'GND','19':'GND','20':'5V','10':'GND','2':'Q0_n','18':'CLOCK_PH0',
          '4':'Q3_n','16':'CLOCK_PH1','6':'Q0','14':'CLOCK_PH2','8':'Q3','12':'CLOCK_PH3',
          '17':'ACTIVE_RAW','3':'ACTIVE','15':'RESET_N_n','5':'READY',
          '13':'STEP','7':'STEP_CMOS','11':'GND','9':None},dip(20))
    part('Connector_Generic:Conn_01x08','J1','CONTROL',1,1700,3900,
         {str(i):n for i,n in enumerate(['5V','GND','RESET_IN_n','RUN','ACTIVE','READY','GND','STEP'],1)},
         'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical')
    part('Connector_Generic:Conn_01x08','J2','PHASES',1,1700,5700,
         {str(i):n for i,n in enumerate(['5V','GND','CLOCK_PH0','CLOCK_PH1','CLOCK_PH2','CLOCK_PH3','GND',None],1)},
         'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical')
    for i,net in enumerate(['RUN','RESET_IN_n','STEP'],1):
        part('Device:R',f'R{i}','10k',1,1000+i*900,7600,{'1':net,'2':'GND'},
             'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal')
    note(800,9100,'100nF per logic package + oscillator; placement and exact passive sourcing pending')
    for i in range(11):
        part('Device:C',f'C{i+1}','100nF',1,1100+i*1250,10000,{'1':'5V','2':'GND'},
             'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    lines.append('$EndSCHEMATC')
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();text=drawing()
    if args.write:
        DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:
        raise SystemExit('Candidate drawing differs from generator; review source changes before regenerating.')
    print(DEST)

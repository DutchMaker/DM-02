"""Draw FR1, or append its private-output flash array to a staged ALU."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from designs.address_candidate import Board

DEST=ROOT/'Circuits/KiCad/ALU/candidates/Flash-Array.sch'


def array(d,start=1,address=None,result=None):
    address=address or [f'A{i}' for i in range(21)]
    result=result or [f'RESULT{i}' for i in range(16)]
    if len(address)!=21 or len(result)!=16:raise ValueError('FR1 port width')
    ref=start
    def part(lib,value,nets,footprint):
        nonlocal ref
        d.part(lib,f'U{ref}',value,1,nets,footprint);ref+=1
    def buf(ins,outs):
        nets={'1':'GND','19':'GND','10':'GND','20':'5V'}
        nets.update({str(p):n for p,n in zip([2,4,6,8,17,15,13,11],ins+['GND']*(8-len(ins)))})
        nets.update({str(p):n for p,n in zip([18,16,14,12,3,5,7,9],outs+[None]*(8-len(outs)))})
        part('74xx:74HCT244','SN74AHCT244N',nets,'Package_DIP:DIP-20_W7.62mm')
    def mux(sel,a,b,q):
        nets={'1':sel,'15':'GND','16':'5V','8':'GND'}
        for ip,jp,op,x,y,z in zip([2,5,11,14],[3,6,10,13],[4,7,9,12],a,b,q):nets.update({str(ip):x,str(jp):y,str(op):z})
        part('74xx:74LS157','SN74AHCT157N',nets,'Package_DIP:DIP-16_W7.62mm')
    bits=lambda prefix,base=0,width=4:[f'FR_{prefix}{i}' for i in range(base,base+width)]
    for bank in range(4):
        for lane in range(2):
            nets={'16':'GND','32':'5V','22':'GND','24':'GND','31':'5V'}
            nets.update({str(pin):f'FR_GROUP{bank//2}_A{bit}' for bit,pin in enumerate([12,11,10,9,8,7,6,5,27,26,23,25,4,28,29,3,2,30,1])})
            nets.update({str(pin):f'FR_BANK{bank}_{8*lane+bit}' for bit,pin in enumerate([13,14,15,17,18,19,20,21])})
            part('DM02-Flash:SST39SF040','SST39SF040-70-4I-NHE',nets,'Package_LCC:PLCC-32_THT-Socket')
    for group in range(2):
        for byte in range(3):
            begin=byte*8;end=min(begin+8,19)
            buf(address[begin:end],bits(f'GROUP{group}_A',begin,end-begin))
    buf([address[19],address[19],address[20]],['FR_SELECT_LOW','FR_SELECT_HIGH','FR_SELECT_FINAL'])
    for nibble in range(4):
        begin=nibble*4
        mux('FR_SELECT_LOW',bits('BANK0_',begin),bits('BANK1_',begin),bits('PAIR0_',begin))
        mux('FR_SELECT_HIGH',bits('BANK2_',begin),bits('BANK3_',begin),bits('PAIR1_',begin))
        mux('FR_SELECT_FINAL',bits('PAIR0_',begin),bits('PAIR1_',begin),result[begin:begin+4])
    for index in range(start,ref):d.part('Device:C',f'C{index}','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')


def drawing():
    d=Board('DM-02 private-output flash array','FR1',[
        'Eight SST39SF040 PLCC32 devices; four word banks; WE tied inactive high.',
        'Private outputs, buffered address groups and two-level AHCT157 bank selection.',
        '100 us power-up-to-read; physical programmer, startup supply and PCB qualification pending.'])
    d.row_step=2800;array(d)
    d.connector('J1',['5V','GND']+[f'A{i}' for i in range(21)])
    d.connector('J2',['5V','GND']+[f'RESULT{i}' for i in range(16)])
    return d.text()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('FR1 candidate drawing differs')
    print(DEST)

"""Draw ME1: protected ROM/RAM, phased write and registered external IO."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from designs.address_candidate import Board

DEST=ROOT/'Circuits/KiCad/Memory/candidates/Memory-IO.sch'


def drawing():
    d=Board('DM-02 memory and IO candidate','ME1',[
        'ROM 0000-3FFF; SRAM 4000-FEFF; external IO FF00-FFFF.',
        'SRAM write window ends at PH3; registered IO output strobe on PH0.',
        'Program loading, electrical bus/reset qualification and external display remain open.'])
    bits=lambda prefix,base=0,width=4:[f'{prefix}{b}' for b in range(base,base+width)]
    # Exact PDIP pin maps, including the SRAM's unused A16 and NC pins.
    d.ref+=1;nets={'14':'GND','28':'5V','20':'GND','22':'GND'}
    for b,p in enumerate([10,9,8,7,6,5,4,3,25,24,21,23,2,26,27,1]):nets[str(p)]=f'ADDRESS{b}' if b<14 else 'GND'
    nets.update({str(p):f'ROM{b}' for b,p in enumerate([11,12,13,15,16,17,18,19])})
    d.part('Memory_EPROM:27C512','U1','AT27C512R-70PU',1,nets,'Package_DIP:DIP-28_W15.24mm')
    d.ref+=1;nets={'1':None,'2':'GND','16':'GND','32':'5V','22':'GND','30':'5V','24':'READ_n','29':'RAM_WE_n'}
    for b,p in enumerate([12,11,10,9,8,7,6,5,27,26,23,25,4,28,3,31]):nets[str(p)]=f'ADDRESS{b}'
    nets.update({str(p):f'RAM{b}' for b,p in enumerate([13,14,15,17,18,19,20,21])})
    d.part('DM02-Memory:AS6C1008','U2','AS6C1008-55PCN',1,nets,'Package_DIP:DIP-32_W15.24mm')
    d.buf(bits('DATA',width=8),bits('INPUT',width=8))
    d.buf(bits('INPUT',width=8),bits('RAM',width=8),'WRITE_n')
    for half in range(2):
        d.mux('NON_ROM',bits('ROM',half*4),bits('RAM',half*4),bits('MEMORY',half*4))
        d.mux('IO_SELECT',bits('MEMORY',half*4),bits('IO_INPUT',half*4),bits('READ_DATA',half*4))
    d.buf(bits('READ_DATA',width=8),bits('DATA',width=8),'READ_n')
    d.buf(['PH3','CLOCK_ROOT','CLOCK_ROOT','IO_REQUEST','IO_REQUEST']+['GND']*3,
          ['CLOCK_ROOT','DATA_CLOCK','ADDR_CLOCK','IO_DATA_LOAD','IO_ADDR_LOAD']+[None]*3)
    for prefix,source,clock in [('IO_DATA','INPUT','DATA_CLOCK'),('IO_ADDR','ADDRESS','ADDR_CLOCK')]:
        for half in range(2):
            d.reg(clock,bits(prefix+'_D',half*4),bits(prefix,half*4))
            d.mux(prefix+'_LOAD',bits(prefix,half*4),bits(source,half*4),bits(prefix+'_D',half*4))
    d.reg('DATA_CLOCK',['IO_REQUEST','GND','GND','GND'],['IO_PENDING',None,None,None])
    d.gate('32','ADDRESS14','ADDRESS15','NON_ROM')
    for i in range(4):d.gate('08',f'ADDRESS{8+2*i}',f'ADDRESS{9+2*i}',f'IO_PAIR{i}')
    d.gate('08','IO_PAIR0','IO_PAIR1','IO_LOW');d.gate('08','IO_PAIR2','IO_PAIR3','IO_HIGH')
    d.gate('08','IO_LOW','IO_HIGH','IO_SELECT');d.gate('04','IO_SELECT','NOT_IO')
    d.gate('08','NON_ROM','NOT_IO','RAM_SELECT')
    d.gate('04','MEM_out_n','READ_RAW');d.gate('08','READ_RAW','MEM_load_n','READ_SAFE')
    d.gate('00','READ_SAFE','RESET_n','READ_n')
    d.gate('04','MEM_load_n','WRITE_RAW');d.gate('08','WRITE_RAW','MEM_out_n','WRITE_SAFE')
    d.gate('08','WRITE_SAFE','RESET_n','WRITE');d.gate('04','WRITE','WRITE_n')
    d.gate('04','PH3','BEFORE_CAPTURE');d.gate('08','WRITE','PH2','WRITE_WINDOW')
    d.gate('08','WRITE_WINDOW','BEFORE_CAPTURE','EARLY_WRITE')
    d.gate('00','EARLY_WRITE','RAM_SELECT','RAM_WE_n')
    d.gate('08','WRITE','IO_SELECT','IO_REQUEST')
    d.gate('08','IO_PENDING','RESET_n','IO_READY');d.gate('08','IO_READY','PH0','IO_STROBE')
    d.connector('J1',['5V','GND','PH0','PH2','PH3','RESET_n','MEM_out_n','MEM_load_n'])
    d.connector('J2',['5V','GND']+bits('DATA',width=8))
    d.connector('J3',['5V','GND']+bits('ADDRESS',width=16))
    d.connector('J4',['5V','GND','IO_STROBE']+bits('IO_DATA',width=8)+bits('IO_ADDR',width=8))
    d.connector('J5',['5V','GND']+bits('IO_INPUT',width=8))
    return d.finish()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('ME1 drawing differs')
    print(DEST)

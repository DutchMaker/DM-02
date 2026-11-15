"""Draw RG1: buffered DATA input and resettable B/C/H/L storage."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from designs.drawing import Drawing

DEST=ROOT/'Circuits/KiCad/Registers-StackPointer/candidates/General-Registers.sch'


def drawing():
    d=Drawing('DM-02 general register candidate','RG1',[
        'B/C/H/L capture on PH3; reset clears storage and inhibits DATA outputs.',
        'One input buffer isolates the four register banks from shared DATA.',
        'Shared bus load, reset distribution and PCB qualification remain open.'])
    part=d.part;dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    def buffer(ref,ins,outs,oe='GND'):
        nets={'1':oe,'19':oe,'10':'GND','20':'5V'}
        nets.update({str(p):s for p,s in zip([2,4,6,8,17,15,13,11],ins)})
        nets.update({str(p):s for p,s in zip([18,16,14,12,3,5,7,9],outs)})
        part('74xx:74HCT244',ref,'SN74AHCT244N',1,nets,dip(20))
    buffer('U1',[f'DATA{b}' for b in range(8)],[f'INPUT{b}' for b in range(8)])
    buffer('U2',['PH3']+['CLOCK_ROOT']*4+['GND']*3,['CLOCK_ROOT']+[r+'_CLOCK' for r in 'BCHL']+[None]*3)
    for index,r in enumerate('BCHL'):
        base=3+5*index
        for half in range(2):
            nets={'1':'RESET_n','9':r+'_CLOCK','16':'5V','8':'GND'}
            for b,(di,q,nq) in enumerate([(4,2,3),(5,7,6),(12,10,11),(13,15,14)]):
                bit=half*4+b;nets.update({str(di):f'{r}_D{bit}',str(q):f'{r}{bit}',str(nq):None})
            part('74xx:74LS175',f'U{base+half}','CD74AC175M96',1,nets,'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')
            nets={'1':r+'_LOAD','15':'GND','16':'5V','8':'GND'}
            for b,(a,z,q) in enumerate([(2,3,4),(5,6,7),(11,10,9),(14,13,12)]):
                bit=half*4+b;nets.update({str(a):f'{r}{bit}',str(z):f'INPUT{bit}',str(q):f'{r}_D{bit}'})
            part('74xx:74LS157',f'U{base+2+half}','SN74AHCT157N',1,nets,dip(16))
        buffer(f'U{base+4}',[f'{r}{b}' for b in range(8)],[f'DATA{b}' for b in range(8)],r+'_OE_n')
    # Distribute PH3 through a single root input; each bank sees one branch.
    # Four branch inputs load the root by 40 pF plus local routing allocation.
    ref=23
    uses={'04':[(r+'_load_n',r+'_LOAD_RAW') for r in 'BCHL']+[(r+'_out_n',r+'_OUT') for r in 'BCHL'],
          '08':[(r+'_LOAD_RAW','RESET_n',r+'_LOAD') for r in 'BCHL'],
          '00':[(r+'_OUT','RESET_n',r+'_OE_n') for r in 'BCHL']}
    for kind,items in uses.items():
        width=6 if kind=='04' else 4
        for start in range(0,len(items),width):
            name=f'U{ref}';ref+=1
            lib='74xx:74HCT04' if kind=='04' else '74xx:74LS'+kind
            value={'04':'SN74AHCT04N','08':'SN74AHCT08DR','00':'SN74AHCT00DR'}[kind]
            fp=dip(14) if kind=='04' else 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm'
            for u in range(1,width+1):
                use=items[start+u-1] if start+u<=len(items) else (('GND',None) if kind=='04' else ('GND','GND',None))
                pins=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[u-1]
                part(lib,name,value,u,{str(p):s for p,s in zip(pins,use)},fp)
            part(lib,name,value,width+1,{'14':'5V','7':'GND'},fp)
    for i,names in enumerate([['5V','GND','PH3','RESET_n']+[r+'_load_n' for r in 'BCHL']+[r+'_out_n' for r in 'BCHL'],
                              ['5V','GND']+[f'DATA{b}' for b in range(8)]],1):
        count=len(names)
        part(f'Connector_Generic:Conn_01x{count:02}',f'J{i}',f'J{i}',1,{str(p):s for p,s in enumerate(names,1)},
             f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')
    for i in range(1,ref):part('Device:C',f'C{i}','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    return d.text()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    text=drawing()
    if args.write:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(text)
    elif not DEST.exists() or DEST.read_text()!=text:raise SystemExit('RG1 drawing differs')
    print(DEST)

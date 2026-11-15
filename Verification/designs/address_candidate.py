"""Draw SP1/MA1 with PH1 address snapshots and PH3 state capture."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from designs.drawing import Drawing

SOURCES={name:ROOT/path for name,path in {
    'stack':'Circuits/KiCad/Registers-StackPointer/candidates/Stack-Pointer.sch',
    'mar':'Circuits/KiCad/Memory/candidates/Memory-Address.sch'}.items()}


class Board(Drawing):
    def __init__(self,title,rev,comments=None):
        super().__init__(title,rev,comments or ['PH1 snapshots; PH3 synchronous state updates; reset clears storage.',
            'Dedicated PC/SP address links; early MAR bypass serves same-word memory reads.',
            'Device-delay evidence is conditional on load and slew; no PCB release.'],page=('A0',46811,33110))
        self.ref=0;self.gates={'04':[],'08':[],'00':[],'32':[]}

    def ic(self,lib,value,nets,footprint=None):
        self.ref+=1;ref=f'U{self.ref}'
        self.part('74xx:'+lib,ref,value,1,nets,footprint or 'Package_DIP:DIP-16_W7.62mm');return ref

    def reg(self,clock,ds,qs):
        nets={'1':'RESET_n','9':clock,'16':'5V','8':'GND'}
        for a,b,c,d,q in zip([4,5,12,13],[2,7,10,15],[3,6,11,14],ds,qs):nets.update({str(a):d,str(b):q,str(c):None})
        return self.ic('74LS175','CD74AC175M96',nets,'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')

    def mux(self,sel,old,new,out):
        nets={'1':sel,'15':'GND','16':'5V','8':'GND'}
        for a,b,q,x,y,z in zip([2,5,11,14],[3,6,10,13],[4,7,9,12],old,new,out):nets.update({str(a):x,str(b):y,str(q):z})
        return self.ic('74LS157','SN74AHCT157N',nets)

    def buf(self,ins,outs,oe='GND'):
        nets={'1':oe,'19':oe,'10':'GND','20':'5V'}
        nets.update({str(p):n for p,n in zip([2,4,6,8,17,15,13,11],ins)})
        nets.update({str(p):n for p,n in zip([18,16,14,12,3,5,7,9],outs)})
        return self.ic('74HCT244','SN74AHCT244N',nets,'Package_DIP:DIP-20_W7.62mm')

    def adder(self,a,b,ci,s,co):
        nets={'7':ci,'9':co,'8':'GND','16':'5V'}
        for pins,names in [([5,3,14,12],a),([6,2,15,11],b),([4,1,13,10],s)]:
            nets.update({str(p):n for p,n in zip(pins,names)})
        return self.ic('74LS283','CD74ACT283E',nets)

    def gate(self,kind,*nets):self.gates[kind].append(nets)

    def connector(self,ref,names):
        count=len(names);self.part(f'Connector_Generic:Conn_01x{count:02}',ref,ref,1,{str(p):n for p,n in enumerate(names,1)},
                                  f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')

    def finish(self):
        for kind,items in self.gates.items():
            width=6 if kind=='04' else 4
            for start in range(0,len(items),width):
                self.ref+=1;ref=f'U{self.ref}';lib='74xx:74HCT04' if kind=='04' else '74xx:74LS'+kind
                value={'04':'SN74AHCT04N','08':'SN74AHCT08DR','00':'SN74AHCT00DR','32':'SN74AHCT32N'}[kind]
                fp='Package_DIP:DIP-14_W7.62mm' if kind in ('04','32') else 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm'
                for u in range(1,width+1):
                    use=items[start+u-1] if start+u<=len(items) else (('GND',None) if kind=='04' else ('GND','GND',None))
                    pins=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[u-1]
                    self.part(lib,ref,value,u,{str(p):n for p,n in zip(pins,use)},fp)
                self.part(lib,ref,value,width+1,{'14':'5V','7':'GND'},fp)
        for i in range(1,self.ref+1):self.part('Device:C',f'C{i}','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
        return self.text()


def drawing(kind):
    if kind not in SOURCES:raise ValueError(kind)
    mar=kind=='mar';d=Board('DM-02 '+('memory address' if mar else 'stack pointer')+' candidate','MA1' if mar else 'SP1')
    bits=lambda prefix,base=0,width=4:[f'{prefix}{i}' for i in range(base,base+width)]
    # Clock roots and four-pin fanout branches stay within local 50 pF bounds.
    d.buf(['PH1','PH3','PH1_ROOT','PH1_ROOT','PH1_ROOT','PH3_ROOT','PH3_ROOT','GND'],
          ['PH1_ROOT','PH3_ROOT','SHADOW_CLOCK','PC_CLOCK','SP_CLOCK','LOW_CLOCK','HIGH_CLOCK',None])
    d.buf(bits('DATA',width=8),bits('INPUT',width=8))
    for nibble in range(4):
        b=4*nibble
        d.reg('LOW_CLOCK' if nibble<2 else 'HIGH_CLOCK',bits('NEXT',b),bits('STATE',b))
        d.reg('SHADOW_CLOCK',bits('STATE',b),bits('SHADOW',b))
    if mar:
        for nibble in range(4):
            b=4*nibble
            d.reg('PC_CLOCK',bits('PC',b),bits('PC_SNAPSHOT',b))
            d.reg('SP_CLOCK',bits('SP',b),bits('SP_SNAPSHOT',b))
        d.gate('32','FETCH0','PC_TRANSFER','FROM_PC')
        d.gate('32','FROM_PC','SP_TRANSFER','TRANSFER')
        # Buffer replicated selects; each branch drives only four mux inputs.
        d.buf(['SP_TRANSFER','TRANSFER','TRANSFER','INC']+['GND']*4,
              ['SOURCE_SP','TRANSFER_BASE','TRANSFER_VISIBLE','CARRY_IN']+[None]*4)
        for nibble in range(4):
            b=4*nibble
            d.mux('SOURCE_SP',bits('PC_SNAPSHOT',b),bits('SP_SNAPSHOT',b),bits('TRANSFER_VALUE',b))
            d.mux('TRANSFER_BASE',bits('SHADOW',b),bits('TRANSFER_VALUE',b),bits('BASE',b))
            d.mux('TRANSFER_VISIBLE',bits('STATE',b),bits('TRANSFER_VALUE',b),bits('ADDRESS',b))
    else:
        d.buf(['DEC']*4+['INC']+['GND']*3,[f'DEC{n}' for n in range(4)]+['CARRY_IN']+[None]*3)
    for nibble in range(4):
        b=4*nibble
        d.adder(bits('BASE' if mar else 'SHADOW',b),['GND' if mar else f'DEC{nibble}']*4,
                'CARRY_IN' if nibble==0 else f'CARRY{nibble}',bits('SUM',b),f'CARRY{nibble+1}' if nibble<3 else None)
        d.mux('LOAD_LOW' if nibble<2 else 'LOAD_HIGH',bits('SUM',b),bits('INPUT',4*(nibble%2)),bits('NEXT',b))
    for half,name in enumerate(('LOW','HIGH')):
        d.gate('04',f'{name}_load_n',f'{name}_LOAD_RAW');d.gate('08',f'{name}_LOAD_RAW','RESET_n',f'LOAD_{name}')
        d.gate('04',f'{name}_out_n',f'{name}_OUT');d.gate('00',f'{name}_OUT','RESET_n',f'{name}_OE_n')
        d.buf(bits('ADDRESS' if mar else 'STATE',half*8,8),bits('DATA',width=8),f'{name}_OE_n')
        if not mar:d.buf(bits('STATE',half*8,8),bits('ADDRESS',half*8,8))
    d.connector('J1',['5V','GND','PH1','PH3','RESET_n','INC']+
                (['FETCH0','PC_TRANSFER','SP_TRANSFER'] if mar else ['DEC'])+
                ['LOW_load_n','HIGH_load_n','LOW_out_n','HIGH_out_n'])
    d.connector('J2',['5V','GND']+bits('DATA',width=8))
    d.connector('J3',['5V','GND']+bits('ADDRESS',width=16))
    if mar:
        d.connector('J4',['5V','GND']+bits('PC',width=16));d.connector('J5',['5V','GND']+bits('SP',width=16))
    return d.finish()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    for kind,dest in SOURCES.items():
        text=drawing(kind)
        if args.write:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        elif not dest.exists() or dest.read_text()!=text:raise SystemExit(kind+' drawing differs')
        print(dest)

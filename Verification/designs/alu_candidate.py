"""Draw AL1: PH1 result isolation, synchronous flags and reset-inhibited drivers."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dm02.common import ROOT
from dm02.legacy import library
from designs.drawing import Drawing

DEST=ROOT/'Circuits/KiCad/ALU/candidates/Timed-ALU.sch'
FLASH_DEST=ROOT/'Circuits/KiCad/ALU/candidates/Flash-ALU.sch'


def drawing(flash=False):
    d=Drawing('DM-02 staged ALU candidate','AL1',[
        'PH3 operand capture; PH1 ROM result snapshot; PH3 synchronous flag capture.',
        'Legacy M27C322-100F1 timing study: obsolete ROM; replacement/procurement unresolved.',
         'Documentation/Timed-ALU.md; shared DATA load and PCB qualification remain open.'])
    if flash:
        d=Drawing('DM-02 staged flash ALU candidate','AL2',[
            'Eight SST39SF040 PLCC32 devices; private outputs and bank selection.',
            'PH1 result isolation; PH3 operands/A/flags; reset must cover flash startup.',
            'Physical programming, startup supervisor, DATA and clock/reset qualification remain open.'],
            row_step=2800,page=('User',46811,46811))
    part=d.part;dip=lambda n:f'Package_DIP:DIP-{n}_W7.62mm'
    so16='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'
    pins={}
    for p in library('74xx-Computer-Symbols')['M27C322']['pins']:
        if p['convert'] not in (0,1):continue
        name=p['name']
        if name.startswith('A'):
            bit=int(name[1:]);net=f'B{bit}' if bit<8 else f'A{bit-8}' if bit<16 else f'OP{bit-16}'
        elif name.startswith('D'):net='ROM_'+name
        else:net='5V' if name=='VCC' else 'GND'
        pins[p['number']]=net
    if not flash:part('74xx-Computer-Symbols:M27C322','U1','M27C322-100F1',1,pins,'Package_DIP:DIP-42_W15.24mm')
    def reg(ref,clock,ds,qs):
        nets={'1':'RESET_n','9':clock,'16':'5V','8':'GND'}
        for i,(a,b,c) in enumerate([(4,2,3),(5,7,6),(12,10,11),(13,15,14)]):
            nets.update({str(a):ds[i],str(b):qs[i],str(c):None})
        part('74xx:74LS175',ref,'CD74AC175M96',1,nets,so16)
    for i in range(2):reg(f'U{2+i}','A_CLOCK',[f'A_D{4*i+b}' for b in range(4)],[f'A{4*i+b}' for b in range(4)])
    def mux(ref,select,old,new,out):
        nets={'1':select,'15':'GND','16':'5V','8':'GND'}
        for i,(a,b,c) in enumerate([(2,3,4),(5,6,7),(11,10,9),(14,13,12)]):
            nets.update({str(a):old[i],str(b):new[i],str(c):out[i]})
        part('74xx:74LS157',ref,'SN74AHCT157N',1,nets,dip(16))
    for i in range(2):mux(f'U{4+i}','A_LOAD',[f'A{4*i+b}' for b in range(4)],
                         [f'DATA{4*i+b}' for b in range(4)],[f'A_D{4*i+b}' for b in range(4)])
    for i in range(2):
        nets={'1':'OPERAND_LOAD_n','10':'GND','11':'OPERAND_CLOCK','20':'5V'}
        for b,(inp,out) in enumerate(zip([3,4,7,8,13,14,17,18],[2,5,6,9,12,15,16,19])):
            nets[str(inp)]=f'DATA{b}' if i==0 else f'FUNCTION{b}' if b<5 else 'GND'
            nets[str(out)]=f'B{b}' if i==0 else f'OP{b}' if b<5 else None
        part('74xx:74LS377',f'U{6+i}','CD74HCT377M96',1,nets,'Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm')
    for i in range(2):
        nets={'1':'GND','10':'GND','11':'RESULT_CLOCK','20':'5V'}
        nets.update({str(2+b):f'ROM_D{8*i+b}' for b in range(8)})
        nets.update({str(19-b):f'RESULT{8*i+b}' if 8*i+b<12 else None for b in range(8)})
        part('74xx:74HCT574',f'U{8+i}','SN74HCT574N',1,nets,dip(20))
    reg('U10','FLAG_CLOCK',[f'FLAG_D{b}' for b in range(4)],[f'FLAG{b}' for b in range(4)])
    mux('U11','ALU_OUT',['COMMAND_C','FLAG1','COMMAND_Z','FLAG3'],[f'RESULT{b+8}' for b in range(4)],[f'FLAG_ALU{b}' for b in range(4)])
    mux('U12','F_LOAD',[f'FLAG_ALU{b}' for b in range(4)],[f'DATA{b}' for b in range(4)],[f'FLAG_D{b}' for b in range(4)])
    def buffer(ref,ins,outs,oe='GND'):
        nets={'1':oe,'19':oe,'10':'GND','20':'5V'}
        for pin,name in zip([2,4,6,8,17,15,13,11],ins):nets[str(pin)]=name
        for pin,name in zip([18,16,14,12,3,5,7,9],outs):nets[str(pin)]=name
        part('74xx:74HCT244',ref,'SN74AHCT244N',1,nets,dip(20))
    for ref,ins,oe in [('U13',[f'A{b}' for b in range(8)],'A_OE_n'),
                       ('U14',[f'RESULT{b}' for b in range(8)],'ALU_OE_n'),
                       ('U15',[f'FLAG{b}' for b in range(4)]+['GND']*4,'F_OE_n')]:
        buffer(ref,ins,[f'DATA{b}' for b in range(8)],oe)
    buffer('U16',['PH1','PH3','CAPTURE_ROOT','CAPTURE_ROOT','CAPTURE_ROOT']+['GND']*3,
           ['RESULT_CLOCK','CAPTURE_ROOT','A_CLOCK','OPERAND_CLOCK','FLAG_CLOCK']+[None]*3)
    gates={'04':[], '08':[], '00':[]}
    def gate(kind,*nets):gates[kind].append(nets)
    for src,dst in [('A_load_n','A_LOAD_RAW'),('ALU_load_n','OPERAND_LOAD'),('F_load_n','F_LOAD'),
                    ('A_out_n','A_OUT'),('ALU_out_n','ALU_OUT'),('F_out_n','F_OUT')]:gate('04',src,dst)
    gate('08','A_LOAD_RAW','RESET_n','A_LOAD')
    gate('00','OPERAND_LOAD','RESET_n','OPERAND_LOAD_n')
    for src,dst in [('A_OUT','A_OE_n'),('ALU_OUT','ALU_OE_n'),('F_OUT','F_OE_n')]:gate('00',src,'RESET_n',dst)
    # Command -> ALU flags -> F load priority matches the compiled executor.
    for bit,name in [(0,'C'),(2,'Z')]:
        gate('04',f'FLAG{bit}',f'FLAG_{name}_n');gate('04',f'SET_{name}',f'SET_{name}_n')
        gate('00',f'FLAG_{name}_n',f'SET_{name}_n',f'SET_OR_{name}')
        gate('04',f'CLEAR_{name}',f'CLEAR_{name}_n');gate('08',f'SET_OR_{name}',f'CLEAR_{name}_n',f'COMMAND_{name}')
    ref=17
    for kind,uses in gates.items():
        width=6 if kind=='04' else 4;lib='74xx:74HCT04' if kind=='04' else '74xx:74LS'+kind
        value={'04':'SN74AHCT04N','08':'SN74AHCT08DR','00':'SN74AHCT00DR'}[kind]
        for start in range(0,len(uses),width):
            name=f'U{ref}';ref+=1;fp=dip(14) if kind=='04' else 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm'
            for unit in range(1,width+1):
                use=uses[start+unit-1] if start+unit<=len(uses) else (('GND',None) if kind=='04' else ('GND','GND',None))
                pins=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[unit-1]
                part(lib,name,value,unit,{str(p):n for p,n in zip(pins,use)},fp)
            part(lib,name,value,width+1,{'14':'5V','7':'GND'},fp)
    connectors=[['5V','GND','PH1','PH3','RESET_n','A_load_n','ALU_load_n','F_load_n','A_out_n','ALU_out_n','F_out_n',
                 'SET_C','SET_Z','CLEAR_C','CLEAR_Z'],['5V','GND']+[f'DATA{b}' for b in range(8)],
                ['5V','GND']+[f'FUNCTION{b}' for b in range(5)]+[f'FLAG{b}' for b in range(4)]]
    for i,names in enumerate(connectors,1):
        count=len(names);part(f'Connector_Generic:Conn_01x{count:02}',f'J{i}',f'J{i}',1,
                             {str(p):n for p,n in enumerate(names,1)},f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical')
    for i in range(2 if flash else 1,ref):part('Device:C',f'C{i}','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    if flash:
        from designs.flash_candidate import array
        array(d,101,[f'B{i}' for i in range(8)]+[f'A{i}' for i in range(8)]+[f'OP{i}' for i in range(5)],
              [f'ROM_D{i}' for i in range(16)])
    return d.text()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');p.add_argument('--flash',action='store_true')
    args=p.parse_args();text=drawing(args.flash);dest=FLASH_DEST if args.flash else DEST
    if args.write:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    elif not dest.exists() or dest.read_text()!=text:raise SystemExit('ALU candidate drawing differs')
    print(dest)

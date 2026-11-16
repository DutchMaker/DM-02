"""CP1-BR1 candidate sheets. All logic DIP; passives and DIN contacts THT."""
from pathlib import Path
from dm02.common import ROOT, write_json
from dm02.connector_plan import generate as contact_plan
from .drawing import Drawing

DEST=ROOT/'Circuits/KiCad/IO-Bridge/candidates'
LIBRARY=ROOT/'Circuits/KiCad/Libraries/DM02Bridge.lib'
BITS=lambda name,n=8:[name+str(i) for i in range(n)]
BUF_IN=[2,4,6,8,17,15,13,11]
BUF_OUT=[18,16,14,12,3,5,7,9]
DEC_OUT=list(range(1,12))+list(range(13,18))


def library_text():
    lines=['EESchema-LIBRARY Version 2.4','#encoding utf-8','DEF DIN96 J 0 40 Y Y 1 F N',
        'F0 "J" 0 250 50 H V C CNN','F1 "DIN96" 0 150 50 H V C CNN','DRAW',
        'S -200 100 200 -4800 0 1 10 f']
    for i,pin in enumerate(f'{r}{n}' for n in range(1,33) for r in 'abc'):
        lines.append(f'X {pin} {pin} -400 {-50*i} 200 R 30 30 1 1 P')
    return '\n'.join(lines+['ENDDRAW','ENDDEF','#End Library',''])


class Board(Drawing):
    def __init__(self,name):
        super().__init__('DM-02 '+name+' IO bridge candidate','CP1-BR1',[
            'Independent candidate; not incorporated into accepted CP1-R2.',
            'All logic DIP; common 5 V supply only; no hot plug or unpowered-card qualification.',
            'Read allocations FF03 text / FF10,20,30 qualification fixtures.',
            'Native-pin simulation and conditional delays do not qualify hardware.'],
            row_step=5600,page=('User',33110,170000))
        self.name=name;self.ref=0;self.res=0;self.gates={k:[] for k in ('04','08','00','32')};self.ports={}

    def ic(self,kind,nets,width=7.62):
        self.ref+=1
        pins={'244':20,'153':16,'154':24}[kind]
        symbol='74HCT244' if kind=='244' else '74LS'+kind
        self.part('74xx:'+symbol,f'U{self.ref}','CD74HCT'+kind+'E',1,nets,
                  f'Package_DIP:DIP-{pins}_W{width:.2f}mm')

    def buf(self,ins,outs):
        assert len(ins)==len(outs)==8
        nets={'1':'GND','19':'GND','10':'GND','20':'5V'}
        nets.update({str(p):n for p,n in zip(BUF_IN,ins)})
        nets.update({str(p):n for p,n in zip(BUF_OUT,outs)})
        self.ic('244',nets)

    def gate(self,kind,*nets):self.gates[kind].append(nets)

    def reduce(self,kind,names,out):
        names=list(names);level=0
        while len(names)>1:
            nxt=[]
            for i in range(0,len(names),2):
                if i+1==len(names):nxt.append(names[i]);continue
                target=out if len(names)==2 else f'{out}_L{level}_{i//2}'
                self.gate(kind,names[i],names[i+1],target);nxt.append(target)
            names=nxt;level+=1

    def decoder(self,ins,prefix):
        nets={'12':'GND','24':'5V','18':'GND','19':'GND'}
        nets.update({str(p):n for p,n in zip((23,22,21,20),ins)})
        nets.update({str(p):f'{prefix}{i}_n' for i,p in enumerate(DEC_OUT)})
        self.ic('154',nets,15.24)

    def resistor(self,a,b,value):
        self.res+=1
        self.part('Device:R',f'R{self.res}',value,1,{'1':a,'2':b},
                  'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal')

    def port(self,ref,names,count=None):
        count=count or len(names);names=list(names)+[None]*(count-len(names))
        self.part(f'Connector_Generic:Conn_01x{count:02}',ref,'INTERNAL_BOUNDARY_NOT_FITTED',1,
            {str(i):n for i,n in enumerate(names,1)},'')
        self.ports[ref]={str(i):n for i,n in enumerate(names,1) if n is not None}

    def slot(self,number,connector):
        nets={p['pin']:p['net'] for p in connector['pins']}
        self.part('DM02Bridge:DIN96',f'J{number}','09032966824',1,nets,
                  'Connector_DIN:DIN41612_C_3x32_Female_Vertical_THT')
        self.ports[f'J{number}']={p:n for p,n in nets.items() if n is not None}

    def finish(self):
        for kind,items in self.gates.items():
            width=6 if kind=='04' else 4
            for first in range(0,len(items),width):
                self.ref+=1;ref=f'U{self.ref}'
                symbol='74HCT04' if kind=='04' else '74LS'+kind
                fp='Package_DIP:DIP-14_W7.62mm'
                for u in range(1,width+1):
                    nets=items[first+u-1] if first+u<=len(items) else (('GND',None) if kind=='04' else ('GND','GND',None))
                    pins=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04'
                          else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[u-1]
                    self.part('74xx:'+symbol,ref,'CD74HCT'+kind+'E',u,
                              {str(p):n for p,n in zip(pins,nets)},fp)
                self.part('74xx:'+symbol,ref,'CD74HCT'+kind+'E',width+1,{'14':'5V','7':'GND'},fp)
        for i in range(1,self.ref+1):
            self.part('Device:C',f'C{i}','100nF',1,{'1':'5V','2':'GND'},
                      'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
        return self.text()


def qualifier():
    d=Board('MQ1')
    for first in (0,8):d.buf(BITS('ADDRESS',16)[first:first+8],BITS('LIVE_ADDRESS',16)[first:first+8])
    d.reduce('08',BITS('LIVE_ADDRESS',16)[8:],'PAGE_FF')
    d.gate('04','MEM_n','MEM_READ')
    d.reduce('08',['PAGE_FF','MEM_READ','LOAD_n10','ME1_RESET_n'],'IO_READ_VALID')
    d.port('J1',['5V','GND']+BITS('ADDRESS',16)+['MEM_n','LOAD_n10','ME1_RESET_n'],24)
    d.port('J2',['5V','GND']+BITS('LIVE_ADDRESS',16)+['IO_READ_VALID'],20)
    return d


def bridge():
    d=Board('BR1');plan=contact_plan()
    d.buf(['RESET_n']+['RESET_BASE']*3+['GND']*4,
          ['RESET_BASE','RESET_LOGIC','RESET_LATCH','RESET_FAN']+[None]*4)
    # Source roots isolate R2 output latches from the four outgoing branches.
    for source,root in (('IO_ADDRESS','W_ADDR_ROOT'),('IO_DATA','W_DATA_ROOT'),('LIVE_ADDRESS','R_ADDR_ROOT')):
        d.buf(BITS(source),BITS(root))
    d.decoder(BITS('LIVE_ADDRESS')[:4],'LO')
    d.decoder(BITS('LIVE_ADDRESS')[4:],'HI')
    # Exact routes: FF03 text, FF10/20/30 independent qualification fixtures.
    for index in range(4):
        slot=index+5
        d.gate('32',f'HI{index}_n',f'LO{3 if index==0 else 0}_n',f'BAD_ADDR{index}')
        d.gate('32',f'BAD_ADDR{index}',f'SLOT{slot}_PRESENT_n',f'NO_MATCH{index}')
        d.gate('04',f'NO_MATCH{index}',f'MATCH{index}')
        d.resistor(f'SLOT{slot}_PRESENT_n','5V','10k')
        for bit in range(8):d.resistor(f'SLOT{slot}_R_DATA{bit}','GND','100k')
    d.reduce('32',BITS('MATCH',4),'ANY_MATCH')
    d.reduce('08',['ANY_MATCH','IO_READ_VALID','RESET_LOGIC'],'RETURN_VALID')
    d.gate('04','RETURN_VALID','RETURN_DISABLE')
    # Each enable branch drives only two mux pins. Select branches drive two.
    d.buf(['LIVE_ADDRESS4']*2+['LIVE_ADDRESS5']*2+['RETURN_DISABLE']*4,
          ['SEL0_A','SEL0_B','SEL1_A','SEL1_B']+BITS('MUX_DISABLE',4))
    for pair in range(4):
        nets={'16':'5V','8':'GND','14':'SEL0_'+('A' if pair<2 else 'B'),
              '2':'SEL1_'+('A' if pair<2 else 'B'),'1':f'MUX_DISABLE{pair}','15':f'MUX_DISABLE{pair}'}
        for bit,ins,out in ((pair*2,[6,5,4,3],7),(pair*2+1,[10,11,12,13],9)):
            nets.update({str(p):f'SLOT{slot}_R_DATA{bit}' for p,slot in zip(ins,range(5,9))})
            nets[str(out)]=f'IO_INPUT{bit}'
        d.ic('153',nets)
    # NAND SR latch: reset clears ARMED even if raw strobe remains high.
    # Set is possible only during a low strobe. This prevents a reset-release
    # edge from being mistaken for a new write event.
    d.gate('04','IO_STROBE','STROBE_LOW')
    d.gate('00','RESET_LATCH','STROBE_LOW','ARM_SET_n')
    d.gate('00','ARM_SET_n','ARMED_n','ARMED')
    d.gate('00','RESET_LATCH','ARMED','ARMED_n')
    d.gate('08','IO_STROBE','ARMED','ARMED_STROBE')
    d.gate('08','ARMED_STROBE','RESET_LOGIC','WRITE_EVENT')
    # Replicate controls before each slot's local buffer.
    d.buf(['WRITE_EVENT']*4+['RESET_FAN']*4,
          [f'S{n}_W_ROOT' for n in range(5,9)]+[f'S{n}_RESET_ROOT' for n in range(5,9)])
    d.buf(['IO_READ_VALID']+['READ_ROOT']*4+['GND']*3,
          ['READ_ROOT']+[f'S{n}_R_ROOT' for n in range(5,9)]+[None]*3)
    for slot in range(5,9):
        for root,port in (('W_ADDR_ROOT','W_ADDR'),('W_DATA_ROOT','W_DATA'),('R_ADDR_ROOT','R_ADDR')):
            d.buf(BITS(root),BITS(f'SLOT{slot}_'+port))
        d.buf([f'S{slot}_W_ROOT',f'S{slot}_R_ROOT',f'S{slot}_RESET_ROOT']+['GND']*5,
              [f'SLOT{slot}_W_STROBE',f'SLOT{slot}_R_VALID',f'SLOT{slot}_RESET_n']+[None]*5)
        d.slot(slot,plan['peripheral_cards'][slot-5]['connector'])
    d.port('J1',['5V','GND']+BITS('IO_ADDRESS')+BITS('IO_DATA')+['IO_STROBE'],20)
    d.port('J2',['5V','GND']+BITS('LIVE_ADDRESS',16)+['IO_READ_VALID'],20)
    d.port('J3',['5V','GND']+BITS('IO_INPUT'))
    d.port('J4',['5V','GND','RESET_n'])
    return d


def generate():
    expected=library_text()
    if LIBRARY.exists() and LIBRARY.read_text()!=expected:
        raise ValueError('DM02Bridge symbol differs; review before replacement')
    LIBRARY.parent.mkdir(parents=True,exist_ok=True)
    if not LIBRARY.exists():LIBRARY.write_text(expected)
    DEST.mkdir(parents=True,exist_ok=True)
    ports={}
    for factory in (qualifier,bridge):
        board=factory();text=board.finish();path=DEST/(board.name+'.sch')
        path.write_text(text);ports[board.name]=board.ports
    write_json(DEST/'boundary.json',dict(revision='CP1-BR1',ports=ports,
        internal_headers='Non-fitted logical boundaries; combine nets on MC1 boards, not extra production connectors.',
        physical_qualification=False))
    return ports


if __name__=='__main__':generate()

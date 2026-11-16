"""Separate TX1 mailbox and autonomous 8N1 candidate, explicit physical pins."""
from dm02.common import ROOT,write_json
from dm02.connector_plan import generate as contact_plan
from .drawing import Drawing
from .io_bridge_candidate import Board,BITS,DEC_OUT

DEST=ROOT/'Circuits/KiCad/Text/candidates'
LIBRARY=ROOT/'Circuits/KiCad/Libraries/DM02Text.lib'
D273=(3,4,7,8,13,14,17,18)
Q273=(2,5,6,9,12,15,16,19)


class TextBoard(Board):
    def __init__(self):
        Drawing.__init__(self,'DM-02 TX1 serial text candidate','CP1-TX1',[
            'Independent DIP/THT candidate; local 4 MHz clock, nominal 9600 baud 8N1.',
            'One persistent mailbox credit; separate transmit register; reset aborts frames.',
            'J2 is 5 V TTL TX/GND, not RS-232. Receiver and cable require qualification.',
            'Native simulation excludes metastability, analog edges and physical acceptance.'],
            row_step=5600,page=('User',33110,220000))
        self.name='TX1';self.ref=0;self.res=0;self.ports={}
        self.gates={k:[] for k in ('04','08','00','32')}
        self.flops=[];self.muxes={}

    def device(self,kind,nets):
        self.ref+=1;ref=f'U{self.ref}'
        pins={'273':20,'157':16,'161':16,'151':16,'154':24}[kind]
        symbol='74HCT273' if kind=='273' else '74LS'+kind
        self.part('74xx:'+symbol,ref,'CD74HCT'+kind+'E',1,nets,
                  f'Package_DIP:DIP-{pins}_W{15.24 if pins==24 else 7.62:.2f}mm')
        return ref

    def ff(self,data,clock,q,clear='RESET0',preset='5V',qn=None):
        self.flops.append((data,clock,q,clear,preset,qn))

    def mux(self,select,zero,one,out):
        self.muxes.setdefault(select,[]).append((zero,one,out))

    def xor(self,a,b,out):
        self.gate('00',a,b,out+'_N')
        self.gate('00',a,out+'_N',out+'_A')
        self.gate('00',b,out+'_N',out+'_B')
        self.gate('00',out+'_A',out+'_B',out)

    def register(self,ins,outs,clock,enable,reset='RESET0'):
        ds=[o+'_D' for o in outs]
        for old,new,target in zip(outs,ins,ds):self.mux(enable,old,new,target)
        self.device('273',{'1':reset,'10':'GND','11':clock,'20':'5V',
            **{str(p):n for p,n in zip(D273,ds)},**{str(p):n for p,n in zip(Q273,outs)}})

    def count(self,clock,outs,enable='5V',load_n='5V',carry=None,reset='RESET1'):
        self.device('161',{'1':reset,'2':clock,'3':'GND','4':'GND','5':'GND','6':'GND',
            '7':enable,'8':'GND','9':load_n,'10':'5V','15':carry,'16':'5V',
            **{str(p):n for p,n in zip((14,13,12,11),outs)}})

    def decode(self,ins,prefix,disable0='GND',disable1='GND'):
        self.device('154',{'12':'GND','24':'5V','18':disable0,'19':disable1,
            **{str(p):n for p,n in zip((23,22,21,20),ins)},
            **{str(p):f'{prefix}{i}_n' for i,p in enumerate(DEC_OUT)}})

    def finish(self):
        for select,items in self.muxes.items():
            for first in range(0,len(items),4):
                nets={'1':select,'15':'GND','16':'5V','8':'GND'}
                for j,pins in enumerate(((2,3,4),(5,6,7),(11,10,9),(14,13,12))):
                    row=items[first+j] if first+j<len(items) else ('GND','GND',None)
                    nets.update({str(p):n for p,n in zip(pins,row)})
                self.device('157',nets)
        for first in range(0,len(self.flops),2):
            self.ref+=1;ref=f'U{self.ref}';fp='Package_DIP:DIP-14_W7.62mm'
            for j,pins in enumerate(((2,3,5,1,4,6),(12,11,9,13,10,8))):
                row=self.flops[first+j] if first+j<len(self.flops) else ('GND','GND',None,'5V','5V',None)
                self.part('74xx:74HC74',ref,'CD74HCT74E',j+1,{str(p):n for p,n in zip(pins,row)},fp)
            self.part('74xx:74HC74',ref,'CD74HCT74E',3,{'14':'5V','7':'GND'},fp)
        return super().finish()


def candidate():
    d=TextBoard()
    d.buf(['RESET_n']*2+['RESET_A']*3+['RESET_B']*2+['GND'],
          ['RESET_A','RESET_B']+BITS('RESET',5)+[None])
    d.buf(['OSC']+['BAUD']*3+['ACK','REQ','TAKE','GND'],
          ['OSC_CLK','BAUD_A','BAUD_B','BAUD_C','ACK_W','REQ_W','TAKE_DATA',None])
    # W_STROBE is the transaction clock. Decode/data must settle before its edge.
    d.reduce('32',BITS('W_ADDR')[4:],'W_HIGH')
    d.decode(BITS('W_ADDR')[:4],'W',disable0='W_HIGH')
    d.gate('04','W0_n','TEXT_WRITE');d.gate('04','W4_n','CONTROL_WRITE')
    d.xor('REQ_W','ACK_W','PENDING');d.gate('04','PENDING','EMPTY')
    d.reduce('08',['EMPTY','INIT','RESET_n'],'READY')
    d.gate('08','READY','TEXT_WRITE','ACCEPT')
    d.register(BITS('W_DATA'),BITS('MAIL'),'W_STROBE','ACCEPT')
    d.xor('REQ','ACCEPT','REQ_D');d.ff('REQ_D','W_STROBE','REQ')
    d.gate('04','READY','NOT_READY')
    d.reduce('08',['TEXT_WRITE','NOT_READY','INIT'],'REJECT')
    d.gate('08','CONTROL_WRITE','W_DATA1','CLEAR_OVERRUN')
    d.gate('04','CLEAR_OVERRUN','KEEP_OVERRUN')
    d.gate('08','OVERRUN','KEEP_OVERRUN','OLD_OVERRUN')
    d.gate('32','OLD_OVERRUN','REJECT','OVERRUN_D')
    d.ff('OVERRUN_D','W_STROBE','OVERRUN')
    # Synchronous divide-by-208 plus toggling FF: 4 MHz / 416 = 9615.3846 baud.
    d.part('DM02Text:ACH', 'Y1','ACH-4.000MHZ-EK',1,
           {'1':None,'4':'GND','5':'OSC','8':'5V'},'Oscillator:Oscillator_DIP-8')
    d.count('OSC_CLK',BITS('DIV',4),load_n='DIV_LOAD_n',carry='DIV_CARRY')
    d.count('OSC_CLK',BITS('DIV',8)[4:],enable='DIV_CARRY',load_n='DIV_LOAD_n')
    d.decode(BITS('DIV',8)[4:],'DIV_HI')
    d.gate('04','DIV_HI12_n','DIV_12')
    d.gate('08','DIV_12','DIV_CARRY','DIV_END')
    d.gate('04','DIV_END','DIV_LOAD_n')
    d.mux('DIV_END','BAUD','BAUD_n','BAUD_D')
    d.ff('BAUD_D','OSC_CLK','BAUD',clear='RESET1',qn='BAUD_n')
    d.part('Device:C','CY1','100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
    # Explicit init and bundled-data request synchronizer; ACK follows capture.
    d.ff('5V','BAUD_A','INIT1',clear='RESET2');d.ff('INIT1','BAUD_A','INIT2',clear='RESET2');d.ff('INIT2','BAUD_A','INIT',clear='RESET2')
    d.ff('REQ','BAUD_B','REQ1',clear='RESET3');d.ff('REQ1','BAUD_B','REQ2',clear='RESET3')
    d.xor('REQ2','ACK','LOCAL_PENDING')
    d.decode(BITS('STATE',4),'STATE_EQ')
    d.gate('04','STATE_EQ0_n','IDLE');d.gate('04','STATE_EQ9_n','STOP')
    d.reduce('08',['LOCAL_PENDING','INIT','IDLE'],'TAKE')
    d.mux('TAKE','ACK','REQ2','ACK_D');d.ff('ACK_D','BAUD_B','ACK',clear='RESET3')
    d.register(BITS('MAIL'),BITS('TX_DATA'),'BAUD_C','TAKE_DATA',reset='RESET4')
    d.gate('32','STATE_EQ0_n','TAKE','COUNT_ENABLE')
    d.count('BAUD_C',BITS('STATE',4),enable='COUNT_ENABLE',load_n='STATE_EQ9_n',reset='RESET4')
    # State 0 takes/start; states 1..8 emit D0..D7; state 9 emits stop/returns 0.
    select_data=['TX_DATA7']+BITS('TX_DATA')[:7]
    d.device('151',{'16':'5V','8':'GND','7':'GND','11':'STATE0','10':'STATE1','9':'STATE2',
        '5':'SELECTED_BIT','6':None,**{str(p):n for p,n in zip((4,3,2,1,15,14,13,12),select_data)}})
    d.gate('04','TAKE','NO_TAKE');d.gate('08','IDLE','NO_TAKE','IDLE_BIT')
    d.reduce('08',['STATE_EQ0_n','STATE_EQ9_n','SELECTED_BIT'],'DATA_BIT')
    d.reduce('32',['IDLE_BIT','DATA_BIT','STOP'],'TX_D')
    d.ff('TX_D','BAUD_C','TX_LOGIC',clear='5V',preset='RESET4')
    # Private status return. Upper-nibble rejection and reset/valid gate enables.
    d.reduce('32',BITS('R_ADDR')[4:],'R_HIGH')
    d.gate('00','R_VALID','RESET_n','READ_DISABLE')
    d.decode(BITS('R_ADDR')[:4],'R',disable0='R_HIGH',disable1='READ_DISABLE')
    d.gate('04','R3_n','STATUS_READ')
    d.gate('08','STATUS_READ','READY','R_DATA0')
    d.gate('08','STATUS_READ','OVERRUN','R_DATA1')
    # Passive terminal header carries no power back into the computer.
    d.buf(['TX_LOGIC']+['GND']*7,['TX_BUFFER']+[None]*7)
    d.resistor('TX_BUFFER','TX_PIN','1k')
    d.part('Connector_Generic:Conn_01x02','J2','TTL_TX_GND',1,{'1':'GND','2':'TX_PIN'},
           'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
    d.ports['J2']={'1':'GND','2':'TX_PIN'}
    plan=contact_plan()['peripheral_cards'][0]['connector']
    nets={p['pin']:p['net'] for p in plan['pins']}
    for pin,net in list(nets.items()):
        if net and net.startswith('SLOT5_'):net=net.removeprefix('SLOT5_')
        if net=='PRESENT_n':net='GND'
        if net in [f'R_DATA{i}' for i in range(2,7)]:net='GND'
        if net=='R_DATA7':net='STATUS_READ'
        nets[pin]=net
    d.part('DM02Bridge:DIN96','J1','09031966921',1,nets,
           'Connector_DIN:DIN41612_C_3x32_Male_Horizontal_THT')
    d.ports['J1']={p:n for p,n in nets.items() if n is not None}
    return d


def generate():
    text='''EESchema-LIBRARY Version 2.4
#encoding utf-8
DEF ACH Y 0 40 Y Y 1 F N
F0 "Y" 0 300 50 H V C CNN
F1 "ACH" 0 200 50 H V C CNN
DRAW
S -200 100 200 -200 0 1 10 f
X NC 1 -400 0 200 R 30 30 1 1 N
X GND 4 0 -400 200 U 30 30 1 1 W
X OUT 5 400 0 200 L 30 30 1 1 O
X VDD 8 0 300 200 D 30 30 1 1 W
ENDDRAW
ENDDEF
#End Library
'''
    if LIBRARY.exists() and LIBRARY.read_text()!=text:raise ValueError('Changed TX1 oscillator symbol')
    if not LIBRARY.exists():LIBRARY.write_text(text)
    DEST.mkdir(parents=True,exist_ok=True)
    d=candidate();(DEST/'TX1.sch').write_text(d.finish())
    write_json(DEST/'boundary.json',dict(revision='CP1-TX1',ports=d.ports,
        physical_qualification=False,oscillator_pin='Y1.5',terminal='J2.2 TTL TX, J2.1 GND'))


if __name__=='__main__':generate()

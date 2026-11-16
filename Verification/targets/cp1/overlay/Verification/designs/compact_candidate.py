"""CP1: owned DIP memories, enabled registers, counters and shared DATA.

Every emitted connection is a physical symbol pin. Behaviour comes from the
separately implemented component models, never from this drawing generator.
"""
from collections import defaultdict
from pathlib import Path
import json
from dm02.common import ROOT,VROOT,BUILD
from dm02.legacy import read_sheet,connectivity,library
from designs.drawing import Drawing
from designs.clock_candidate import drawing as clock_drawing

DEST=ROOT/'Circuits/KiCad/Compact/candidates'
DIP=lambda n,w=7.62:f'Package_DIP:DIP-{n}_W{w:.2f}mm'
BITS=lambda p,n=8,start=0:[f'{p}{i}' for i in range(start,start+n)]
INPUT377=[3,4,7,8,13,14,17,18]
OUTPUT377=[2,5,6,9,12,15,16,19]
SOURCE_GROUPS={'AL1':0,'RG1':1,'PC1':2,'SP1':2,'MA1':3,'ME1':3}
GROUP_REFS={'AL1':['U13','U14','U15'],'RG1':['U7','U12','U17','U22'],
            'PC1':['U5','U6'],'SP1':['U20','U21'],'MA1':['U20','U21'],'ME1':['U9']}
PHASES={'CW1':[1],'SQ1':[0,1,2,3],'PC1':[3],'AL1':[1,3],'RG1':[3],
        'SP1':[1,2,3],'MA1':[1,2,3],'ME1':[0,2,3],'BF1':[]}
LEAVES=[(f'PH{p}',f'{name}_PH{p}') for name,ps in PHASES.items() for p in ps]+[
    ('INIT_CLK',f'{name}_INIT_CLK') for name in ('RG1','SP1','MA1')]+[
    ('RESET_n',f'{name}_RESET_n') for name in PHASES]
CHANGES={'CD74AC175M96':('CD74ACT175E',DIP(16)),
    'CD74HCT161M96':('CD74HCT161E',DIP(16)),
    'CD74HCT377M96':('SN74HC377N',DIP(20)),
    'CD74HCT154M96':('CD74HCT154E',DIP(24,15.24)),
    'SN74AHCT00DR':('SN74AHCT00N',DIP(14)),
    'SN74AHCT08DR':('SN74AHCT08N',DIP(14))}

def custom_library():
    """Independent datasheet pin maps, including true NC pins."""
    maps={
        'M27C1024':({**{21+i:('A'+str(i),'I') for i in range(9)},
            **{31+i:('A'+str(i+9),'I') for i in range(7)},
            **{19-i:('Q'+str(i),'T') for i in range(8)},
            **{10-i:('Q'+str(i+8),'T') for i in range(8)},
            1:('VPP','W'),2:('~E','I'),11:('VSS','W'),20:('~G','I'),30:('VSS','W'),
            38:('NC','N'),39:('~P','I'),40:('VCC','W')},40),
        'UM61512':({**{p:('A'+str(i),'I') for i,p in enumerate([12,11,10,9,8,7,6,5,27,26,23,25,4,28,3,31])},
            **{p:('DQ'+str(i),'B') for i,p in enumerate([13,14,15,17,18,19,20,21])},
            1:('NC','N'),2:('NC','N'),16:('GND','W'),22:('~CE1','I'),24:('~OE','I'),
            29:('~WE','I'),30:('CE2','I'),32:('VCC','W')},32),
        '74HCT191':({15:('D0','I'),1:('D1','I'),10:('D2','I'),9:('D3','I'),
            3:('Q0','O'),2:('Q1','O'),6:('Q2','O'),7:('Q3','O'),
            4:('~CE','I'),5:('DOWN','I'),11:('~LOAD','I'),14:('CLK','I'),
            12:('TC','O'),13:('~RCO','O'),8:('GND','W'),16:('VCC','W')},16)}
    lines=['EESchema-LIBRARY Version 2.4','#encoding utf-8']
    for name,(pins,count) in maps.items():
        assert set(pins)==set(range(1,count+1))
        height=50*(count//2+1)
        lines += [f'# {name}',f'DEF {name} U 0 40 Y Y 1 F N',f'F0 "U" 0 {height+100} 50 H V C CNN',
                  f'F1 "{name}" 0 {height} 50 H V C CNN','DRAW',f'S -500 {height} 500 {-height} 0 1 10 f']
        for pin,(label,kind) in sorted(pins.items()):
            left=pin<=count//2;index=pin-1 if left else count-pin
            lines.append(f'X {label} {pin} {-700 if left else 700} {height-100-100*index} 200 {"R" if left else "L"} 50 50 1 1 {kind}')
        lines+=['ENDDRAW','ENDDEF']
    lines+=['#End Library']
    p=ROOT/'Circuits/KiCad/Libraries/DM02-Compact.lib';p.write_text('\n'.join(lines)+'\n')
    library.cache_clear()

class Board:
    def __init__(self,name,source=None):
        self.name=name;self.items=[];self.gates=defaultdict(list);self.serial=100
        if source:
            sheet=read_sheet(source);nets=connectivity(sheet)
            names={tuple(node):(n['labels'][0] if n['labels'] else 'NET_'+str(i) if len(n['nodes'])>1 else None)
                   for i,n in enumerate(nets) for node in n['nodes']}
            for c in sheet['components']:
                if c['ref'].startswith('#') or c['ref'].startswith('C'):continue
                self.add(c['lib_id'],c['ref'],c['value'],{p['number']:names[c['ref'],p['number']] for p in c['pins']},c['footprint'],c['unit'])
    def add(self,lib,ref,value,nets,fp,unit=1):
        value,fp=CHANGES.get(value,(value,fp))
        self.items.append(dict(lib=lib,ref=ref,value=value,nets={str(k):v for k,v in nets.items()},fp=fp,unit=unit));return ref
    def ic(self,lib,value,nets,pins=20,ref=None):
        if ref is None:self.serial+=1;ref='U'+str(self.serial)
        return self.add(lib,ref,value,nets,DIP(pins))
    def get(self,ref):return next(i for i in self.items if i['ref']==ref)
    def remove(self,*refs):self.items=[i for i in self.items if i['ref'] not in refs]
    def gate(self,kind,*nets):self.gates[kind].append(nets)
    def connector(self,ref,signals):
        self.add(f'Connector_Generic:Conn_01x{len(signals):02}',ref,ref,dict(enumerate(signals,1)),
                 f'Connector_PinHeader_2.54mm:PinHeader_1x{len(signals):02}_P2.54mm_Vertical')
    def mux(self,select,a,b,out,ref=None):
        assert len(a)==len(b)==len(out)==4
        ns={1:select,15:'GND',16:'5V',8:'GND'}
        for ap,bp,qp,x,y,z in zip([2,5,11,14],[3,6,10,13],[4,7,9,12],a,b,out):ns.update({ap:x,bp:y,qp:z})
        return self.ic('74xx:74LS157','SN74AHCT157N',ns,16,ref)
    def buffer(self,a,b,oe='GND',ref=None,owned=False):
        assert len(a)==len(b)==8
        if owned:
            ns={1:'5V',19:oe,10:'GND',20:'5V',**dict(zip(range(2,10),a)),**dict(zip(range(18,10,-1),b))}
            return self.ic('74xx:74LS245','SN74HCT245N',ns,20,ref)
        ns={1:oe,19:oe,10:'GND',20:'5V',**dict(zip([2,4,6,8,17,15,13,11],a)),**dict(zip([18,16,14,12,3,5,7,9],b))}
        return self.ic('74xx:74HCT244','SN74AHCT244N',ns,20,ref)
    def storage(self,kind,a,q,clock,control='GND',ref=None):
        assert len(a)==len(q)==8
        if kind=='574':ns={1:control,11:clock,10:'GND',20:'5V',**dict(zip(range(2,10),a)),**dict(zip(range(19,11,-1),q))}
        else:ns={1:control,11:clock,10:'GND',20:'5V',**dict(zip(INPUT377,a)),**dict(zip(OUTPUT377,q))}
        part='SN74HC377N' if kind=='377' else 'CD74HCT273E' if kind=='273' else 'SN74HCT'+kind+'N'
        return self.ic('74xx:74LS'+kind,part,ns,20,ref)
    def ff(self,d,clock,q,nq,clear='RESET_n',ref=None):
        if ref is None:self.serial+=1;ref='U'+str(self.serial)
        self.add('74xx:74HC74',ref,'SN74AHC74N',{1:clear,2:d,3:clock,4:'5V',5:q,6:nq},DIP(14),1)
        self.add('74xx:74HC74',ref,'SN74AHC74N',{13:'5V',12:'GND',11:'GND',10:'5V',9:None,8:None},DIP(14),2)
        self.add('74xx:74HC74',ref,'SN74AHC74N',{7:'GND',14:'5V'},DIP(14),3)
    def finish(self):
        for kind,uses in self.gates.items():
            width=6 if kind=='04' else 4
            for start in range(0,len(uses),width):
                self.serial+=1;ref=f'U{self.serial}'
                for u in range(width):
                    pp=([(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)] if kind=='04' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)])[u]
                    nn=uses[start+u] if start+u<len(uses) else (('GND',None) if kind=='04' else ('GND','GND',None))
                    self.add('74xx:'+('74HCT04' if kind=='04' else '74LS'+kind),ref,'SN74AHCT'+kind+'N',dict(zip(pp,nn)),DIP(14),u+1)
                self.add('74xx:'+('74HCT04' if kind=='04' else '74LS'+kind),ref,'SN74AHCT'+kind+'N',{14:'5V',7:'GND'},DIP(14),width+1)
        # Buffer local fanout in groups of four 10 pF inputs. Connector and
        # inactive-output capacitance are audited separately across the backplane.
        sinks=defaultdict(list)
        for item in self.items:
            if not item['ref'].startswith('U'):continue
            ns,symbol=item['lib'].split(':')
            for p in library(ns)[symbol]['pins']:
                if p['unit'] not in (0,item['unit']) or p['convert'] not in (0,1) or p['kind']!='I':continue
                net=item['nets'][p['number']]
                if net and net not in ('5V','GND'):sinks[net].append((item,p['number']))
        pairs=[]
        for net,loads in sinks.items():
            if len(loads)<=4:continue
            assert len(loads)<=16,(self.name,net,len(loads))
            for i in range(0,len(loads),4):
                leaf=f'{net}_FAN{i//4}';pairs.append((net,leaf))
                for item,pin in loads[i:i+4]:item['nets'][pin]=leaf
        for i in range(0,len(pairs),8):
            chunk=pairs[i:i+8]+[('GND',None)]*(8-len(pairs[i:i+8]))
            self.buffer([a for a,z in chunk],[z for a,z in chunk])
        d=Drawing('DM-02 compact '+self.name,'CP1',['Owned-DIP compact candidate; physical qualification pending.',
            'Shared DATA with phase-qualified output enables; explicit init/counter clocks.',
            'Pin-derived simulation and independent KiCad export are required.'],row_step=4000 if self.name=='BP2' else 2200,page=('A0',46811,33110))
        for i in self.items:d.part(i['lib'],i['ref'],i['value'],i['unit'],i['nets'],i['fp'])
        for index,ref in enumerate(sorted({i['ref'] for i in self.items if i['ref'].startswith(('U','Y'))}),1):
            d.part('Device:C','C'+str(index),'100nF',1,{'1':'5V','2':'GND'},'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm')
        return d.text()

def combine(board,first,second):
    a,b=board.get(first),board.get(second)
    assert a['nets']['9']==b['nets']['9'] and a['nets']['1']==b['nets']['1']
    ds=[i['nets'][str(p)] for i in (a,b) for p in (4,5,12,13)]
    qs=[i['nets'][str(p)] for i in (a,b) for p in (2,7,10,15)]
    assert all(i['nets'][str(p)] is None for i in (a,b) for p in (3,6,11,14))
    board.remove(first,second);board.storage('273',ds,qs,a['nets']['9'],a['nets']['1'],first)

def registers(source):
    b=Board('RG2',source)
    b.remove('U23','U24','U25','U26')
    # Shared zero-data and oscillator-driven reset initialization, with CE low.
    # RESET_n is released on the falling oscillator edge by the physical C1 synchronizer.
    for half in range(2):b.mux('RESET_n',['GND']*4,BITS('INPUT',4,4*half),BITS('INIT_DATA',4,4*half))
    b.mux('RESET_n',['INIT_CLK']*4,[r+'_CLOCK' for r in 'BCHL'],[r+'_CAPTURE' for r in 'BCHL'])
    for i,r in enumerate('BCHL'):
        base=3+5*i;b.remove(*(f'U{x}' for x in range(base,base+4)))
        b.storage('377',BITS('INIT_DATA'),BITS(r),r+'_CAPTURE',r+'_CE_n',f'U{base}')
        b.gate('08',r+'_load_n','RESET_n',r+'_CE_n')
        b.gate('04',r+'_out_n',r+'_OUT');b.gate('00',r+'_OUT','RESET_n',r+'_OE_n')
    b.connector('J90',['5V','GND','INIT_CLK'])
    return b

def shared_bus(boards):
    for name,refs in GROUP_REFS.items():
        b=boards[name]
        for ref in refs:
            item=b.get(ref);ns=item['nets']
            if item['value']=='SN74HCT245N':ins=[ns[str(p)] for p in range(2,10)];oe=ns['19']
            else:
                assert ns['1']==ns['19'];oe=ns['1'];ins=[ns[str(p)] for p in [2,4,6,8,17,15,13,11]]
            b.remove(ref);b.buffer(ins,BITS('SOURCE'),oe,ref=ref,owned=True)
        b.connector('J91',['5V','GND']+BITS('SOURCE'))
    b=Board('BF2')
    # Four small source buses feed a trunk; one receiver buffer drives DATA.
    # Group enables are ANDs of active-low, already phase-qualified source OEs.
    groups=[[0,5,6],[1,2,3,4],[10,11,12,13],[7,8,9]]
    group_disables=[]
    for group,ids in enumerate(groups):
        chain='ENABLE_n'+str(ids[0])
        for i,source in enumerate(ids[1:]):
            nxt=f'GROUP{group}_AND{i}';b.gate('08',chain,'ENABLE_n'+str(source),nxt);chain=nxt
        b.buffer(BITS(f'BRANCH{group}_'),BITS('TRUNK'),chain,owned=True)
        group_disables.append(chain)
        b.connector('J'+str(group+1),['5V','GND']+BITS(f'BRANCH{group}_'))
    b.gate('08',group_disables[0],group_disables[1],'IDLE01')
    b.gate('08',group_disables[2],group_disables[3],'IDLE23')
    b.gate('08','IDLE01','IDLE23','BUS_IDLE')
    b.gate('04','RESET_n','RESET');b.gate('32','BUS_IDLE','RESET','RECEIVER_OE_n')
    b.buffer(BITS('TRUNK'),BITS('DATA'),'RECEIVER_OE_n',owned=True)
    b.connector('J5',['5V','GND']+BITS('DATA'))
    b.connector('J6',['5V','GND']+BITS('ENABLE_n',14))
    b.connector('J7',['5V','GND','RESET_n'])
    boards['BF1']=b

def distribution():
    b=Board('DT2');pairs=[]
    for root in dict(LEAVES):
        leaves=[leaf for r,leaf in LEAVES if r==root]
        # Each output drives at most four buffer inputs (40 pF + 5 pF route).
        for group in range((len(leaves)+3)//4):
            branch=f'{root}_BR{group}';pairs.append((root,branch))
            pairs.extend((branch,leaf) for leaf in leaves[4*group:4*group+4])
    for i in range(0,len(pairs),8):
        chunk=pairs[i:i+8]+[('GND',None)]*(8-len(pairs[i:i+8]))
        b.buffer([a for a,z in chunk],[z for a,z in chunk])
    b.connector('J1',['5V','GND']+BITS('PH',4)+['INIT_CLK','RESET_n'])
    # Keep connectors within the vendored symbol catalogue's 40-pin range.
    b.connector('J2',['5V','GND']+[leaf for root,leaf in LEAVES])
    return b

def counters(mar=False):
    b=Board('MA2' if mar else 'SP2')
    b.buffer(BITS('DATA'),BITS('INPUT'),ref='U1')
    # Delay the falling COUNT clock to the opposite oscillator edge. Commands
    # and asynchronous transfer loads settle while all ripple clocks are high.
    b.gate('04','INIT_CLK','OSC_N')
    b.ff('PH2','OSC_N','PH2_D',None,clear='5V',ref='U2')
    b.ff('PH2_D','INIT_CLK','PH2_D2',None,ref='U8')
    # Keep zero preset data stable through asynchronous LOAD release. A separate
    # oscillator edge enables functional data only after the 2 ns hold interval.
    b.ff('RESET_n','INIT_CLK','LOAD_READY',None,ref='U7')
    b.gate('04','PH2_D2','PH2_D2_n');b.gate('32','PH3','PH2_D2_n','COUNT_PHASE')
    b.gate('08','PH2_D','PH2_D2_n','TRANSFER_WINDOW')
    if mar:
        b.gate('32','FETCH0','PC_TRANSFER','FROM_PC');b.gate('32','FROM_PC','SP_TRANSFER','TRANSFER')
        for source in ('PC','SP'):
            for half in range(2):b.storage('574',BITS(source,8,8*half),BITS(source+'_SNAPSHOT',8,8*half),'PH1')
        for nibble in range(4):
            j=4*nibble
            b.mux('SP_TRANSFER',BITS('PC_SNAPSHOT',4,j),BITS('SP_SNAPSHOT',4,j),BITS('TRANSFER_DATA',4,j))
            b.mux('TRANSFER',BITS('INPUT',4,j%8),BITS('TRANSFER_DATA',4,j),BITS('LOAD_DATA',4,j))
            b.mux('LOAD_READY',['GND']*4,BITS('LOAD_DATA',4,j),BITS('PRESET',4,j))
        b.gate('08','TRANSFER','TRANSFER_WINDOW','TRANSFER_LOAD')
    else:
        for half in range(2):b.mux('LOAD_READY',['GND']*4,BITS('INPUT',4,4*half),BITS('PRESET',4,4*half))
    b.gate('32','INC','GND' if mar else 'DEC','COUNT_REQUEST')
    b.gate('00','COUNT_REQUEST','RESET_n','COUNT_ENABLE_n')
    b.gate('32','COUNT_PHASE','COUNT_ENABLE_n','COUNT_CLOCK')
    b.gate('04','PH3','PH3_n')
    for half,name in enumerate(('LOW','HIGH')):
        b.gate('04',name+'_load_n',name+'_LOAD_RAW')
        b.gate('08',name+'_LOAD_RAW','PH3_n',name+'_LOAD')
        if mar:b.gate('32',name+'_LOAD','TRANSFER_LOAD',name+'_PRESET')
        b.gate('04',name+'_PRESET' if mar else name+'_LOAD',name+'_PRESET_n')
        b.gate('08',name+'_PRESET_n','RESET_n',name+'_PL_n')
        b.gate('04',name+'_out_n',name+'_OUT');b.gate('00',name+'_OUT','RESET_n',name+'_OE_n')
        b.buffer(BITS('STATE',8,half*8),BITS('DATA'),name+'_OE_n',ref=f'U{20+half}',owned=True)
        if not mar:b.buffer(BITS('STATE',8,half*8),BITS('ADDRESS',8,half*8),ref=f'U{22+half}')
    for nibble in range(4):
        ns={4:'COUNT_ENABLE_n',5:'GND' if mar else 'DEC',11:('LOW' if nibble<2 else 'HIGH')+'_PL_n',
            14:'COUNT_CLOCK' if nibble==0 else 'RCO'+str(nibble-1),12:None,13:'RCO'+str(nibble),8:'GND',16:'5V'}
        ns.update(dict(zip([15,1,10,9],BITS('PRESET',4,4*nibble if mar else 4*(nibble%2)))))
        ns.update(dict(zip([3,2,6,7],BITS('STATE',4,4*nibble))))
        b.ic('DM02-Compact:74HCT191','CD74HCT191E',ns,16,f'U{3+nibble}')
    b.connector('J1',['5V','GND','PH1','PH3','RESET_n','INC']+
        (['FETCH0','PC_TRANSFER','SP_TRANSFER'] if mar else ['DEC'])+
        ['LOW_load_n','HIGH_load_n','LOW_out_n','HIGH_out_n'])
    b.connector('J2',['5V','GND']+BITS('DATA'))
    b.connector('J3',['5V','GND']+BITS('STATE' if mar else 'ADDRESS',16))
    if mar:
        b.connector('J4',['5V','GND']+BITS('PC',16));b.connector('J5',['5V','GND']+BITS('SP',16))
    b.connector('J90',['5V','GND','INIT_CLK','PH2'])
    # U2 and U7 each used one half of a dual FF; consolidate the two physical
    # units, preserving their independent clocks and asynchronous clear pins.
    first=next(i for i in b.items if i['ref']=='U2' and i['unit']==2)
    second=next(i for i in b.items if i['ref']=='U7' and i['unit']==1)
    first['nets']={str(q):second['nets'][str(p)] for p,q in [(1,13),(2,12),(3,11),(4,10),(5,9),(6,8)]}
    b.remove('U7')
    return b

def generate():
    custom_library();DEST.mkdir(parents=True,exist_ok=True)
    # Use single-ROM AL1 and shared-bus module sources, rather than FD1's flash/private links.
    paths={'C1':'Power-Clock/candidates/Counted-Clock.sch','CW1':'Controller/candidates/Control-Word.sch',
        'SQ1':'Controller/candidates/Sequencer.sch','PC1':'Registers-StackPointer/candidates/Program-Counter.sch',
        'AL1':'ALU/candidates/Timed-ALU.sch','RG1':'Registers-StackPointer/candidates/General-Registers.sch',
        'ME1':'Memory/candidates/Memory-IO.sch'}
    clock_source=BUILD/'compact/clock-input.sch';clock_source.parent.mkdir(parents=True,exist_ok=True)
    clock_source.write_text(clock_drawing())
    boards={name:Board(name,clock_source if name=='C1' else ROOT/'Circuits/KiCad'/path) for name,path in paths.items()}
    boards['RG1']=registers(ROOT/'Circuits/KiCad'/paths['RG1'])
    boards['SP1']=counters();boards['MA1']=counters(True)
    b=boards['C1'];b.get('U10')['nets'].update({'6':'ROOT_P','14':'INIT_CLK','8':'RESET_P_n','12':'RESET_RELEASE_n'})
    b.connector('J90',['5V','GND','INIT_CLK','RESET_RELEASE_n'])
    b=boards['CW1'];b.remove('U1','U2')
    ns={1:'5V',2:'GND',11:'GND',20:'GND',30:'GND',38:None,39:'5V',40:'5V'}
    ns.update(dict(zip(list(range(21,30))+list(range(31,38)),BITS('ROM_A',16))))
    ns.update(dict(zip(list(range(19,11,-1))+list(range(10,2,-1)),BITS('ROM_D',16))))
    b.add('DM02-Compact:M27C1024','U1','M27C1024-10F1',ns,DIP(40,15.24))
    b=boards['AL1'];combine(b,'U2','U3')
    b=boards['ME1'];b.get('U1')['value']='W27C512-45Z'
    ram=b.get('U2');ram['lib']='DM02-Compact:UM61512';ram['value']='UM61512AK-15';ram['fp']=DIP(32)
    ram['nets']['1']=None;ram['nets']['2']=None
    combine(b,'U11','U13');combine(b,'U15','U17')
    shared_bus(boards);boards['DT1']=distribution()
    result={}
    for name,b in boards.items():
        p=DEST/(name+'.sch');p.write_text(b.finish());result[name]=str(p.relative_to(ROOT))
    (DEST/'boards.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Generated CP1',len(boards),'boards')
    return result

if __name__=='__main__':generate()

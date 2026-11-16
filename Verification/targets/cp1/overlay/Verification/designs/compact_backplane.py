"""Explicit connector-to-connector CP1 assembly, including external interfaces."""
from .compact_candidate import Board,BITS,DEST,SOURCE_GROUPS,LEAVES
from dm02.legacy import read_sheet
from dm02.common import write_json

def ports():
    p={}
    def add(board,ref,signals):p[board,ref]=['5V','GND']+signals
    for name in ('SQ1','PC1','AL1','RG1','SP1','MA1','ME1'):add(name,'J2',BITS('DATA'))
    for name,group in SOURCE_GROUPS.items():add(name,'J91',BITS(f'BRANCH{group}_'))
    add('C1','J1',['RESET_REQUEST_n','REQUEST','ACTIVE','READY','GND','STEP'])
    add('C1','J2',BITS('PH',4)+['GND',None]);add('C1','J90',['INIT_CLK','RESET_n'])
    add('CW1','J1',['CW1_PH1','CW_PH2','CW1_RESET_n','VALID'])
    add('CW1','J2',BITS('FLAG',4)+BITS('T',4)+BITS('OP'))
    add('CW1','J3',BITS('OUT_n',14,1));add('CW1','J4',BITS('LOAD_n',14,1))
    add('CW1','J5',BITS('FUN',12,1));add('CW1','J6',BITS('ALU_OP',5)+['CW_PC_n','ALU_ENABLE'])
    add('SQ1','J1',BITS('SQ1_PH',4)+['SQ1_RESET_n','RUN','RESUME','VALID','FUN1','FUN2','FUN5','CW_PC_n','OUT_n10'])
    add('SQ1','J3',BITS('T',4)+BITS('OP'))
    add('SQ1','J4',['CW_PH2','REQUEST','HALTED','FETCH0','FETCH1','EXECUTING','PC_INC','PC_ADDRESS_n','MEM_n'])
    add('PC1','J1',['PC1_PH3','PC1_RESET_n','PC_INC','LOAD_n12','LOAD_n11','OUT_n12','OUT_n11','GND'])
    add('PC1','J3',BITS('PC_ADDRESS',16))
    add('AL1','J1',['AL1_PH1','AL1_PH3','AL1_RESET_n','LOAD_n1','LOAD_n6','LOAD_n7','OUT_n1','OUT_n6','OUT_n7','FUN10','FUN9','FUN12','FUN11'])
    add('AL1','J3',BITS('ALU_OP',5)+BITS('FLAG',4))
    add('RG1','J1',['RG1_PH3','RG1_RESET_n']+BITS('LOAD_n',4,2)+BITS('OUT_n',4,2))
    add('RG1','J90',['RG1_INIT_CLK'])
    add('SP1','J1',['SP1_PH1','SP1_PH3','SP1_RESET_n','FUN3','FUN4','LOAD_n14','LOAD_n13','OUT_n14','OUT_n13'])
    add('SP1','J3',BITS('SP_ADDRESS',16));add('SP1','J90',['SP1_INIT_CLK','SP1_PH2'])
    add('MA1','J1',['MA1_PH1','MA1_PH3','MA1_RESET_n','FUN8','FETCH0','FUN6','FUN7','LOAD_n9','LOAD_n8','OUT_n9','OUT_n8'])
    add('MA1','J3',BITS('ADDRESS',16));add('MA1','J4',BITS('PC_ADDRESS',16));add('MA1','J5',BITS('SP_ADDRESS',16))
    add('MA1','J90',['MA1_INIT_CLK','MA1_PH2'])
    add('ME1','J1',['ME1_PH0','ME1_PH2','ME1_PH3','ME1_RESET_n','MEM_n','LOAD_n10'])
    add('ME1','J3',BITS('ADDRESS',16));add('ME1','J4',['IO_STROBE']+BITS('IO_DATA')+BITS('IO_ADDRESS'))
    add('ME1','J5',BITS('IO_INPUT'))
    for group in range(4):add('BF1','J'+str(group+1),BITS(f'BRANCH{group}_'))
    add('BF1','J5',BITS('DATA'));add('BF1','J6',BITS('OUT_n',9,1)+['MEM_n']+BITS('OUT_n',4,11))
    add('BF1','J7',['BF1_RESET_n'])
    add('DT1','J1',BITS('PH',4)+['INIT_CLK','RESET_n']);add('DT1','J2',[leaf for root,leaf in LEAVES])
    return p

def generate():
    b=Board('BP2');mapping=ports();rows=[]
    for (name,ref),signals in mapping.items():
        c=next(c for c in read_sheet(DEST/(name+'.sch'))['components'] if c['ref']==ref)
        assert len(c['pins'])==len(signals),(name,ref)
        bp_ref=f'J{len(rows)+1}';b.connector(bp_ref,signals)
        rows.append(dict(board=name,connector=ref,backplane=bp_ref,signals=signals))
    for ref,signals in [('J901',['5V','GND','RESET_REQUEST_n','RUN','RESUME','STEP']),
        ('J902',['5V','GND','IO_STROBE']+BITS('IO_DATA')+BITS('IO_ADDRESS')),
        ('J903',['5V','GND']+BITS('IO_INPUT')),('J904',['5V','GND','ACTIVE','READY','HALTED','FETCH0','FETCH1','EXECUTING','PC_ADDRESS_n','ALU_ENABLE'])]:
        b.connector(ref,signals)
    (DEST/'BP1.sch').write_text(b.finish());write_json(DEST/'connections.json',rows)
    print('Generated CP1 backplane',len(rows),'module connectors')

if __name__=='__main__':generate()

"""FD1 connector contract and actual-pin allocated-load audit."""
from pathlib import Path
from designs.distribution_candidate import FACTORIES,SOURCES,RECEIVERS,LEAVES,RESET_PINS
from .distribution_hardware import load_boards,ClockTree,ResetTree,Fabric,Selector


def connections():
    rows=[]
    def join(name,*endpoints):rows.append(dict(name=name,connections=[(b,r,str(p)) for b,r,p in endpoints]))
    for board,refs in SOURCES.items():
        for source in refs.values():
            for bit in range(8):join(f'source{source}.{bit}',(board,f'J{900+source}',bit+3),('DF1',f'J{source}',bit+3))
    for i,board in enumerate(RECEIVERS):
        for bit in range(8):join(f'receiver-{board}.{bit}',('DF1',f'J{21+i}',bit+3),(board,'J2',bit+3))
    for bit in range(6):join(f'control.{bit}',('CW1','J900',bit+3),('SEL','J1',bit+3))
    for bit in range(4):join(f'select.{bit}',('SEL','J2',bit+3),('DF1','J30',bit+3))
    join('fetch1',('SQ1','J4',7),('SEL','J1',9))
    assert len(rows)==179
    for bit in range(16):
        join(f'PC_ADDRESS{bit}',('PC1','J3',bit+3),('MA1','J4',bit+3))
        join(f'SP_ADDRESS{bit}',('SP1','J3',bit+3),('MA1','J5',bit+3))
        join(f'MEM_ADDRESS{bit}',('MA1','J3',bit+3),('ME1','J3',bit+3))
    for bit in range(4):
        join(f'FLAGS{bit}',('AL1','J3',bit+8),('CW1','J2',bit+3))
        join(f'TSTATE{bit}',('SQ1','J3',bit+3),('CW1','J2',bit+7))
    for bit in range(8):join(f'OPCODE{bit}',('SQ1','J3',bit+7),('CW1','J2',bit+11))
    for bit in range(5):join(f'ALU_OP{bit}',('CW1','J6',bit+3),('AL1','J3',bit+3))
    outs={1:('AL1','J1',9),2:('RG1','J1',9),3:('RG1','J1',10),4:('RG1','J1',11),5:('RG1','J1',12),
          6:('AL1','J1',10),7:('AL1','J1',11),8:('MA1','J1',13),9:('MA1','J1',12),10:('SQ1','J1',15),
          11:('PC1','J1',9),12:('PC1','J1',8),13:('SP1','J1',11),14:('SP1','J1',10)}
    loads={1:('AL1','J1',6),2:('RG1','J1',5),3:('RG1','J1',6),4:('RG1','J1',7),5:('RG1','J1',8),
           6:('AL1','J1',7),7:('AL1','J1',8),8:('MA1','J1',11),9:('MA1','J1',10),10:('ME1','J1',8),
           11:('PC1','J1',7),12:('PC1','J1',6),13:('SP1','J1',9),14:('SP1','J1',8)}
    functions={1:('SQ1','J1',11),2:('SQ1','J1',12),3:('SP1','J1',6),4:('SP1','J1',7),5:('SQ1','J1',13),
               6:('MA1','J1',8),7:('MA1','J1',9),8:('MA1','J1',6),9:('AL1','J1',13),10:('AL1','J1',12),
               11:('AL1','J1',15),12:('AL1','J1',14)}
    for bit,target in outs.items():join(f'OUT{bit}_n',('CW1','J3',bit+2),target)
    for bit,target in loads.items():join(f'LOAD{bit}_n',('CW1','J4',bit+2),target)
    for bit,target in functions.items():join(f'FUN{bit}',('CW1','J5',bit+2),target)
    for name,source,target in [
            ('CW_VALID',('CW1','J1',6),('SQ1','J1',10)),('CW_PC_ADDRESS_n',('CW1','J6',8),('SQ1','J1',14)),
            ('CW_PH2',('SQ1','J4',3),('CW1','J1',4)),('PC_INC',('SQ1','J4',9),('PC1','J1',5)),
            ('MEM_READ_n',('SQ1','J4',11),('ME1','J1',7)),('FETCH0',('SQ1','J4',6),('MA1','J1',7)),
            ('CLOCK_REQUEST',('SQ1','J4',4),('C1','J1',4))]:join(name,source,target)
    phase_pins={'CW1':{1:3},'SQ1':{0:3,1:4,2:5,3:6},'PC1':{3:3},'AL1':{1:3,3:4},
                'RG1':{3:3},'SP1':{1:3,3:4},'MA1':{1:3,3:4},'ME1':{0:3,2:4,3:5}}
    for phase in range(4):join(f'PH{phase}_ROOT',('C1','J2',phase+3),('CD1','J1',phase+3))
    for i,(phase,name) in enumerate((phase,name) for phase,names in LEAVES.items() for name in names):
        join(f'PH{phase}_{name}',('CD1','J2',i+3),(name,'J1',phase_pins[name][phase]))
    for i,name in enumerate(FACTORIES):join(f'RESET_{name}',('RD1','J2',i+3),(name,'J1',RESET_PINS[name]))
    assert len(rows)==324 and len({r['name'] for r in rows})==324
    endpoints=[e for r in rows for e in r['connections']]
    assert len(endpoints)==648 and len(set(endpoints))==648
    return rows


def all_boards(folder):
    folder=Path(folder);boards=load_boards(folder)
    boards.update(CD1=ClockTree(folder/'Clock-Distribution.sch'),RD1=ResetTree(folder/'Reset-Distribution.sch'),
                  DF1=Fabric(folder/'Data-Fabric.sch'),SEL=Selector(folder/'Data-Selector.sch'))
    return boards


def audit(folder):
    boards=all_boards(folder);rows=[]
    pins={name:{(p['ref'],x['number']):(p,x) for p in c.sheet['components'] for x in p['pins']} for name,c in boards.items()}
    for link in connections():
        endpoints={};labels={};limits=[]
        for board,ref,pin in link['connections']:
            c=boards[board];net=c.nets[c.nodes[ref,pin]];labels[f'{board}:{ref}:{pin}']=net['labels']
            for node in net['nodes']:
                part,p=pins[board][tuple(node)]
                if not part['ref'].startswith('U'):continue
                device=c.parts['devices'][part['value']]
                endpoints[board,*node]=dict(board=board,ref=node[0],pin=node[1],kind=p['kind'],mpn=part['value'],
                                            cap_pf=device['input_cap_pf'] if p['kind']=='I' else 0)
                if p['kind'] in ('O','T'):limits.append(device.get('timing_load_pf',50))
        inputs=[v for v in endpoints.values() if v['kind']=='I'];outputs=[v for v in endpoints.values() if v['kind'] in ('O','T')]
        cap=10+sum(r['cap_pf'] for r in inputs);limit=min(limits,default=0)
        rows.append(dict(**link,labels=labels,receivers=inputs,drivers=outputs,link_allocation_pf=10,
                         cap_pf=cap,limit_pf=limit,passed=len(outputs)==1 and cap<=limit))
    return dict(rows=rows,passed=all(r['passed'] for r in rows),
                scope='324 physical connector links in AL2/CD1/RD1/DF2. Each link allocates 10 pF total routing/connectors '
                      'and counts each actual IC input once. One driver required, with its declared timing-load ceiling. '
                      'External reset/oscillator/front-panel/display, supplies, local SRAM turnaround, full-temperature '
                      'capacitance, routing and physical slew remain outside this bounded audit.')

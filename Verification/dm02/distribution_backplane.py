"""BP1 logical backplane generated from the clean FD1 connector contract."""
from copy import deepcopy
from pathlib import Path
from dm02.common import ROOT,BUILD,digest,write_json,evidence
from dm02.legacy import read_sheet,connectivity
from dm02.electrical import audit
from dm02.native_migrate import validate
from designs.drawing import Drawing
from designs.distribution_candidate import FACTORIES,SOURCE
from .distribution_links import all_boards,audit as link_audit

BACKPLANE=ROOT/'Circuits/KiCad/Backplane/candidates/Backplane.sch'


def contract(folder):
    boards=all_boards(folder);review=link_audit(folder)
    assert review['passed'];endpoints={};links=[]
    for row in review['rows']:
        net=f'LINK{len(links):03d}'
        for endpoint in row['connections']:
            assert endpoint not in endpoints,endpoint
            endpoints[endpoint]=net
        links.append(dict(net=net,name=row['name'],connections=row['connections'],allocation_pf=row['cap_pf'],
                          trace_and_connector_allocation_pf=row['link_allocation_pf']))
    groups={
        'FRONT_PANEL':[('RD1','J1','3'),('SQ1','J1','8'),('SQ1','J1','9'),('C1','J1','8')],
        'STATUS':[('C1','J1','5'),('C1','J1','6'),('SQ1','J4','5'),('SQ1','J4','8'),('SQ1','J4','10'),('CW1','J6','9')],
        'DISPLAY_OUTPUT':[('ME1','J4',str(p)) for p in range(3,20)],
        'DISPLAY_INPUT':[('ME1','J5',str(p)) for p in range(3,11)]}
    peripherals=[]
    for name,connections in groups.items():
        pins=['5V','GND']
        for endpoint in connections:
            assert endpoint not in endpoints
            b,r,p=endpoint;c=boards[b];labels=c.nets[c.nodes[r,p]]['labels'];assert len(labels)==1
            label='EXT_'+b+'_'+labels[0];endpoints[endpoint]=label;pins.append(label)
        peripherals.append(dict(name=name,pins=pins))
    strap=('PC1','J1','10');assert strap not in endpoints;endpoints[strap]='GND'
    headers=[];unused=[]
    # Keep BP1 connector references stable when the AL1 slot changes to AL2.
    for board in [*FACTORIES,'DF1','SEL','CD1','RD1']:
        c=boards[board]
        for part in sorted((p for p in c.sheet['components'] if p['ref'].startswith('J')),key=lambda p:int(p['ref'][1:])):
            pins={}
            for pin in part['pins']:
                number=pin['number'];key=(board,part['ref'],number);net=c.nets[c.nodes[part['ref'],number]]
                supply=set(net['labels']) & {'5V','GND'}
                if supply:
                    assert len(supply)==1 and key not in endpoints;label=next(iter(supply))
                elif key in endpoints:label=endpoints[key]
                else:
                    assert not net['labels'] and len(net['nodes'])==1,(key,net)
                    label=None;unused.append(key)
                pins[number]=label
            headers.append(dict(ref=f'J{len(headers)+1}',board=board,connector=part['ref'],lib_id=part['lib_id'],
                                footprint=part['footprint'],pins=pins))
    assert unused==[('C1','J2','8')],unused
    for peripheral in [dict(name='POWER',pins=['5V','GND']),*peripherals]:
        count=len(peripheral['pins'])
        headers.append(dict(ref=f'J{len(headers)+1}',board='EXTERNAL',connector=peripheral['name'],
                            lib_id=f'Connector_Generic:Conn_01x{count:02}',
                            footprint=f'Connector_PinHeader_2.54mm:PinHeader_1x{count:02}_P2.54mm_Vertical',
                            pins={str(i+1):n for i,n in enumerate(peripheral['pins'])}))
    return dict(links=links,headers=headers,unused=unused,strap=dict(endpoint=strap,net='GND'),
                source_hashes={c.sheet['source']:digest(ROOT/c.sheet['source']) for c in boards.values()},
                scope='BP1 pin-preserving logical backplane for FD1 (AL2/CD1/RD1/DF2). The AL1 slot contains AL2. '
                      '324 signal links and an explicit PC address-enable ground strap. Each 10 pF link allocation covers '
                      'all traces and mating connectors together. Qualified front-panel reset/controls and driven display '
                      'inputs are external; status outputs have no added indicator loads. Physical layout, connector '
                      'procurement, supply protection/integrity and display electronics are unfinished.')


def drawing(spec):
    d=Drawing('DM-02 passive backplane candidate','BP1',[
        'Pin-preserving connectors for FD1: AL2 in the AL1 slot, CD1/RD1/DF2.',
        '324 audited signal links; PC address output enable grounded.',
        'External reset and controls require qualified inputs; display external.',
        'Logical connectivity only; physical routing/load/supply qualification pending.'],row_step=4200,page=('User',36000,56000))
    for h in spec['headers']:d.part(h['lib_id'],h['ref'],h['board']+'_'+h['connector'],1,h['pins'],h['footprint'])
    return d.text()


def compare(sheet,spec):
    expected={(h['ref'],pin):label for h in spec['headers'] for pin,label in h['pins'].items()};actual={};errors=[]
    nets=connectivity(sheet)
    for net in nets:
        labels=net['labels']
        if len(labels)>1:errors.append(dict(kind='shorted-net-labels',labels=labels))
        for node in net['nodes']:actual[tuple(node)]=labels[0] if len(labels)==1 else None
    for endpoint in sorted(set(expected)|set(actual)):
        if endpoint not in actual or endpoint not in expected or expected[endpoint]!=actual[endpoint]:
            errors.append(dict(kind='pin-net-mismatch',endpoint=endpoint,want=expected.get(endpoint),actual=actual.get(endpoint)))
    want_groups={}
    for endpoint,label in expected.items():want_groups.setdefault(label if label is not None else endpoint,set()).add(endpoint)
    got={frozenset(map(tuple,n['nodes'])) for n in nets};want={frozenset(n) for n in want_groups.values()}
    if got!=want:errors.append(dict(kind='net-group-mismatch',missing=len(want-got),extra=len(got-want)))
    return dict(passed=not errors,errors=errors,pins=len(expected),nets=len(want))


def mutations(sheet,spec):
    results=[]
    for name,label in [('data','LINK000'),('clock','LINK300'),('reset','EXT_RD1_RESET_n'),('pc-enable',None)]:
        changed=deepcopy(sheet)
        if name=='pc-enable':
            h=next(h for h in spec['headers'] if h['board']=='PC1' and h['connector']=='J1')
            part=next(p for p in changed['components'] if p['ref']==h['ref']);pin=next(p for p in part['pins'] if p['number']=='10')
            item=next(l for l in changed['labels'] if (l['x'],l['y'])==(pin['x'],pin['y']))
            assert item['name']=='GND';item['name']='5V'
        else:next(l for l in changed['labels'] if l['name']==label)['name']='BROKEN_LINK'
        result=compare(changed,spec);assert not result['passed'],name
        results.append(dict(fault=name,detected=True,errors=result['errors']))
    return results


def run():
    folder=BUILD/'backplane';folder.mkdir(parents=True,exist_ok=True);spec=contract(SOURCE);source=BACKPLANE
    if source.read_text()!=drawing(spec):raise ValueError('BP1 candidate differs from connector contract')
    sheet=read_sheet(source);check=compare(sheet,spec);assert check['passed'],check
    structure=audit(sheet);assert not structure['findings'],structure
    native=validate(sheet,folder/'native');assert native['status']=='pass',native
    result=dict(contract=spec,comparison=check,structure=structure,native=native,mutations=mutations(sheet,spec))
    write_json(folder/'summary.json',result)
    return evidence('backplane','BP1 logical backplane for FD1','limited',
                    f"{len(spec['headers'])} headers, {check['pins']} pins, {len(spec['links'])} links; native KiCad and four connection mutations pass.",
                    limitation=spec['scope'],artifacts=['backplane/summary.json','backplane/native/Backplane.kicad_sch'])


if __name__=='__main__':print(run()['summary'])

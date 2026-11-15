"""Native parity, physical packages, merged net loads and DC interface audit."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];CANDIDATE=HERE/'candidate'
sys.path.insert(0,str(CANDIDATE/'Verification'))
from dm02.common import write_json,digest,ROOT as CROOT
from dm02.compact_hardware import Circuit
from dm02.legacy import read_sheet,connectivity
from dm02.electrical import audit
from dm02.native_migrate import validate
from designs.compact_candidate import DEST
from designs.compact_backplane import generate,ports

def main(native=False):
    generate();boards={};packages=[];circuits={}
    names=list(json.loads((DEST/'boards.json').read_text()))+['BP1']
    for name in names:
        sheet=read_sheet(DEST/(name+'.sch'));structure=audit(sheet)
        row=dict(source_sha256=digest(DEST/(name+'.sch')),structure=structure)
        if native:row['native']=validate(sheet,HERE/'native'/name)
        boards[name]=row;instances=defaultdict(list)
        for c in sheet['components']:instances[c['ref']].append(c)
        for ref,cs in instances.items():
            c=cs[0];assert len({(x['value'],x['footprint']) for x in cs})==1
            assert len({x['unit'] for x in cs})==len(cs),(name,ref,'duplicate physical unit')
            packages.append(dict(board=name,ref=ref,value=c['value'],footprint=c['footprint'],units=[x['unit'] for x in cs],
                ic=ref.startswith('U'),oscillator=ref.startswith('Y')))
        if name!='BP1':circuits[name]=Circuit(name)
    # Union board nets with physical backplane connector nets, then collect ALL
    # receiver/disabled-output loads without double counting connector budgets.
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def join(a,b):parent[find(a)]=find(b)
    connections=json.loads((DEST/'connections.json').read_text())
    bp=read_sheet(DEST/'BP1.sch');bnets=connectivity(bp)
    bp_nodes={tuple(n):i for i,net in enumerate(bnets) for n in net['nodes']}
    for row in connections:
        c=circuits[row['board']]
        for pin in range(1,len(row['signals'])+1):
            join((row['board'],c.nodes[row['connector'],str(pin)]),('BP1',bp_nodes[row['backplane'],str(pin)]))
    merged=defaultdict(lambda:dict(labels=set(),pins=[],connectors=0))
    for name,c in circuits.items():
        for i,net in enumerate(c.nets):
            r=merged[find((name,i))];r['labels'].update(name+':'+s for s in net['labels'])
        for co in c.sheet['components']:
            for p in co['pins']:
                r=merged[find((name,c.nodes[co['ref'],p['number']]))]
                if co['ref'].startswith('J'):r['connectors']+=1
                if co['ref'].startswith('U'):
                    d=c.parts['devices'][co['value']]
                    role=p['kind'];allocation=None;guaranteed=True
                    if d['function']=='245' and p['number'] in map(str,range(2,10)):
                        role='I';allocation=10;guaranteed=False
                    elif d['function']=='245' and p['number'] in map(str,range(11,19)):
                        role='T';allocation=10;guaranteed=False
                    elif role=='I':allocation=d['input_cap_pf']
                    elif role in ('O','T','B'):allocation=d.get('io_cap_pf') or 10;guaranteed=False
                    r['pins'].append(dict(board=name,ref=co['ref'],pin=p['number'],part=co['value'],role=role,
                        capacitance_pf=allocation,cap_guaranteed=guaranteed,limit_pf=d.get('timing_load_pf',50)))
    loads=[]
    for r in merged.values():
        drivers=[p for p in r['pins'] if p['role'] in ('O','T','B')]
        if not drivers:continue
        receivers=[p for p in r['pins'] if p['role']=='I']
        # Active driver's own capacitance is part of its characterized output.
        inactive=max(0,sum(p['capacitance_pf'] or 0 for p in drivers)-min(p['capacitance_pf'] or 0 for p in drivers))
        cap=sum(p['capacitance_pf'] or 0 for p in receivers)+inactive+(10 if r['connectors'] else 5)
        limit=min(p['limit_pf'] for p in drivers)
        unknown=any(not p['cap_guaranteed'] for p in receivers) or len(drivers)>1
        loads.append(dict(labels=sorted(r['labels']),drivers=drivers,receivers=receivers,allocated_load_pf=cap,
            timing_table_load_pf=limit,within_allocation=cap<=limit,cap_guaranteed=not unknown,
            scope='Routing allowance is unmeasured; 245 IO capacitance is an allocation, not a datasheet maximum.'))
    counts=Counter(p['value'] for p in packages if p['ic'])
    result=dict(boards=boards,logic_memory_packages=sum(counts.values()),by_part=dict(sorted(counts.items())),
        baseline_packages=288,saving=288-sum(counts.values()),all_ic_dip=all('DIP' in p['footprint'] for p in packages if p['ic']),
        structure_passed=all(not b['structure']['findings'] for b in boards.values()),
        native_passed=all(b.get('native',{}).get('status')=='pass' for b in boards.values()) if native else None,
        load_over_allocations=[r for r in loads if not r['within_allocation']],
        load_scope='Allocation check, not guaranteed full-envelope electrical qualification.',
        physical_qualification=False)
    write_json(HERE/'packages.json',packages);write_json(HERE/'loads.json',loads)
    write_json(HERE/('native-audit.json' if native else 'audit.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('boards','load_over_allocations')},indent=2))
    print('Overloads:',[(x['labels'],x['allocated_load_pf'],x['timing_table_load_pf']) for x in result['load_over_allocations']])
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',action='store_true');a=p.parse_args();main(a.native)

"""Compare physical BP1 connector groups to the actual HDL interface bindings.

This does not import the backplane's wiring-plan function. It reads the emitted
schematic and generated module/bench assignments and compares equivalence sets.
"""
from pathlib import Path
from collections import defaultdict
import importlib.util,json,re
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.compact_hardware import Circuit
from dm02.legacy import read_sheet,connectivity
from dm02.common import digest,write_json
from designs.compact_candidate import DEST

INSTANCES={'C1':'source','CW1':'control','SQ1':'dut','PC1':'counter','AL1':'alu',
    'RG1':'registers','SP1':'stack','MA1':'address','ME1':'memory','BF1':'fabric','DT1':'tree'}

def split(text):
    chunks=[];depth=0;start=0
    for i,c in enumerate(text):
        if c=='{':depth+=1
        if c=='}':depth-=1
        if c==',' and not depth:chunks.append(text[start:i].strip());start=i+1
    chunks.append(text[start:].strip());return chunks

def ports(text):
    header=re.search(r'\bmodule\s+\w+\s*\((.*?)\);',text,re.S)[1]
    result=[];high=low=0
    for chunk in split(header):
        m=re.match(r'(input|output|inout)\s+(?:wire\s+)?(?:\[(\d+):(\d+)\]\s*)?(\w+)$',chunk)
        if m:high,low=(int(m[2]),int(m[3])) if m[2] else (0,0);name=m[4]
        else:assert re.fullmatch(r'\w+',chunk),chunk;name=chunk
        result.append((name,high,low))
    return result

def main():
    folder=HERE/'candidate/Verification/build/compact/c1-cases0'
    tb=(folder/'tb.sv').read_text();widths={}
    for m in re.finditer(r'\b(?:wire|tri|reg)\s*(?:\[(\d+):(\d+)\])?\s+([^;]+);',tb):
        high,low=(int(m[1]),int(m[2])) if m[1] else (0,0)
        for chunk in split(m[3]):
            name=re.match(r'\w+',chunk)
            if name:widths[name[0]]=(high,low)
    aliases={}
    def bits(expr):
        expr=expr.strip()
        if expr=="HARD_ADDRESS ? 1'b0 : pc_address_n":return ['0']
        if expr.startswith('{'):return sum((bits(x) for x in split(expr[1:-1])),[])
        if expr in ('0',"1'b0"):return ['0']
        if expr in ('1',"1'b1"):return ['1']
        constant=re.fullmatch(r"(\d+)'b([01]+)",expr)
        if constant:return list(constant[2].zfill(int(constant[1])))
        m=re.fullmatch(r'(\w+)(?:\[(\d+)(?::(\d+))?\])?',expr);assert m,expr
        name=m[1]
        if m[2]:high=int(m[2]);low=int(m[3] or m[2]);scalar=False
        else:high,low=widths[name];scalar=high==low==0
        return [aliases.get(name if scalar else f'{name}[{i}]',name if scalar else f'{name}[{i}]') for i in range(high,low-1,-1)]
    for m in re.finditer(r'wire\s+(\w+)=distribution_leaves\[(\d+)\];',tb):aliases[m[1]]=f'distribution_leaves[{m[2]}]'
    for i in range(4):aliases[f'SQ1_phase[{i}]']=aliases[f'SQ1_PH{i}']
    for m in re.finditer(r'wire\s*\[(\d+):(\d+)\]\s*(\w+)=\{([^}]+)\};',tb):
        if '.' in m[4]:continue # Hierarchical observation monitors are not interconnect.
        values=bits('{'+m[4]+'}');assert len(values)==int(m[1])-int(m[2])+1
        for i,value in zip(range(int(m[1]),int(m[2])-1,-1),values):aliases[f'{m[3]}[{i}]']=value
    sim={};models={};equivalent={}
    def root(x):
        equivalent.setdefault(x,x)
        if equivalent[x]!=x:equivalent[x]=root(equivalent[x])
        return equivalent[x]
    for board,instance in INSTANCES.items():
        text=(folder/(board+'.sv')).read_text();models[board]=digest(folder/(board+'.sv'))
        interface=ports(text)
        matches=re.findall(r'\b'+instance+r'\s*\((.*?)\);',tb,re.S)
        assert len(matches)==1,(board,instance)
        arguments=split(matches[0]);assert len(arguments)==len(interface),(board,arguments,interface)
        mapping={}
        for (port,high,low),arg in zip(interface,arguments):
            actual=bits(arg);assert len(actual)==high-low+1,(board,port,arg,actual)
            if board=='ME1' and port=='io_input':actual=[f'external_io_input[{i}]' for i in range(7,-1,-1)]
            for i,x in zip(range(high,low-1,-1),actual):mapping[port if high==low==0 else f'{port}[{i}]']=x
        node_bindings=defaultdict(set)
        for m in re.finditer(r'assign\s+(n\[\d+\]|\w+(?:\[\d+\])?)\s*=\s*(n\[\d+\]|\w+(?:\[\d+\])?|1\x27b[01])\s*;',text):
            a,b=m[1],m[2]
            if a.startswith('n[') and (b in mapping or b in ('0','1',"1'b0","1'b1")):node_bindings[a].add(mapping.get(b,b[-1]))
            if b.startswith('n[') and a in mapping:node_bindings[b].add(mapping[a])
        for m in re.finditer(r'assign\s+(\w+)\s*=\s*\{([^}]+)\};',text):
            nodes=split(m[2]);keys=[k for k in mapping if k.startswith(m[1]+'[')]
            if not keys:continue
            keys.sort(key=lambda k:int(k.split('[')[1][:-1]),reverse=True)
            assert len(keys)==len(nodes),(board,m[1])
            for key,node in zip(keys,nodes):
                if re.fullmatch(r'n\[\d+\]',node):node_bindings[node].add(mapping[key])
        for m in re.finditer(r'tran\s*\(\s*(n\[\d+\]),\s*(\w+(?:\[\d+\])?)\s*\);',text):
            if m[2] in mapping:node_bindings[m[1]].add(mapping[m[2]])
        c=Circuit(board)
        for co in c.sheet['components']:
            if not co['ref'].startswith('J'):continue
            for pin in co['pins']:
                group=node_bindings[c.n(co['ref'],pin['number'])]
                if not group:continue
                first=next(iter(group))
                for member in group:equivalent[root(member)]=root(first)
                sim[(board,co['ref'],pin['number'])]=first
    rows=json.loads((DEST/'connections.json').read_text())
    bp_nets=connectivity(read_sheet(DEST/'BP1.sch'));bp_nodes={tuple(p):i for i,net in enumerate(bp_nets) for p in net['nodes']}
    physical=defaultdict(set);simulated=defaultdict(set)
    for row in rows:
        for pin in range(1,len(row['signals'])+1):
            endpoint=(row['board'],row['connector'],str(pin))
            if endpoint not in sim:
                assert row['signals'][pin-1] is None,('Unbound physical signal',endpoint,row['signals'][pin-1])
                continue
            physical[bp_nodes[row['backplane'],str(pin)]].add(endpoint)
            simulated[root(sim[endpoint])].add(endpoint)
    want={frozenset(g) for g in physical.values()};got={frozenset(g) for g in simulated.values()}
    assert want==got,{'physical_only':[sorted(g) for g in want-got],'simulation_only':[sorted(g) for g in got-want]}
    result=dict(passed=True,connector_pins=len(sim),assembly_groups=len(want),backplane_sha256=digest(DEST/'BP1.sch'),
        connection_index_sha256=digest(DEST/'connections.json'),bench_sha256=digest(folder/'tb.sv'),model_hashes=models,
        scope='Physical BP1 net partition equals generated module-port/testbench scalar wiring partition, including supplies and reset/clock branches; NC pins excluded.')
    write_json(HERE/'interconnect-check.json',result);print(result)
if __name__=='__main__':main()

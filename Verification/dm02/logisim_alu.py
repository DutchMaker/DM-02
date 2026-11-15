"""Trace ALU data boundaries through explicit Logisim subcircuit appearances."""
import xml.etree.ElementTree as ET
from .common import ROOT, digest
from .logisim_pc import Nets, attributes, point, gate_ports


def ports(instance,definition):
    if attributes(instance).get('facing','east')!='east': raise ValueError('Rotated ALU subcircuit')
    appearance=definition.find('appear'); anchor=appearance.find('circ-anchor')
    if anchor.get('facing')!='east': raise ValueError('Unexpected ALU appearance anchor')
    ax=int(anchor.get('x'))+int(anchor.get('width'))//2
    ay=int(anchor.get('y'))+int(anchor.get('height'))//2
    names={point(p.get('loc')):attributes(p)['label'] for p in definition.findall("comp[@name='Pin']")}
    x,y=point(instance.get('loc'))
    return {names[point(p.get('pin'))]:(x+int(p.get('x'))+int(p.get('width'))//2-ax,
                                      y+int(p.get('y'))+int(p.get('height'))//2-ay)
            for p in appearance.findall('circ-port')}


def trace(root=None):
    paths={'main':ROOT/'Logisim/DM-02.circ','8':ROOT/'Logisim/libraries/logi7400ic.circ',
           '9':ROOT/'Logisim/libraries/logi7400dip.circ','14':ROOT/'Logisim/libraries/CSCvon8-ALU.circ'}
    roots={key:ET.parse(path).getroot() for key,path in paths.items()}
    roots[None]=root if root is not None else roots['main']
    circuit=roots[None].find("circuit[@name='ALU']"); components={}
    for c in circuit.findall('comp'):
        if c.get('lib') not in (None,'8','9','14'): continue
        definition=roots[c.get('lib')].find(f"circuit[@name='{c.get('name')}']")
        components[point(c.get('loc'))]=ports(c,definition)
    pin={attributes(c)['label']:point(c.get('loc')) for c in circuit.findall("comp[@name='Pin']")}
    tunnel={attributes(c)['label']:point(c.get('loc')) for c in circuit.findall("comp[@name='Tunnel']")}
    branches=[(540,y) for y in (490,500,510,520,540,550,560,570)]
    branches += [(x,290) for x in range(1000,1050,10)]
    gates=[(c.get('name'),*gate_ports(c)) for c in circuit.findall('comp') if c.get('name').endswith(' Gate')]
    nets=Nets(circuit,branches+[p for group in components.values() for p in group.values()]+
              [p for _,out,ins in gates for p in (out,*ins)])
    rows=[]
    def check(a,b,description):
        rows.append(dict(connection=description,start=a,end=b,connected=nets.net(a)==nets.net(b)))
    for loc in ((300,220),(480,220)):
        check(components[loc]['D'],pin['DATA_BUS_in'],str(loc)+' operand input')
    for loc,label in [((300,220),'A'),((480,220),'B')]:
        check(components[loc]['Q'],components[710,190][label],label+' operand to ROM')
    check(components[930,90]['A'],components[710,190]['RESULT'],'result to bus buffer')
    check(components[930,90]['B'],pin['DATA_BUS_out'],'result buffer output')
    check(components[1030,340]['B'],pin['DATA_BUS_out'],'flag buffer output')
    check(components[930,90]['~OE'],pin['~ALU_out'],'result output enable')
    check(components[1030,340]['~OE'],pin['~F_out'],'flag output enable')
    check(components[600,490]['OEA'],pin['~ALU_load'],'raw flag select')
    check(components[600,490]['OEB'],pin['~F_load'],'bus flag select')
    for b,(loc,half,label) in enumerate([((780,410),1,'Fc'),((990,410),1,'Fo'),
                                       ((780,410),2,'Fz'),((990,410),2,'Fn')]):
        ff=components[loc];buffer=components[600,490]
        check(buffer[f'A{b+1}'],(540,490+b*10),f'raw flag branch {b}')
        check(buffer[f'B{b+1}'],(540,540+b*10),f'bus flag branch {b}')
        for prefix in ('Y','Z'): check(buffer[f'{prefix}{b+1}'],ff[f'D{half}'],f'{label} data source {prefix}')
        check(ff[f'Q{half}'],tunnel[label],label+' stored output')
        check(tunnel[label],(1040-b*10,290),f'packed bit {b}')
    # Reviewed splitter mappings are boundaries, not inferred from wire order.
    splitters={point(c.get('loc')):attributes(c) for c in circuit.findall("comp[@name='Splitter']")}
    required={
        (520,510):{'fanout':'4','incoming':'5','appear':'center','bit4':'none'},
        (520,560):{'fanout':'4','incoming':'8','appear':'center',**{f'bit{i}':'none' for i in range(4,8)}},
        (1020,310):{'facing':'north','fanout':'5','incoming':'8','appear':'center',**{f'bit{i}':'4' for i in range(5,8)}}}
    for loc,want in required.items():
        if splitters.get(loc)!=want: raise ValueError(f'ALU splitter boundary changed at {loc}')
    # Trace the actual clock cone with the bus-load-derived F_clock inactive.
    # This bounded transition requires no assumptions about pull-resistor or
    # 74240 timing: ALU_out alone can force the OR gate's clock output high.
    samples=[]
    for out_n in (1,0):
        values={nets.net(pin[name]):value for name,value in [('~ALU_out',out_n),('~ALU_load',1),('~F_load',1)]}
        values[nets.net(tunnel['F_clock'])]=0
        pending=list(gates)
        while pending:
            rest=[]
            for kind,out,inputs in pending:
                if not all(nets.net(p) in values for p in inputs): rest.append((kind,out,inputs));continue
                ins=[values[nets.net(p)] for p in inputs]
                if kind not in ('OR Gate','NOT Gate'): raise ValueError('Unexpected ALU clock-cone gate')
                values[nets.net(out)]=int(any(ins)) if kind=='OR Gate' else 1-ins[0]
            if len(rest)==len(pending): break
            pending=rest
        clocks=[values[nets.net(components[loc][f'CLK{half}'])] for loc in ((780,410),(990,410)) for half in (1,2)]
        enables=[not values[nets.net(components[600,490][name])] for name in ('OEA','OEB')]
        samples.append(dict(alu_out_n=out_n,flag_clocks=clocks,enabled_data_sources=sum(enables)))
    hazard=(samples[0]['flag_clocks']==[0]*4 and samples[1]['flag_clocks']==[1]*4 and
            samples[1]['enabled_data_sources']==0)
    return dict(sources={str(p.relative_to(ROOT)):digest(p) for p in paths.values()},connections=rows,
                errors=[r for r in rows if not r['connected']],
                clock_hazard=dict(reproduced=hazard,samples=samples,
                                  scope='Settled ALU_out transition with ALU_load/F_load inactive and F_clock=0. A rising flag-clock path has no enabled D source; device delays determine the transient outcome.'),
                design_difference='KiCad now selects raw flags on ALU_out and uses a common PH3 clock with 125 feedback hold. The Logisim clock/selector network is retained only as evidence of the original hazard.',
                limitations='Subcircuit appearance ports and the flag-clock Boolean cone are extracted; splitter bit order is a reviewed, guarded geometry boundary. Pull resistor and imported primitive internals and physical delays are not simulated.')

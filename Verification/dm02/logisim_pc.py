"""Extract and evaluate the Logisim PC counter logic (untimed, bounded subset)."""
import xml.etree.ElementTree as ET
from functools import lru_cache
from .common import ROOT, BUILD, digest, evidence, write_json


def attributes(component):
    return {a.get('name'):a.get('val') for a in component.findall('a')}


def point(text):
    return tuple(map(int,text.strip('()').split(',')))


class Nets:
    def __init__(self,circuit,extra=()):
        wires=[(point(w.get('from')),point(w.get('to'))) for w in circuit.findall('wire')]
        points=set(extra)|{p for w in wires for p in w}|{point(c.get('loc')) for c in circuit.findall('comp')}
        self.parent={p:p for p in points}
        for a,b in wires:
            if a[0]!=b[0] and a[1]!=b[1]: raise ValueError('Non-axis-aligned wire')
            for p in points:
                if (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) or
                        a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0])):
                    self.parent[self.net(p)]=self.net(a)
        tunnels={}
        for c in circuit.findall("comp[@name='Tunnel']"):
            label=attributes(c)['label']; p=point(c.get('loc'))
            if label in tunnels: self.parent[self.net(p)]=self.net(tunnels[label])
            tunnels[label]=p

    def net(self,p):
        while self.parent[p]!=p:
            self.parent[p]=self.parent[self.parent[p]]; p=self.parent[p]
        return p


def gate_ports(c):
    a=attributes(c); x,y=point(c.get('loc')); name=c.get('name')
    size=int(a.get('size','30' if name=='NOT Gate' else '50'))
    if name=='XOR Gate': size+=10  # Logisim's extra input-side XOR curve.
    n=1 if name=='NOT Gate' else int(a.get('inputs','5'))
    offsets={1:[0],2:[-10,10],3:[-10,0,10],4:[-20,-10,10,20],5:[-20,-10,0,10,20]}[n]
    facing=a.get('facing','east')
    inputs=[]
    for d in offsets:
        dx,dy=-size,d
        if facing=='west': dx,dy=size,-d
        elif facing=='south': dx,dy=-d,-size
        elif facing=='north': dx,dy=d,size
        elif facing!='east': raise ValueError(facing)
        inputs.append((x+dx,y+dy))
    return (x,y),inputs


class Nibble:
    def __init__(self,root):
        circuit=root.find("circuit[@name='74161-Bus']")
        gates=[c for c in circuit.findall('comp') if c.get('name').endswith(' Gate')]
        self.ff=[point(c.get('loc')) for c in circuit.findall("comp[@name='D_Flip_Flop']")]
        if sorted(self.ff)!=[(600,240),(600,380),(600,520),(600,660)]:
            raise ValueError('Counter flip-flop geometry changed; review boundary pin mapping')
        self.ff.sort(key=lambda p:p[1])
        ports=[p for c in gates for p in (gate_ports(c)[0],*gate_ports(c)[1])]
        self.data=[(100,220+i*10) for i in range(4)]
        # External D_Flip_Flop symbol boundary used in this legacy file.
        self.d=[(x-40,y) for x,y in self.ff]
        self.clk=[(x-40,y+40) for x,y in self.ff]
        self.reset=[(x-20,y+50) for x,y in self.ff]
        self.nets=Nets(circuit,ports+self.data+self.d+self.clk+self.reset)
        self.pins={attributes(c)['label']:point(c.get('loc')) for c in circuit.findall("comp[@name='Pin']")}
        self.gates=[(c.get('name'),*gate_ports(c)) for c in gates]
        splitters=circuit.findall("comp[@name='Splitter']")
        if len(splitters)!=2: raise ValueError('Unexpected counter splitters')
        for c in splitters:
            a=attributes(c)
            if a.get('fanout')!='4' or a.get('incoming')!='4' or any(k.startswith('bit') for k in a):
                raise ValueError('Counter bit mapping changed')
        if any(self.nets.net(p)!=self.nets.net(self.pins['CLK']) for p in self.clk):
            raise ValueError('Counter flip-flop clock connection changed')

    @lru_cache(maxsize=8192)
    def evaluate(self,q,data,load_n,cep,cet,clear_n=1):
        n=self.nets; values={}
        def seed(p,value):
            key=n.net(p)
            if key in values and values[key]!=value: raise ValueError('Conflicting net drivers')
            values[key]=value
        for label,value in [('~PE',load_n),('CEP',cep),('CET',cet),('~CLR',clear_n),('CLK',0)]:
            seed(self.pins[label],value)
        for i,p in enumerate(self.ff): seed(p,(q>>i)&1)
        for i,p in enumerate(self.data): seed(p,(data>>i)&1)
        pending=list(self.gates)
        while pending:
            rest=[]
            for kind,out,inputs in pending:
                if not all(n.net(p) in values for p in inputs): rest.append((kind,out,inputs)); continue
                ins=[values[n.net(p)] for p in inputs]
                value={'AND Gate':lambda:int(all(ins)),'OR Gate':lambda:int(any(ins)),
                       'XOR Gate':lambda:sum(ins)%2,'NOT Gate':lambda:1-ins[0]}[kind]()
                seed(out,value)
            if len(rest)==len(pending): raise ValueError('Unresolved counter gate inputs')
            pending=rest
        if any(values[n.net(p)]!=1-clear_n for p in self.reset):
            raise ValueError('Counter asynchronous-reset connection changed')
        return (sum(values[n.net(p)]<<i for i,p in enumerate(self.d)) if clear_n else 0,
                values[n.net(self.pins['TC'])])


class ProgramCounter:
    def __init__(self,path=None):
        self.path=path or ROOT/'Logisim/DM-02.circ'
        root=ET.parse(self.path).getroot(); self.nibble=Nibble(root)
        c=root.find("circuit[@name='Program-Counter']")
        sub=root.find("circuit[@name='74161-Bus']")
        anchor=sub.find('appear/circ-anchor'); ax=int(anchor.get('x'))+3; ay=int(anchor.get('y'))+3
        pins={point(p.get('loc')):attributes(p)['label'] for p in sub.findall("comp[@name='Pin']")}
        offsets={}
        for port in sub.findall('appear/circ-port'):
            offsets[pins[point(port.get('pin'))]]=(int(port.get('x'))+int(port.get('width'))//2-ax,
                                                 int(port.get('y'))+int(port.get('height'))//2-ay)
        counters=c.findall("comp[@name='74161-Bus']")
        self.ports=[]
        # Physical left-to-right order is most-significant to least-significant.
        for comp in sorted(counters,key=lambda x:point(x.get('loc'))[0],reverse=True):
            if attributes(comp).get('facing','east')!='east': raise ValueError('Rotated PC counter')
            x,y=point(comp.get('loc'))
            self.ports.append({name:(x+dx,y+dy) for name,(dx,dy) in offsets.items()})
        if len(self.ports)!=4: raise ValueError('Expected four PC counters')
        self.gates=[(x.get('name'),*gate_ports(x)) for x in c.findall('comp') if x.get('name').endswith(' Gate')]
        if any(g[0]!='AND Gate' for g in self.gates): raise ValueError('Unexpected PC glue gate')
        extra=[p for ports in self.ports for p in ports.values()]+[p for _,out,ins in self.gates for p in [out,*ins]]
        self.nets=Nets(c,extra)
        self.pins={attributes(x)['label']:point(x.get('loc')) for x in c.findall("comp[@name='Pin']")}
        self.constants=[(point(x.get('loc')),int(attributes(x).get('value','0x1'),0)) for x in c.findall("comp[@name='Constant']")]
        n=self.nets
        for index,ports in enumerate(self.ports):
            for name,external in [('CLK','CLOCK'),('~CLR','~RESET'),('~PE','~L_load' if index<2 else '~H_load')]:
                if n.net(ports[name])!=n.net(self.pins[external]): raise ValueError(f'PC {index} {name} wiring differs')
        # Guard the reviewed splitter branch-to-counter ordering. The byte
        # splitter geometry/mapping remains an explicit model boundary.
        for ports,branch in zip(self.ports,[(850,480),(840,480),(520,480),(510,480)]):
            if n.net(ports['D'])!=n.net(branch): raise ValueError('PC data nibble route changed')

    def step(self,pc,data,increment,load_low=False,load_high=False,reset=False):
        n=self.nets
        values={n.net(self.pins['INCREMENT']):int(increment)}
        values.update({n.net(p):v for p,v in self.constants})
        # CET chain and CEP glue settle before the common clock edge. TC
        # depends on old Q and CET, independently of parallel load enable.
        pending=[('tc',i) for i in range(4)]+[('gate',g) for g in self.gates]
        while pending:
            rest=[]
            for kind,item in pending:
                if kind=='tc':
                    ports=self.ports[item]; cet=n.net(ports['CET'])
                    if cet not in values: rest.append((kind,item)); continue
                    values[n.net(ports['TC'])]=int(((pc>>(4*item))&15)==15 and values[cet])
                else:
                    _,out,inputs=item
                    if not all(n.net(p) in values for p in inputs): rest.append((kind,item)); continue
                    values[n.net(out)]=int(all(values[n.net(p)] for p in inputs))
            if len(rest)==len(pending): raise ValueError('Unresolved PC carry/glue net')
            pending=rest
        result=0
        for i,ports in enumerate(self.ports):
            q=(pc>>(i*4))&15; d=(data>>(4*(i%2)))&15
            load_n=int(not (load_low if i<2 else load_high))
            value,_=self.nibble.evaluate(q,d,load_n,values[n.net(ports['CEP'])],values[n.net(ports['CET'])],int(not reset))
            result |= value<<(4*i)
        return result


def run():
    pc=ProgramCounter(); errors=[]; cases=0
    for q in range(16):
        for d in range(16):
            for controls in range(16):
                load,cep,cet,clear=(controls>>i&1 for i in range(4))
                got,tc=pc.nibble.evaluate(q,d,load,cep,cet,clear)
                want=0 if not clear else d if not load else (q+1)&15 if cep and cet else q
                cases+=1
                if (got,tc)!=(want,int(q==15 and cet)): errors.append([q,d,controls,got,tc,want])
    rows=[]
    for before in (0x4500,0x45fe,0x45ff,0xffff):
        rows.append(dict(before=before,data=0x67,increment=1,load_low=True,
                         after=pc.step(before,0x67,1,load_low=True)))
    normal_errors=0
    for before in range(65536):
        normal_errors+=pc.step(before,0,1)!=((before+1)&65535)
    folder=BUILD/'microcode'; folder.mkdir(parents=True,exist_ok=True)
    result=dict(source='Logisim/DM-02.circ',source_sha256=digest(pc.path),nibble_cases=cases,
                nibble_errors=len(errors),examples=errors[:8],increment_cases=65536,increment_errors=normal_errors,
                simultaneous_load_examples=rows,
                conclusion='Each nibble gives parallel load priority, but TC still reflects old Q. Loading PC_L while incrementing can carry into unloaded PC_H when old PC_L=FF.',
                limitations=['Logisim supplementary design; no KiCad PC implementation found.',
                             'Counter Q/D, clock and reset boundary geometry is explicit and guarded; external D_Flip_Flop internals are not simulated.',
                             'PC data splitter bit order is a reviewed boundary assumption with branch wiring guards; electrical delays and bus-OE are excluded.'])
    write_json(folder/'pc-circuit.json',result)
    return evidence('pc-circuit','Logisim PC counter extraction','pass' if not errors and not normal_errors else 'fail',
                    f'{cases:,} extracted nibble truth-table cases and 65,536 PC increments; {len(errors)+normal_errors} mismatches.',
                    artifacts=['microcode/pc-circuit.json'],limitation='Untimed supplementary Logisim circuit; flip-flop boundary semantics assumed, no physical PC qualification.')

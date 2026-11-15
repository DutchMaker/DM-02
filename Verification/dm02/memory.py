"""KiCad-derived combinational memory control, with MAR as a state boundary."""
from collections import Counter
from .common import ROOT, BUILD, digest, evidence, write_json
from .legacy import read_sheet, connectivity, function_number


class Decoder:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(ROOT/'Circuits/KiCad/Memory/Memory.sch')
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,n in enumerate(self.nets) for node in n['nodes']}
        self.labels={label:i for i,n in enumerate(self.nets) for label in n['labels']}
        self.parts={c['stamp']:c for c in self.sheet['components']}
        self.rom=self.parts['5F5AD161']; self.ram=self.parts['5F5AEABC']; self.buffer=self.parts['5F5A8C71']
        self.gates=[]
        kinds={'00':('nand',2),'02':('nor',2),'04':('not',1),'08':('and',2),'21':('and',4),'32':('or',2)}
        for c in self.sheet['components']:
            f=function_number(c['lib_id'].split(':')[-1])
            if f not in kinds: continue
            ins=[self.nodes[c['ref'],p['number']] for p in c['pins'] if p['kind']=='I']
            outs=[self.nodes[c['ref'],p['number']] for p in c['pins'] if p['kind']=='O']
            kind,count=kinds[f]
            if not ins and not outs: continue  # Separate power unit.
            if len(ins)!=count or len(outs)!=1: raise ValueError(f'Unsupported gate pins: {c["stamp"]}')
            self.gates.append(dict(stamp=c['stamp'],kind=kind,inputs=ins,output=outs[0]))
        outputs=[g['output'] for g in self.gates]
        if len(set(outputs))!=len(outputs): raise ValueError('Multiple gate outputs share a net')
        self.inputs=[f'{prefix}{i}' for prefix in ('A','R') for i in range(16)]
        self.inputs+=['~MEM_out','~MEM_load','~MAR_L_load','~MAR_H_load',
                      '~PC_MAR_transfer','~STK_MAR_transfer','CLOCK_PH2','CLOCK_PH3']
        self.constants={self.labels[l]:v for l,v in [('GND',0),('+5V',1),('5V',1)] if l in self.labels}
        ready=set(self.constants)|{self.labels[l] for l in self.inputs if l in self.labels}
        pending=list(self.gates); self.ordered=[]
        while pending:
            rest=[]
            for g in pending:
                if not set(g['inputs'])<=ready: rest.append(g); continue
                if g['output'] in ready: raise ValueError('Gate drives an input boundary or supply')
                self.ordered.append(g); ready.add(g['output'])
            if len(rest)==len(pending): raise ValueError('Unresolved decoder gates: '+str([g['stamp'] for g in rest]))
            pending=rest

    def pin(self,part,number):
        return self.nodes[part['ref'],str(number)]

    def evaluate(self,mar,external,read=False,write=False,phase2=0,phase3=1,
                 load_low=False,load_high=False,pc_transfer=False,stk_transfer=False):
        values=dict(self.constants)
        def seed(label,value):
            if label not in self.labels: return
            net=self.labels[label]
            if net in values and values[net]!=value: raise ValueError('Conflicting boundary drivers: '+label)
            values[net]=int(value)
        for prefix,word in [('R',mar),('A',external)]:
            for bit in range(16): seed(f'{prefix}{bit}',word>>bit&1)
        for label,value in [('~MEM_out',not read),('~MEM_load',not write),('CLOCK_PH2',phase2),
                            ('CLOCK_PH3',phase3),('~MAR_L_load',not load_low),('~MAR_H_load',not load_high),
                            ('~PC_MAR_transfer',not pc_transfer),('~STK_MAR_transfer',not stk_transfer)]: seed(label,value)
        for g in self.ordered:
            ins=[values[i] for i in g['inputs']]; kind=g['kind']
            value=all(ins) if kind in ('and','nand') else any(ins)
            if kind in ('nand','nor','not'): value=not value
            values[g['output']]=int(value)
        def pin(part,n): return values[self.pin(part,n)]
        ram_selected=not pin(self.ram,22) and pin(self.ram,30)
        rom_driving=not pin(self.rom,20) and not pin(self.rom,22)
        ram_writing=ram_selected and not pin(self.ram,29)
        ram_driving=ram_selected and not pin(self.ram,24) and not ram_writing
        enabled=not pin(self.buffer,19); direction=pin(self.buffer,1)
        return dict(rom_driving=bool(rom_driving),ram_driving=bool(ram_driving),ram_writing=bool(ram_writing),
                    memory_to_cpu=bool(enabled and direction),cpu_to_memory=bool(enabled and not direction),
                    io_out=bool(values[self.labels['IO_out']]),io_load=bool(values[self.labels['IO_load']]),
                    low_load=not values[self.labels['~L_load_CLOCK']],high_load=not values[self.labels['~H_load_CLOCK']])

    def routes(self):
        errors=[]; checked=0
        def check(part,number,label):
            nonlocal checked
            checked+=1
            if self.pin(part,number)!=self.labels[label]: errors.append(dict(stamp=part['stamp'],pin=str(number),expected=label))
        for part,width in [(self.rom,15),(self.ram,16)]:
            for p in part['pins']:
                if p['name'].startswith('A') and p['name'][1:].isdigit():
                    check(part,p['number'],'R'+p['name'][1:])
            actual={p['name'] for p in part['pins'] if p['name'].startswith('A')}
            if actual!={f'A{i}' for i in range(width)}: errors.append(dict(stamp=part['stamp'],address_pins=sorted(actual)))
        for bit in range(8):
            bp=self.pin(self.buffer,bit+2)
            for part in (self.rom,self.ram):
                p=next(p for p in part['pins'] if p['name']==f'D{bit}'); checked+=1
                if self.pin(part,p['number'])!=bp: errors.append(dict(stamp=part['stamp'],bit=bit,expected='memory buffer A side'))
            check(self.buffer,18-bit,f'DATA{bit}')
        return dict(checked=checked,errors=errors)


def expected(address,read,write,phase):
    rom=address<0x4000; io=address>=0xff00; ram=not rom and not io
    return dict(rom_driving=bool(rom and read),ram_driving=bool(ram and read),
                ram_writing=bool(ram and write and phase),memory_to_cpu=bool(read and not io),
                cpu_to_memory=bool(write and not io),io_out=bool(io and read),io_load=bool(io and write and phase),
                low_load=False,high_load=False)


def audit(decoder):
    failures=Counter(); examples=[]; cases=0
    # Every MAR high byte crossed with every external high byte; low bits
    # are independently checked by the physical address/data pin audit.
    for high in range(256):
        for external in range(256):
            for read,write in [(False,False),(True,False),(False,True)]:
                for phase in (0,1):
                    got=decoder.evaluate(high<<8,external<<8,read,write,phase)
                    want=expected(high<<8,read,write,phase); cases+=1
                    diff={k:dict(actual=got[k],expected=v) for k,v in want.items() if got[k]!=v}
                    for k in diff: failures[k]+=1
                    if diff and len(examples)<12:
                        examples.append(dict(mar=high<<8,external=external<<8,read=read,write=write,phase2=phase,differences=diff))
    return dict(cases=cases,failures=dict(failures),examples=examples,routes=decoder.routes())


def run():
    decoder=Decoder(); result=audit(decoder)
    result.update(source=decoder.sheet['source'],source_sha256=digest(ROOT/decoder.sheet['source']),gates=decoder.gates,
                  scope='Settled Boolean gates and physical memory/transceiver pin routes from KiCad. MAR outputs and external address bus are independent stimuli. No propagation delay, 74191 ripple/async-load timing, memory access time, power qualification or simultaneous read/write contract.')
    write_json(BUILD/'memory/decoder.json',result)
    good=not result['failures'] and not result['routes']['errors']
    return evidence('memory','Schematic-derived memory control','pass' if good else 'fail',
                    f'{result["cases"]:,} MAR/external-address/read/write/phase cases; {sum(result["failures"].values()):,} signal mismatches; {len(result["routes"]["errors"])} pin-route errors.',
                    artifacts=['memory/decoder.json'],limitation=result['scope'])

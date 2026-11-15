"""Extract the active power sheet's reset cone, including driver isolation."""
from itertools import product
from .common import ROOT, VROOT, BUILD, digest, evidence, write_json
from .legacy import read_sheet, connectivity, function_number

SOURCE=ROOT/'Circuits/KiCad/Power-Clock/Power-Clock.sch'


class Reset:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(SOURCE)
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,n in enumerate(self.nets) for node in n['nodes']}
        self.parts={c['ref']:c for c in self.sheet['components']}
        self.labels={label:i for i,n in enumerate(self.nets) for label in n['labels']}
        self.gates={}
        for c in self.sheet['components']:
            kind=function_number(c['lib_id'].split(':')[-1])
            if kind not in ('04','14','08','32'): continue
            ins=[self.pin(c['ref'],p['number']) for p in c['pins'] if p['kind']=='I']
            outs=[self.pin(c['ref'],p['number']) for p in c['pins'] if p['kind']=='O']
            if not ins and not outs: continue
            if len(outs)!=1 or len(ins)!=(1 if kind in ('04','14') else 2):
                raise ValueError('Unexpected reset gate geometry')
            if outs[0] in self.gates: raise ValueError('Multiple gate outputs share a net')
            self.gates[outs[0]]=(kind,ins)

    def pin(self,ref,pin): return self.nodes[ref,str(pin)]

    def evaluate(self,por_released,button_released):
        values={self.labels['GND']:0,self.labels['5V']:1}
        for node,value in [(self.pin('U5',1),por_released),(self.pin('SW5',2),button_released)]:
            if node in values and values[node]!=value: raise ValueError('Conflicting reset boundary drivers')
            values[node]=int(value)
        visiting=set()
        def get(node):
            if node in values: return values[node]
            if node in visiting: raise ValueError('Reset feedback loop')
            if node not in self.gates: raise ValueError('Undriven reset-cone input')
            visiting.add(node)
            kind,ins=self.gates[node];args=[get(i) for i in ins]
            value=not args[0] if kind in ('04','14') else all(args) if kind=='08' else any(args)
            values[node]=int(value);visiting.remove(node)
            return values[node]
        return dict(reset_released=get(self.pin('BUS1',16)),led_drive=get(self.pin('D3',2)))

    def topology(self):
        failures=[]
        def check(condition,message):
            if not condition: failures.append(message)
        por=self.pin('U5',1);button=self.pin('SW5',2);reset=self.pin('BUS1',16);led=self.pin('D3',2)
        outputs={self.pin(c['ref'],p['number']) for c in self.sheet['components']
                 for p in c['pins'] if p['kind'] in ('O','T') and c['ref'].startswith('U')}
        check(button not in outputs,'Manual switch shorts an active IC output')
        check(len({por,button,reset,led})==4,'Supervisor, button, bus reset and LED must be isolated nets')
        check(self.pin('SW5',1)==self.labels['GND'],'Manual reset must close to GND')
        check(self.pin('R8',1)==button and self.pin('R8',2)==self.labels['5V'],'Manual reset pull-up route')
        check(self.parts['R8']['value']=='5K','Manual reset pull-up value')
        check(self.parts['R9']['value']=='2k2','LED series resistor value')
        check(self.pin('D3',1)==self.pin('R9',2) and self.pin('R9',1)==self.labels['GND'],'LED series path')
        check(self.pin('U5',2)==self.labels['5V'] and self.pin('U5',3)==self.labels['GND'],'Supervisor supply pins')
        check(self.parts['U5']['value']=='MCP100-450D','Supervisor identity requires renewed review')
        return failures


def run():
    circuit=Reset();cases=[]
    for por,button in product((0,1),repeat=2):
        got=circuit.evaluate(por,button);expected=int(por and button)
        cases.append(dict(por_released=por,button_released=button,actual=got,
                          passed=got==dict(reset_released=expected,led_drive=expected)))
    findings=circuit.topology();folder=BUILD/'reset';folder.mkdir(parents=True,exist_ok=True)
    datasheet=VROOT/'vendor/reset/mcp100.pdf'
    if digest(datasheet)!='2e50e62b4cee492f2762da32e2c672099ccf2b23b1f0020ce72dbb2084f49fa2':
        raise ValueError('MCP100 source document changed; review extracted limits')
    (folder/'mcp100.pdf').write_bytes(datasheet.read_bytes())
    details=dict(source_hash=digest(SOURCE),cases=cases,topology_findings=findings,
                 led_current_upper_ma=5.25/(2200*0.95)*1000,
                 led_current_scope='Resistor-only upper bound at 5.25 V, 5% tolerance, zero LED/driver drop. Exact LED and driver sourcing remain open.',
                 supervisor=dict(source='https://ww1.microchip.com/downloads/en/DeviceDoc/11187f.pdf',
                                 document='DS11187F',sha256=digest(datasheet),retrieved='2026-11-14',
                                 extraction='Visually checked rendered page; embedded text encoding is not reliable.',
                                 page=2,release_min_ms=150,release_typ_ms=350,release_max_ms=700,
                                 trip_min_v=4.25,trip_typ_v=4.375,trip_max_v=4.50,
                                 output='push-pull'),
                 limitations=['Settled logic and topology only; button bounce, propagation and reset release are not qualified.',
                              'MCP100-450 threshold can release below the 4.75 V operating envelope; its delay starts at threshold crossing, not at verified oscillator-valid supply.',
                              'MCP100 brownout assertion has a typical rather than maximum delay in the cited table.',
                              'Gate behavior during a slow supply ramp and receiver reset recovery/removal remain unqualified.'])
    write_json(folder/'reset.json',details)
    return evidence('reset-circuit','Schematic-derived reset isolation',
                    'pass' if not findings and all(c['passed'] for c in cases) else 'fail',
                    f'{sum(c["passed"] for c in cases)}/4 supervisor/button combinations; '
                    f'{len(findings)} topology findings; manual switch and indicator isolated from supervisor output.',
                    artifacts=['reset/reset.json','reset/mcp100.pdf'],limitation=' '.join(details['limitations']))

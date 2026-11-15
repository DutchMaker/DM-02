"""Structural electrical checks; findings are not a substitute for device ERC."""
from collections import Counter, defaultdict
from .common import ROOT, BUILD, evidence, write_json
from .legacy import read_sheet, connectivity, library


def audit(sheet):
    nets=connectivity(sheet); lookup={tuple(node):n for n in nets for node in n['nodes']}
    packages=defaultdict(list); findings=[]
    for c in sheet['components']:
        if c['ref'].startswith('U'): packages[c['ref']].append(c)
    for ref,parts in packages.items():
        first=parts[0]; ns,name=first['lib_id'].split(':'); definition=library(ns)[name]
        placed={c['unit'] for c in parts}; pins={p['number'] for c in parts for p in c['pins']}
        missing_power={p['number'] for p in definition['pins'] if p['kind']=='W' and p['number'] not in pins}
        if missing_power:
            findings.append(dict(kind='missing-power-unit',ref=ref,pins=sorted(missing_power),
                                 detail='Physical supply pins have no placed symbol unit.'))
        missing_units={p['unit'] for p in definition['pins'] if p['kind']=='I' and p['unit'] not in placed|{0}}
        if missing_units:
            findings.append(dict(kind='unplaced-logic-unit',ref=ref,units=sorted(missing_units),
                                 detail='Unused logic inputs need an explicit termination decision.'))
        for c in parts:
            for p in c['pins']:
                if p['kind'] not in ('I','W'): continue
                net=lookup[c['ref'],p['number']]; labels=set(net['labels'])
                row=dict(ref=ref,stamp=c['stamp'],pin=p['number'],name=p['name'],net=net)
                if p['kind']=='W':
                    rails={'GND'} if p['name'] in ('GND','VSS') else {'+5V','5V'}
                    if not labels&rails:
                        findings.append(dict(row,kind='unconnected-supply',detail='Supply net does not join the declared +5V/GND rail.'))
                elif len(net['nodes'])==1:
                    marked=[p['x'],p['y']] in sheet['no_connects']
                    findings.append(dict(row,kind='floating-input',detail='Input has no second pin connection'+(' (marked no-connect).' if marked else '.')))
    # Family checks use selected display values; symbols often use pin-compatible
    # LS aliases. A bipolar TTL output does not guarantee a CMOS HC input high.
    by_node={}
    for c in sheet['components']:
        for p in c['pins']: by_node[c['ref'],p['number']]=(c,p)
    for net in nets:
        if 'GND' in net['labels'] and {'+5V','5V'}&set(net['labels']):
            findings.append(dict(kind='shorted-supply-rails',net=net,detail='Ground and +5V share an electrical net.'))
        drivers=[]; receivers=[]
        for node in net['nodes']:
            c,p=by_node[tuple(node)]
            if c['value'].startswith('74LS') and p['kind'] in ('O','T','B'): drivers.append(node)
            if c['value'].startswith('74HC') and not c['value'].startswith('74HCT') and p['kind'] in ('I','B','T'):
                receivers.append(node)
        if drivers and receivers:
            findings.append(dict(kind='ttl-to-hc',drivers=drivers,receivers=receivers,net=net,
                                 detail='Selected LS-to-HC path needs guaranteed VOH/VIH review or a TTL-compatible receiver.'))
    return dict(sheet=sheet['name'],source=sheet['source'],packages=len(packages),findings=findings,
                counts=dict(Counter(r['kind'] for r in findings)))


def run():
    rows=[audit(read_sheet(p)) for p in sorted((ROOT/'Circuits/KiCad').glob('*/*.sch'))]
    counts=Counter()
    for row in rows: counts.update(row['counts'])
    result=dict(sheets=rows,counts=dict(counts),scope='Structural pin/supply/unit and direct LS-to-HC checks. Labelled singleton inputs are still findings. Connector sources, analogue networks, load current, decoupling, power integrity and full driver analysis need electrical review.')
    write_json(BUILD/'inventory/electrical.json',result)
    return evidence('electrical','Schematic electrical completeness','fail' if counts else 'pass',
                    (f'{sum(counts.values())} findings: '+', '.join(f'{v} {k}' for k,v in sorted(counts.items()))) if counts else 'No structural electrical findings across seven sheets.',
                    artifacts=['inventory/electrical.json'],limitation=result['scope'])

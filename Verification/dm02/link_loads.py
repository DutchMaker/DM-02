"""LL1 physical-pin inventory from CA1 export with explicit contact mating."""
from collections import Counter,defaultdict
from copy import deepcopy
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from .common import ROOT,BUILD,write_json,digest
from . import connector_assembly as ca,connector_assembly_evidence as cae,link_parts

STUDY=link_parts.STUDY
NATIVE=ca.STUDY/'final/native'
require=ca.require


class Inventory:
    def __init__(self,path=None,provenance=None):
        self.path=Path(path or NATIVE/'CA1.xml')
        require(ca.Assembly().compare(self.path)['passed'],'CA1 unmated/mated source parity failed')
        self.provenance=provenance or json.loads((NATIVE/'provenance.json').read_text())
        self.components=self.provenance['components'];self.parts=link_parts.review()
        tree=ET.parse(self.path).getroot();self.pins={};self.groups={};self.parent={}
        libraries={(p.get('lib'),p.get('part')):{x.get('num'):dict(x.attrib) for x in p.findall('./pins/pin')}
            for p in tree.findall('./libparts/libpart')}
        metadata={c.get('ref'):libraries[tuple(c.find('libsource').get(k) for k in ('lib','part'))] for c in tree.findall('./components/comp')}
        for net in tree.findall('./nets/net'):
            code=net.get('code');self.parent[code]=code;self.groups[code]=net.get('name')
            for node in net.findall('node'):
                ref,pin=node.get('ref'),node.get('pin');key=ref+'.'+pin
                require(key not in self.pins,'Duplicate physical pin: '+key)
                c=self.components[ref];m=metadata[ref][pin]
                self.pins[key]=dict(id=key,reference=ref,pin=pin,part=c['value'],board=c['board'],
                    source_reference=c['source_reference'],card=c['role'],native_net=code,
                    native_name=net.get('name'),symbol_type=m['type'],pin_name=m['name'])
        expected={r+'.'+p for r,pins in metadata.items() for p in pins}
        require(set(self.pins)==expected,'Missing native physical pin')
        self.contacts=[]
        for row in self.provenance['contacts']:
            a=row['card_reference']+'.'+row['pin'];b=row['backplane_reference']+'.'+row['pin']
            self.contact(a,b,'CPU '+row['role']+' '+row['connector'],row['kind'])
        # Slot 5 used nets already share NA1's domain. Account for BOTH physical
        # contacts; mate unused positions explicitly too, without adding any loads.
        for pin in ca.connector_plan.CONTACTS:self.contact('J13005.'+pin,'J14001.'+pin,'slot5','peripheral')
        self.nets=defaultdict(list)
        for p in self.pins.values():
            p['net']=self.root(p['native_net']);self.nets[p['net']].append(p)
        self.rails={self.pins['Y1001.8']['net']:'5V',self.pins['Y1001.4']['net']:'GND'}
        require(len(self.rails)==2,'Shorted supply rails')
        self.directions=[]
        for ref,c in self.components.items():
            if c['value']!='SN74HCT245N':continue
            direction=self.pins[ref+'.1'];oe=self.pins[ref+'.19']
            require(self.rails.get(direction['net'])=='5V','HCT245 DIR is not tied high: '+ref)
            self.directions.append(dict(reference=ref,board=c['board'],source_reference=c['source_reference'],
                direction_pin=direction['id'],direction_net=direction['net'],direction='A-to-B',
                enable_pin=oe['id'],enable_net=oe['net'],enable_active='low',mutual_exclusion_proven=False))
        self.resistors=[]
        for ref,c in self.components.items():
            if not ref.startswith('R'):continue
            ends=[self.pins[ref+'.'+p] for p in ('1','2')]
            value=c['value'];ohm=float(value[:-1])*1000 if value.endswith('k') else float(value)
            rails=[self.rails.get(p['net']) for p in ends]
            self.resistors.append(dict(reference=ref,value=value,nominal_ohm=ohm,tolerance=None,
                pins=[p['id'] for p in ends],nets=[p['net'] for p in ends],
                kind='pull' if any(rails) else 'series',rail=next((r for r in rails if r),None),
                parasitic_pf=None))
        for pin in self.pins.values():self.classify(pin)

    def root(self,n):
        while self.parent[n]!=n:n=self.parent[n]
        return n

    def contact(self,a,b,scope,kind):
        require(a in self.pins and b in self.pins,'Missing mating contact')
        x,y=(self.root(self.pins[k]['native_net']) for k in (a,b))
        self.parent[max(x,y)]=min(x,y)
        self.contacts.append(dict(pins=[a,b],scope=scope,kind=kind,capacitance_pf=None))

    def classify(self,p):
        ref=p['reference'];t=p['symbol_type'];part=p['part'];role=t
        if ref.startswith('J'):role='contact'
        elif ref.startswith('R'):role='resistor-terminal'
        elif ref.startswith('C'):role='capacitor-terminal'
        if part=='SN74HCT245N' and (2<=int(p['pin'])<=9 or 11<=int(p['pin'])<=18):
            role='input' if int(p['pin'])<=9 else 'tri_state'
        p['electrical_role']=role;p['receiver']=role in ('input','bidirectional');p['driver']=role in ('output','tri_state','bidirectional')
        p['capacitance_pf']=None;p['capacitance_status']='not-a-signal-IC-pin';p['full_OC1_maximum']=False
        if p['receiver'] or p['driver']:
            d=self.parts[part];output=p['driver']
            p['capacitance_pf']=d['inactive_output_pf'] if output else d['input_pf']
            p['capacitance_status']=d['inactive_output_status'] if output else d['input_status']
            p['full_OC1_maximum']=d['inactive_output_full_OC1'] if output else d['input_full_OC1']
            if part=='SN74HCT245N' and p['pin'] not in ('1','19'):
                p.update(capacitance_pf=10,capacitance_status='allocation-no-data-port-maximum',full_OC1_maximum=False)

    def matrix(self):
        rows=[]
        for net,pins in sorted(self.nets.items()):
            ids=sorted(p['id'] for p in pins);drivers=[p for p in pins if p['driver']]
            contacts=[p['id'] for p in pins if p['electrical_role']=='contact']
            signal=net not in self.rails
            unknowns=[]
            if signal:
                unknowns=[dict(term='traces/vias/pads',capacitance_pf=None),dict(term='testpoints/probes',capacitance_pf=None),
                    dict(term='IC sockets',capacitance_pf=None,pins=[p['id'] for p in pins if p['reference'].startswith(('U','Y'))]),
                    dict(term='connector contacts/mating',capacitance_pf=None,pins=contacts)]
                if contacts:unknowns.append(dict(term='unpopulated-slot/future-endpoint or external cable/receiver',capacitance_pf=None,
                    scope='No endpoint added to slots 6-8 in this assembly; fitted stubs still count. Terminal receiver unspecified.'))
                if any(p['electrical_role']=='resistor-terminal' for p in pins):
                    unknowns.append(dict(term='resistor parasitic capacitance',capacitance_pf=None))
            series=[r for r in self.resistors if r['kind']=='series' and net in r['nets']]
            scenarios=[]
            for driver in drivers if signal else []:
                loads=[p for p in pins if p['id']!=driver['id'] and (p['receiver'] or p['driver'])]
                subtotal=sum(p['capacitance_pf'] for p in loads)
                fixtures=self.parts[driver['part']]['selected_fixtures']
                scenarios.append(dict(driver=driver['id'],load_pins=sorted(p['id'] for p in loads),
                    receiver_pins=sorted(p['id'] for p in loads if p['receiver']),
                    other_output_pins=sorted(p['id'] for p in loads if p['driver']),
                    condition='This driver active; other potential outputs inactive. Bus exclusivity and output release not proven here.',
                    ic_only_pf=subtotal,unknown_pin_maxima=sorted(p['id'] for p in loads if not p['full_OC1_maximum']),
                    total_physical_load_pf=None,physical_qualification=False,
                    screens=[dict(**f,ic_only_exceeds=subtotal>f['load_pf'],remaining_before_unknown_pf=f['load_pf']-subtotal,
                        with_legacy_5pf=subtotal+5,legacy_5pf_exceeds=subtotal+5>f['load_pf']) for f in fixtures],
                    series_paths=[dict(resistor=r['reference'],nominal_ohm=r['nominal_ohm'],
                        remote_net=next(n for n in r['nets'] if n!=net),remote_load_pf=None,
                        note='Remote capacitance behind series resistor requires RC/threshold analysis; not a short or zero load.') for r in series]))
            rows.append(dict(net=net,native_names=sorted({p['native_name'] for p in pins}),pins=ids,
                cards=sorted({p['card'] for p in pins}),rail=self.rails.get(net),
                contacts=sorted(contacts),mating_pairs=[c for c in self.contacts if c['pins'][0] in ids],
                receiver_pins=sorted(p['id'] for p in pins if p['receiver']),driver_pins=sorted(p['id'] for p in drivers),
                resistors=[r for r in self.resistors if net in r['nets']],unknown_parasitics=unknowns,scenarios=scenarios))
        return rows

    def compare_prior(self,rows):
        by_net={r['net']:r for r in rows};refs={(c['board'],c['source_reference']):r for r,c in self.components.items() if c['source_reference']}
        comparisons=[]
        def add(study,label,old_pins,cap,allowance):
            physical={refs[b,r]+'.'+str(p) for b,r,p in old_pins}
            nets={self.pins[p]['net'] for p in physical};require(len(nets)==1,'Prior path split: '+str(label))
            row=by_net[next(iter(nets))];present=set(row['receiver_pins'])|set(row['driver_pins'])
            comparisons.append(dict(study=study,label=label,net=row['net'],prior_pins=sorted(physical),
                additional_IC_pins=sorted(present-physical),prior_allocated_pf=cap,prior_wire_pf=allowance,
                fitted_contact_pins=len(row['contacts']),driver_loads=[dict(driver=s['driver'],ic_only_pf=s['ic_only_pf'],
                    delta_IC_pf=s['ic_only_pf']-(cap-allowance),screens=s['screens']) for s in row['scenarios']]))
        for r in json.loads((BUILD/'cp1-hct273/loads.json').read_text()):
            ps=r['drivers']+r['receivers']
            add('R2',r['labels'],[(p['board'],p['ref'],p['pin']) for p in ps],r['allocated_load_pf'],
                r['allocated_load_pf']-sum(p['capacitance_pf'] or 0 for p in r['receivers'])-
                max(0,sum(p['capacitance_pf'] or 0 for p in r['drivers'])-min(p['capacitance_pf'] or 0 for p in r['drivers'])))
        b=json.loads((BUILD/'cp1-bridge/summary.json').read_text())['package_load_audit']
        for r in b['loads']:add('BR1',r['nets'],r['input_pins']+r['ic_drivers'],r['input_cap_max_pf']+5,5)
        t=json.loads((BUILD/'cp1-text/final/audit.json').read_text())
        tx=ET.parse(BUILD/'cp1-text/iteration-2/native/TX1/TX1.xml').getroot()
        txnets={n.get('name').removeprefix('/'):n for n in tx.findall('./nets/net')}
        for r in t['loads']:
            old_pins=[('TX1',ref,p) for ref,p in r['pins']]
            for p in txnets[r['net']].findall('node'):
                ref,pin=p.get('ref'),p.get('pin')
                if self.pins[refs['TX1',ref]+'.'+pin]['driver']:old_pins.append(('TX1',ref,pin))
            add('TX1',[r['net']],old_pins,r['input_cap_pf']+5,5)
        return comparisons

    def generate(self):
        rows=self.matrix();comparisons=self.compare_prior(rows)
        counts=Counter(p['electrical_role'] for p in self.pins.values())
        scenarios=[s for r in rows for s in r['scenarios']]
        return dict(revision='CP1-LL1',accepted_revision='CP1-R2',physical_qualification=False,
            source_native_sha256=digest(self.path),parts=self.parts,pins=self.pins,contacts=self.contacts,
            hct245_directions=self.directions,resistors=self.resistors,nets=rows,prior_comparisons=comparisons,
            summary=dict(components=len(self.components),physical_pins=len(self.pins),mated_groups=len(rows),
                signal_groups=sum(r['rail'] is None for r in rows),pin_roles=dict(counts),
                contact_pairs=len(self.contacts),driver_scenarios=len(scenarios),
                ic_only_over_fixture=sum(any(f['ic_only_exceeds'] for f in s['screens']) for s in scenarios),
                legacy_5pf_over_fixture=sum(any(f['legacy_5pf_exceeds'] for f in s['screens']) for s in scenarios),
                all_totals_unknown=all(s['total_physical_load_pf'] is None for s in scenarios)))


def validate_report(report,expected):
    require(report['physical_qualification'] is False,'LL1 cannot qualify physical operation')
    listed=[p for n in report['nets'] for p in n['pins']]
    require(len(listed)==len(set(listed)) and set(listed)==set(expected['pins']),'Incomplete or duplicated inventory pins')
    require(report['contacts']==expected['contacts'],'Incomplete or changed physical mating contacts')
    require(report['resistors']==expected['resistors'],'Incomplete resistor accounting')
    for row in report['nets']:
        for scenario in row['scenarios']:
            pins=scenario['load_pins']
            require(scenario['driver'] not in pins and len(pins)==len(set(pins)),'Driver self-load or duplicate capacitance')
            require(scenario['ic_only_pf']==sum(report['pins'][p]['capacitance_pf'] for p in pins),'Incorrect load arithmetic')
            require(scenario['total_physical_load_pf'] is None,'Unknown parasitics silently bounded')
    require(report==expected,'LL1 inventory differs from native/source-derived replay')


def mutations(result):
    faults={}
    bad=deepcopy(result)
    target=next(r for r in bad['nets'] if r['receiver_pins'] and r['scenarios'])
    pin=target['receiver_pins'][0];target['pins'].remove(pin)
    faults['dropped-receiver']=bad
    bad=deepcopy(result);bad['contacts'].pop();faults['dropped-contact']=bad
    bad=deepcopy(result);bad['resistors'].pop();faults['dropped-resistor']=bad
    bad=deepcopy(result)
    p=next(p for p in bad['pins'].values() if p['capacitance_status']=='allocation-no-data-port-maximum')
    p['full_OC1_maximum']=True;faults['unjustified-port-maximum']=bad
    out={}
    for name,bad in faults.items():
        try:validate_report(bad,result)
        except ValueError as error:out[name]=dict(detected=True,error=str(error))
        else:raise ValueError('Undetected mutation: '+name)
    try:Inventory(ca.STUDY/'final/global-bypass/CA1.xml')
    except ValueError as error:out['aliased-card-domains']=dict(detected=True,error=str(error))
    else:raise ValueError('Undetected aliased card domains')
    return out


def run(folder):
    cae.load();folder=Path(folder);require(not folder.exists(),'Preserve LL1 run');folder.mkdir(parents=True)
    a=Inventory();result=a.generate();validate_report(result,result);write_json(folder/'inventory.json',result)
    write_json(folder/'mutations.json',mutations(result))
    print(json.dumps(result['summary'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();run(args.output)

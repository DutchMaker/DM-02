"""Explicit package allocation; validate gate pin remapping by endpoint geometry."""
from copy import deepcopy
import json
from .common import ROOT, VROOT, BUILD, evidence, write_json
from .legacy import read_sheet, library, connectivity, inventory


def allocate(sheet,plan):
    proposed=deepcopy(sheet); parts={c['stamp']:c for c in proposed['components']}
    changes=[]; claimed=set(); refs=set()
    for group in plan:
        ref=group['ref']
        if ref in refs: raise ValueError('Duplicate package reference: '+ref)
        refs.add(ref); units=set(); identity=None
        for stamp,unit in group['instances']:
            if stamp in claimed or unit in units: raise ValueError('Duplicate instance or package unit')
            claimed.add(stamp); units.add(unit); c=parts[stamp]
            if identity and identity!=c['lib_id']: raise ValueError('Mixed symbols in one package')
            identity=c['lib_id']; ns,name=identity.split(':')
            definition=library(ns)[name]
            target=[p for p in definition['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,c['convert'])]
            a,b,cc,d=c['matrix']
            pins=[dict(p,x=c['x']+a*p['x']+b*p['y'],y=c['y']+cc*p['x']+d*p['y']) for p in target]
            def shape(p): return p['x'],p['y'],p['kind'],p['hidden']
            old={shape(p):p for p in c['pins']}; new={shape(p):p for p in pins}
            if len(old)!=len(c['pins']) or len(new)!=len(pins) or old.keys()!=new.keys():
                raise ValueError(f'Unit remapping moves or changes pins: {stamp}')
            changes.append(dict(stamp=stamp,old_ref=c['ref'],old_unit=c['unit'],old_value=c['value'],
                                ref=ref,unit=unit,value=group['value'],
                                pin_map={p['number']:new[shape(p)]['number'] for p in c['pins']}))
            c.update(ref=ref,original_ref=ref,unit=unit,value=group['value'],pins=pins)
        # A footprint must agree between units even when the legacy source
        # provided it on only one instance. No footprint is guessed here.
        footprints={parts[s]['footprint'] for s,_ in group['instances'] if parts[s]['footprint']}
        if len(footprints)>1: raise ValueError('Conflicting package footprints: '+ref)
        for stamp,_ in group['instances']: parts[stamp]['footprint']=next(iter(footprints),'')
    unclaimed={c['stamp'] for c in sheet['components'] if c['ref'].startswith('U')}-claimed
    if unclaimed: raise ValueError('Unallocated IC instances: '+str(sorted(unclaimed)))
    inventory(proposed)  # Reject duplicate physical pin assignments and conflicts.
    # Canonicalise nets back to immutable instance/pin endpoints. Every label
    # and every original endpoint must remain in exactly the same net.
    def canonical(s):
        identities={}
        for c in s['components']:
            for p in c['pins']:
                identities.setdefault((c['ref'],p['number']),[]).append((c['stamp'],p['x'],p['y']))
        return sorted((tuple(n['labels']),tuple(sorted(x for node in n['nodes'] for x in identities[tuple(node)])))
                      for n in connectivity(s))
    if canonical(sheet)!=canonical(proposed): raise ValueError('Package allocation changes electrical connectivity')
    return proposed,changes


def run():
    plan=json.loads((VROOT/'package-plan.json').read_text()); rows=[]
    for name,groups in plan['sheets'].items():
        sheet=read_sheet(ROOT/f'Circuits/KiCad/{name}/{name}.sch')
        proposed,changes=allocate(sheet,groups)
        applied=all(c['original_ref']==p['ref'] and c['unit']==p['unit'] and c['value']==p['value']
                    for c,p in zip(sheet['components'],proposed['components']))
        rows.append(dict(sheet=name,applied=applied,instances=len(changes),packages=len(groups),changes=changes))
    write_json(BUILD/'inventory/package-allocation.json',dict(basis=plan['basis'],sheets=rows))
    return evidence('packages','Physical gate/package allocation','pass' if all(r['applied'] for r in rows) else 'limited',
                    f'{sum(r["instances"] for r in rows)} IC instances assigned to {sum(r["packages"] for r in rows)} packages; endpoint connectivity preserved.',
                    artifacts=['inventory/package-allocation.json'],limitation='Function and package-unit allocation only. Electrical wiring checks, exact manufacturer grades, footprints and procurement are separate gates.')

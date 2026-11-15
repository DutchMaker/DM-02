"""Read the project's flat Eeschema v4 sheets and v2.4 symbol libraries.

No electrical identity is inferred from a displayed value. Connectivity uses
symbol pin numbers, the instance transform, wires, junctions and labels.
Hierarchy and bus aliases fail closed. Bus graphics are retained; only scalar
labels establish bus-member connectivity (no vector/group-label expansion).
"""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import re
import shlex
from .common import ROOT, VROOT


@lru_cache(maxsize=None)
def library(name):
    local = ROOT / 'Circuits/KiCad/Libraries' / (name + '.lib')
    path = local if local.exists() else VROOT / 'vendor/kicad5' / (name + '.lib')
    if not path.exists():
        raise ValueError(f'Missing pinned symbol library: {name}; run bootstrap.py')
    definitions = {}
    for block in re.findall(r'^DEF (.*?)^ENDDEF', path.read_text(), re.M | re.S):
        lines = block.splitlines()
        header = shlex.split(lines[0])
        definition = dict(name=header[0], power=header[-1] == 'P', pins=[], path=str(path.relative_to(ROOT)))
        for line in lines[1:]:
            if line.startswith('X '):
                t = line.split()  # Legacy pin names may contain a literal apostrophe.
                definition['pins'].append(dict(name=t[1], number=t[2], x=int(t[3]), y=int(t[4]),
                    unit=int(t[9]), convert=int(t[10]), kind=t[11], hidden='N' in t[12:]))
        definitions[header[0]] = definition
        for line in lines:
            if line.startswith('ALIAS '):
                for alias in shlex.split(line)[1:]:
                    definitions[alias] = definition
    return definitions


def read_sheet(path):
    path = Path(path)
    text = path.read_text()
    if not text.startswith('EESchema Schematic File Version 4'):
        raise ValueError(f'Unsupported schematic version: {path}')
    if any(s in text for s in ('$Sheet', 'Text HLabel', 'BusAlias')):
        raise ValueError(f'Unsupported hierarchy/bus aliases in {path}')
    sheet = dict(name=path.stem, source=str(path.relative_to(ROOT)), components=[], wires=[],
                 labels=[], junctions=[], no_connects=[], notes=[], buses=[], bus_entries=[])
    used_refs = set(re.findall(r'^L \S+ (\S+)', text, re.M))
    synthetic = 9000
    for match in re.finditer(r'^\$Comp\n(.*?)^\$EndComp', text, re.M | re.S):
        b = match[1]
        lines = b.splitlines()
        lib, original_ref = shlex.split(next(l for l in lines if l.startswith('L ')))[1:3]
        u = next(l for l in lines if l.startswith('U ')).split()
        pos = next(l for l in lines if l.startswith('P ')).split()
        matrix = list(map(int, lines[-1].split()))
        if len(matrix) != 4 or abs(matrix[0]*matrix[3]-matrix[1]*matrix[2]) != 1:
            raise ValueError(f'Invalid transform in {lib}')
        fields = {}
        for line in lines:
            if line.startswith('F '):
                tokens = shlex.split(line)
                fields[int(tokens[1])] = tokens[2]
        ref = original_ref
        if '?' in ref:
            while True:
                synthetic += 1
                ref = original_ref.replace('?', str(synthetic))
                if ref not in used_refs:
                    used_refs.add(ref)
                    break
        ns, symbol_name = lib.split(':', 1)
        definition = library(ns).get(symbol_name)
        if definition is None:
            raise ValueError(f'Unresolved symbol {lib}')
        c = dict(ref=ref, original_ref=original_ref, lib_id=lib, value=fields.get(1, ''),
                 footprint=fields.get(2, ''), unit=int(u[1]), convert=int(u[2]), stamp=u[3],
                 x=int(pos[1]), y=int(pos[2]), matrix=matrix, pins=[],
                 power=definition['power'], line=text[:match.start()].count('\n')+1,
                 library_source=definition['path'])
        for pin in definition['pins']:
            if pin['unit'] not in (0, c['unit']) or pin['convert'] not in (0, c['convert']):
                continue
            a,b_,cc,d = matrix
            p = dict(pin, x=c['x']+a*pin['x']+b_*pin['y'], y=c['y']+cc*pin['x']+d*pin['y'])
            c['pins'].append(p)
            # Legacy hidden power inputs are implicit global labels, not floats.
            if pin['hidden'] and pin['kind'] == 'W':
                sheet['labels'].append(dict(name=pin['name'], x=p['x'], y=p['y'], implicit=True))
        if definition['power'] and c['pins']:
            # PWR_FLAG is a power-output marker, not an implicit global net.
            if symbol_name != 'PWR_FLAG':
                p = c['pins'][0]
                sheet['labels'].append(dict(name=fields.get(1, symbol_name), x=p['x'], y=p['y'], implicit=True))
        sheet['components'].append(c)
    lines = text.splitlines()
    for i,l in enumerate(lines):
        if l == 'Wire Wire Line':
            sheet['wires'].append(list(map(int, lines[i+1].split())))
        elif l == 'Wire Bus Line':
            sheet['buses'].append(list(map(int, lines[i+1].split())))
        elif l == 'Entry Wire Line':
            sheet['bus_entries'].append(list(map(int, lines[i+1].split())))
        elif l.startswith(('Text Label ', 'Text GLabel ')):
            t = l.split()
            if any(c in lines[i+1] for c in '[]{}'):
                raise ValueError('Vector/group bus labels are not supported')
            sheet['labels'].append(dict(name=lines[i+1], x=int(t[2]), y=int(t[3]), implicit=False))
        elif l.startswith('Connection ~ '):
            sheet['junctions'].append(list(map(int, l.split()[2:])))
        elif l.startswith('NoConn ~ '):
            sheet['no_connects'].append(list(map(int, l.split()[2:])))
    return sheet


def on_segment(p, wire):
    x,y = p
    x1,y1,x2,y2 = wire
    return ((x-x1)*(y2-y1) == (y-y1)*(x2-x1)
            and min(x1,x2) <= x <= max(x1,x2) and min(y1,y2) <= y <= max(y1,y2))


def connectivity(sheet):
    parent = {}
    def find(p):
        parent.setdefault(p,p)
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]
    def union(a,b):
        parent[find(a)] = find(b)
    points = set(map(tuple, sheet['junctions']))
    for w in sheet['wires']:
        points.update([tuple(w[:2]),tuple(w[2:])])
    for c in sheet['components']:
        points.update((p['x'],p['y']) for p in c['pins'])
    points.update((l['x'],l['y']) for l in sheet['labels'])
    for p in points:
        find(p)
    for w in sheet['wires']:
        for p in points:
            if on_segment(p,w):
                union(tuple(w[:2]),p)
    names = {}
    for l in sheet['labels']:
        p=(l['x'],l['y'])
        if l['name'] in names:
            union(p,names[l['name']])
        names[l['name']] = p
    groups = defaultdict(lambda: dict(labels=set(), nodes=set()))
    for c in sheet['components']:
        if c['original_ref'].startswith('#'):
            continue
        for p in c['pins']:
            groups[find((p['x'],p['y']))]['nodes'].add((c['ref'],p['number']))
    for l in sheet['labels']:
        groups[find((l['x'],l['y']))]['labels'].add(l['name'])
    nets = []
    for g in groups.values():
        if g['nodes']:
            nets.append(dict(labels=sorted(g['labels']),nodes=[list(n) for n in sorted(g['nodes'])]))
    # A physical pin must never be silently represented in two different nets.
    owners = {}
    for i,g in enumerate(nets):
        for node in g['nodes']:
            key=tuple(node)
            if key in owners and owners[key] != i:
                raise ValueError(f'Physical pin belongs to multiple nets: {key}')
            owners[key]=i
    return sorted(nets,key=lambda n:n['nodes'])


def function_number(name):
    m = re.search(r'74(?:LS|HCT|HC|ALS|ACT|AC)?(\d+)',name,re.I)
    return m[1] if m else None


def inventory(sheet):
    issues=[]
    packages={}
    for c in sheet['components']:
        if c['original_ref'].startswith('#'):
            continue
        if c['ref'] in packages:
            p = packages[c['ref']]
            if c['unit'] in p['units'] or any(p[k] != c[k] for k in ('lib_id', 'value', 'footprint')):
                raise ValueError(f'Inconsistent physical package or repeated unit: {c["ref"]}')
        packages.setdefault(c['ref'],dict(ref=c['ref'],value=c['value'],lib_id=c['lib_id'],
                                          footprint=c['footprint'],units=[],procurement='unresolved'))['units'].append(c['unit'])
        if '?' in c['original_ref']:
            issues.append(dict(kind='unannotated',ref=c['ref'],line=c['line'],detail='Review-only reference; physical gate/package allocation is unresolved'))
        sym=c['lib_id'].split(':')[1]
        sf,vf=function_number(sym),function_number(c['value'])
        if (sf and vf and sf!=vf) or (sym.startswith(('M27','UM6')) and vf):
            issues.append(dict(kind='identity_conflict',ref=c['ref'],line=c['line'],
                detail=f"Symbol {sym} conflicts with value {c['value']}; no part substituted"))
    return dict(name=sheet['name'],source=sheet['source'],instances=len(sheet['components']),
                packages=list(packages.values()),issues=issues,
                pins=sum(len(c['pins']) for c in sheet['components']),wires=len(sheet['wires']),
                bus_entries=len(sheet['bus_entries']), nets=connectivity(sheet))

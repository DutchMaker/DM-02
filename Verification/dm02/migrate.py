"""Generate review-only modern sheets with explicit, transformed pin endpoints.

These are electrical review drawings, not fabrication schematics. Original
graphics are intentionally replaced with pin-numbered boxes. Package assignments
for U? are unresolved and get unique review refs. KiCad independently extracts
the generated sheet; its net groups must match the legacy geometry extractor.
"""
from collections import defaultdict
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET
from .common import ROOT, command, write_json
from .legacy import connectivity
from .sexpr import quote as q

TYPES={'I':'input','O':'output','B':'bidirectional','T':'tri_state','P':'passive',
       'U':'unspecified','W':'power_in','w':'power_out','C':'open_collector','E':'open_emitter','N':'no_connect'}


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'dm02-review/'+name))


def mm(value):
    return f'{value*0.0254:.6f}'


def generate(sheet,path):
    root=uid(sheet['source'])
    out=[f'(kicad_sch (version 20250114) (generator "dm02_review") (uuid {root}) (paper "A3")',
         '(lib_symbols']
    packages=defaultdict(list)
    for c in sheet['components']:
        packages[c['ref']].append(c)
    for ref,parts in packages.items():
        lid='DM02:'+ref.replace('#','_')
        out.append(f'(symbol {q(lid)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes)')
        for name,value in [('Reference',ref),('Value',parts[0]['value'])]:
            out.append(f'(property {q(name)} {q(value)} (at 0 0 0) (effects (font (size 1.27 1.27))))')
        seen=set()
        for c in parts:
            if c['unit'] in seen:
                raise ValueError(f'Duplicate package unit {ref}.{c["unit"]}')
            seen.add(c['unit'])
            out.append(f'(symbol {q(ref.replace("#","_")+"_"+str(c["unit"])+"_1")}')
            out.append('(rectangle (start -2.54 2.54) (end 2.54 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))')
            for p in c['pins']:
                x,y=p['x']-c['x'],c['y']-p['y']
                out.append(f'(pin {TYPES[p["kind"]]} line (at {mm(x)} {mm(y)} 0) (length 0)'
                    f'(name {q(p["name"])} (effects (font (size 1.016 1.016))))'
                    f'(number {q(p["number"])} (effects (font (size 1.016 1.016)))))')
            out.append(')')
        out.append(')')
    out.append(')')
    for i,w in enumerate(sheet['wires']):
        out.append(f'(wire (pts (xy {mm(w[0])} {mm(w[1])}) (xy {mm(w[2])} {mm(w[3])}))'
                   f'(stroke (width 0) (type default)) (uuid {uid(root+"wire"+str(i))}))')
    for i,w in enumerate(sheet.get('buses', [])):
        out.append(f'(bus (pts (xy {mm(w[0])} {mm(w[1])}) (xy {mm(w[2])} {mm(w[3])}))'
                   f'(stroke (width 0) (type default)) (uuid {uid(root+"bus"+str(i))}))')
    for i,w in enumerate(sheet.get('bus_entries', [])):
        out.append(f'(bus_entry (at {mm(w[0])} {mm(w[1])}) (size {mm(w[2]-w[0])} {mm(w[3]-w[1])})'
                   f'(stroke (width 0) (type default)) (uuid {uid(root+"entry"+str(i))}))')
    for i,p in enumerate(sheet['junctions']):
        out.append(f'(junction (at {mm(p[0])} {mm(p[1])}) (diameter 0) (color 0 0 0 0) (uuid {uid(root+"junction"+str(i))}))')
    for i,p in enumerate(sheet['no_connects']):
        out.append(f'(no_connect (at {mm(p[0])} {mm(p[1])}) (uuid {uid(root+"nc"+str(i))}))')
    seen_labels=set()
    for i,l in enumerate(sheet['labels']):
        key=(l['name'],l['x'],l['y'])
        if key in seen_labels:
            continue
        seen_labels.add(key)
        out.append(f'(label {q(l["name"])} (at {mm(l["x"])} {mm(l["y"])} 0)'
                   f'(effects (font (size 1.016 1.016)) (justify left bottom)) (uuid {uid(root+"label"+str(i))}))')
    for c in sheet['components']:
        ref=c['ref']; lid='DM02:'+ref.replace('#','_')
        out.append(f'(symbol (lib_id {q(lid)}) (at {mm(c["x"])} {mm(c["y"])} 0) (unit {c["unit"]})'
                   f'(in_bom yes) (on_board yes) (dnp no) (uuid {uid(root+c["stamp"])} )')
        for i,(name,value) in enumerate([('Reference',ref),('Value',c['value']),('Footprint',c['footprint']),('SourceSymbol',c['lib_id'])]):
            out.append(f'(property {q(name)} {q(value)} (at {mm(c["x"])} {mm(c["y"]-200+i*100)} 0)'
                       f'(effects (font (size 1.016 1.016))'+ (' (hide yes)' if i>1 else '')+'))')
        out.append(f'(instances (project {q(path.stem)} (path {q("/"+root)} (reference {q(ref)}) (unit {c["unit"]})))) )')
    out.append(')')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(out)+'\n')


def validate(sheet,folder):
    path=folder/(sheet['name']+'.kicad_sch')
    generate(sheet,path)
    netfile=path.with_suffix('.xml')
    netfile.unlink(missing_ok=True)
    code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',netfile,path])
    path.with_suffix('.log').write_text(log)
    if code or not netfile.exists():
        raise ValueError(f'KiCad export failed for {sheet["name"]}: {log[-1000:]}')
    xml=ET.parse(netfile).getroot()
    expected_refs={c['ref'] for c in sheet['components'] if not c['ref'].startswith('#')}
    actual_refs={c.attrib['ref'] for c in xml.findall('./components/comp')}
    if not actual_refs or actual_refs != expected_refs:
        raise ValueError(f'Component preservation failed: missing {expected_refs-actual_refs}, extra {actual_refs-expected_refs}')
    expected=connectivity(sheet)
    # Singleton unconnected pins may be omitted by KiCad. Connected groups may not.
    groups=lambda nets:{frozenset(tuple(n) for n in g) for g in nets if len(g)>1}
    exp=groups([n['nodes'] for n in expected])
    actual=[]
    for net in xml.findall('./nets/net'):
        actual.append([(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')])
    act=groups(actual)
    mismatch=[dict(kind='missing' if g in exp else 'extra',nodes=sorted(g)) for g in exp^act]
    write_json(path.with_suffix('.comparison.json'),dict(expected_connected_nets=len(exp),actual_connected_nets=len(act),differences=mismatch))
    return dict(sheet=sheet['name'],status='pass' if not mismatch else 'fail',
                components=len(actual_refs),connected_nets=len(exp),differences=len(mismatch),
                artifact=str(path.relative_to(folder.parent)), limitation='Review geometry only; package allocation, original graphics and fabrication approval are not implied')

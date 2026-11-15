"""Independent KiCad symbol import and native placement of legacy instances.

The ordinary review route embeds Python-interpreted pin endpoints. This route
discards those symbols, lets KiCad import the original library definitions,
and expresses instance rotations/mirrors in KiCad's own placement format.
"""
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from .common import ROOT, command, digest, write_json
from .migrate import generate as review_generate
from .sexpr import parse, quote
from .legacy import connectivity


def blocks(text):
    """Top-level child expressions, preserving their original token spelling."""
    depth=0;quoted=False;escaped=False;start=None;result=[]
    for i,ch in enumerate(text):
        if quoted:
            if escaped: escaped=False
            elif ch=='\\': escaped=True
            elif ch=='"': quoted=False
            continue
        if ch=='"': quoted=True
        elif ch=='(':
            if depth==1: start=i
            depth+=1
        elif ch==')':
            depth-=1
            if depth==1: result.append(text[start:i+1])
    if depth or quoted: raise ValueError('Unbalanced native KiCad expression')
    return result


def flatten(name,symbols,visiting=()):
    if name in visiting: raise ValueError('Symbol inheritance loop')
    fields=blocks(symbols[name]);parent=next((parse(f)[1] for f in fields if f.startswith('(extends ')),None)
    if parent:
        inherited=flatten(parent,symbols,visiting+(name,))
        overrides={tuple(parse(f)[:2]) if f.startswith('(property ') else (parse(f)[0],) for f in fields}
        fields=[f for f in inherited if
                (tuple(parse(f)[:2]) if f.startswith('(property ') else (parse(f)[0],)) not in overrides]+fields
    return [f for f in fields if not f.startswith('(extends ')]


def orientation(matrix):
    # KiCad positive rotations are counterclockwise on the sheet. Mirror X
    # reflects the placed symbol's screen Y coordinate after rotation.
    rotations={0:(1,0,0,-1),90:(0,-1,-1,0),180:(-1,0,0,1),270:(0,1,1,0)}
    for angle,m in rotations.items():
        if tuple(matrix)==m: return angle,''
        a,b,c,d=m
        if tuple(matrix)==(a,b,-c,-d): return angle,' (mirror x)'
    raise ValueError('Unsupported legacy transform: '+str(matrix))


def generate(sheet,folder):
    folder.mkdir(parents=True,exist_ok=True)
    libs={};provenance=[]
    for source in sorted({c['library_source'] for c in sheet['components']}):
        original=ROOT/source;dest=folder/(original.stem+'.kicad_sym')
        dest.unlink(missing_ok=True)
        code,log=command(['kicad-cli','sym','upgrade','--output',dest,original])
        dest.with_suffix('.log').write_text(log)
        if code or not dest.exists(): raise ValueError('Native library import failed: '+log)
        libs[source]={parse(b)[1]:b for b in blocks(dest.read_text()) if b.startswith('(symbol ')}
        provenance.append(dict(source=source,sha256=digest(original),imported=dest.name,imported_sha256=digest(dest)))
    path=folder/(sheet['name']+'.kicad_sch')
    geometry=deepcopy(sheet)
    # Native power symbols and hidden power pins must establish their own nets.
    geometry['labels']=[l for l in geometry['labels'] if not l.get('implicit')]
    review_generate(geometry,path)
    text=path.read_text();embedded=[];seen=set()
    for c in sheet['components']:
        ref=c['ref'];name=c['lib_id'].split(':')[1]
        if ref in seen: continue
        seen.add(ref)
        fields=flatten(name,libs[c['library_source']])
        fields=[re.sub(r'^\(symbol "[^"]+_(\d+_\d+)"',lambda m:'(symbol '+quote(ref.replace('#','_')+'_'+m[1]),f)
                if f.startswith('(symbol ') else f for f in fields]
        embedded.append('(symbol '+quote('DM02:'+ref.replace('#','_'))+'\n'+'\n'.join(fields)+')')
    old=next(b for b in blocks(text) if b.startswith('(lib_symbols'))
    text=text.replace(old,'(lib_symbols\n'+'\n'.join(embedded)+')',1)
    instances=[b for b in blocks(text) if b.startswith('(symbol (lib_id ')]
    if len(instances)!=len(sheet['components']): raise ValueError('Instance count changed during native placement')
    for instance,c in zip(instances,sheet['components']):
        angle,mirror=orientation(c['matrix'])
        new=re.sub(r'\(at ([^ ]+) ([^ ]+) 0\)',lambda m:f'(at {m[1]} {m[2]} {angle})'+mirror,instance,count=1)
        text=text.replace(instance,new,1)
    path.write_text(text)
    write_json(folder/'libraries.json',provenance)
    return path


def validate(sheet,folder):
    path=generate(sheet,folder);netfile=path.with_suffix('.xml');netfile.unlink(missing_ok=True)
    code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',netfile,path])
    path.with_suffix('.log').write_text(log)
    if code or not netfile.exists(): raise ValueError('Native-symbol netlist failed: '+log)
    xml=ET.parse(netfile).getroot()
    expected_refs={c['ref'] for c in sheet['components'] if not c['ref'].startswith('#')}
    actual_refs={c.attrib['ref'] for c in xml.findall('./components/comp')}
    if not actual_refs or actual_refs!=expected_refs: raise ValueError('Native-symbol component preservation failed')
    groups=lambda nets:{frozenset(tuple(n) for n in g) for g in nets if g}
    expected=groups(n['nodes'] for n in connectivity(sheet))
    actual=groups([(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')
                   if not n.attrib['ref'].startswith('#')] for net in xml.findall('./nets/net'))
    differences=[dict(kind='missing' if g in expected else 'extra',nodes=sorted(g)) for g in expected^actual]
    result=dict(sheet=sheet['name'],status='pass' if not differences else 'fail',components=len(actual_refs),
                net_groups=len(expected),connected_nets=sum(len(g)>1 for g in expected),
                physical_pins=sum(len(g) for g in expected),differences=differences,
                source_hash=digest(ROOT/sheet['source']),
                scope='KiCad imports original legacy library geometry; native rotations, mirrors, unit placement and hidden supplies. '
                      'All pin groups, including unconnected singletons, are compared. '
                      'Source placement/wire/label parsing is shared; annotation graphics and fabrication approval are excluded.')
    write_json(folder/'comparison.json',result)
    return result

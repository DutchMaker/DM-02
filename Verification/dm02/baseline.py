"""Inventory, review migration, and layout completeness evidence."""
from collections import Counter
import json
from .common import ROOT, VROOT, BUILD, digest, evidence, write_json
from .legacy import read_sheet, inventory
from .migrate import validate
from .native_migrate import validate as native_validate
from .sexpr import parse, children, child


def run():
    manifest=json.loads((VROOT/'vendor/kicad5/manifest.json').read_text())
    if manifest['commit']!='2777f4341e7d96346cb8c78574350d64033c615c' or len(manifest['files'])!=10:
        raise ValueError('Unexpected historical-symbol manifest')
    for file in manifest['files']:
        if digest(VROOT/'vendor/kicad5'/file['name'])!=file['sha256']:
            raise ValueError(f'Pinned library hash mismatch: {file["name"]}')
    sheets={}; inventories=[]; migrations=[];native=[]
    paths=sorted((ROOT/'Circuits/KiCad').glob('*/*.sch'))
    if len(paths)!=7: raise ValueError(f'Expected seven baseline sheets; got {len(paths)}. Review scope before updating this count.')
    for path in paths:
        sheet=read_sheet(path); sheets[sheet['name']]=sheet
        inv=inventory(sheet); inventories.append(inv)
        write_json(BUILD/'inventory'/(sheet['name']+'.json'),inv)
        migrations.append(validate(sheet,BUILD/'schematics'))
        native.append(native_validate(sheet,BUILD/'native-schematics'/sheet['name']))
    issues=[dict(sheet=i['name'],**x) for i in inventories for x in i['issues']]
    write_json(BUILD/'inventory/summary.json',dict(sheets=inventories,issues=issues))
    boards=[]
    for path in sorted((ROOT/'Circuits/KiCad').glob('*/*.kicad_pcb')):
        tree=parse(path.read_text())
        modules=children(tree,'module')+children(tree,'footprint')
        refs=[]
        for m in modules:
            ref=next((t[2] for t in children(m,'fp_text') if t[1]=='reference'),None)
            if ref: refs.append(ref)
        inv=next((i for i in inventories if i['name']==path.stem),None)
        expected={p['ref'] for p in inv['packages']} if inv else set()
        boards.append(dict(name=path.stem,source=str(path.relative_to(ROOT)),footprints=len(modules),
                           segments=len(children(tree,'segment')),vias=len(children(tree,'via')),
                           missing_schematic_refs=sorted(expected-set(refs)),extra_pcb_refs=sorted(set(refs)-expected),
                           limitation='Counts and reference comparison only; not ERC/DRC, pad-net equivalence or fabrication sign-off.'))
    if len(boards)!=6: raise ValueError('Expected six baseline boards')
    write_json(BUILD/'boards.json',boards)
    counts=Counter(x['kind'] for x in issues)
    rows=[evidence('migration','Legacy electrical review migration',
                    'pass' if all(m['status']=='pass' for m in migrations+native) else 'fail',
                    f'{len(migrations)} sheets checked by endpoint review and native KiCad symbol import; '
                    f'{sum(m["net_groups"] for m in native):,} complete pin groups agree, including singletons.',
                    rows=migrations,native_rows=native,
                    artifacts=['inventory/summary.json']+[f'schematics/{s["sheet"]}.comparison.json' for s in migrations]+
                              [f'native-schematics/{s["sheet"]}/{name}' for s in native
                               for name in ('comparison.json','libraries.json',s['sheet']+'.kicad_sch',s['sheet']+'.xml')],
                    limitation='Native KiCad import interprets original library pins, units, rotation/mirror and hidden supply semantics independently of Python pin extraction. Source placement/wire/scalar-label parsing remains shared. This accepts electrical review migration, not fabrication, original annotation graphics or exact-part selection.'),
          evidence('bom','Physical-part identity and procurement','blocked',
                   f'{sum(len(i["packages"]) for i in inventories)} review package references; {counts["identity_conflict"]} identity conflicts; {counts["unannotated"]} unannotated instances.',
                   issues=issues,artifacts=['inventory/summary.json'],
                   limitation='An exact approved BOM, speed grades, stock, and ROM programmer support remain unresolved. LS/HC symbols with HCT values are pin-compatible candidates, not verified substitutions.'),
          evidence('pcb','PCB completeness','blocked','Six layouts inventoried; only the debugger contains routed segments.',rows=boards,artifacts=['boards.json'])]
    return rows,sheets

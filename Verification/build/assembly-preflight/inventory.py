"""FD1/BP1 physical-reference BOM and installed footprint pad-number preflight.

This checks pad-number coverage, not package geometry or mating suitability.
Run from the repository root with PYTHONPATH=Verification.
"""
from collections import Counter,defaultdict
from pathlib import Path
import re
import shutil
from designs.distribution_candidate import SOURCE
from dm02.common import ROOT,digest,write_json
from dm02.distribution_links import all_boards
from dm02.distribution_backplane import BACKPLANE,contract
from dm02.legacy import read_sheet
from dm02.sexpr import parse

HERE=Path(__file__).resolve().parent
LIBRARY=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'


def field(node,name):
    return next((v[1:] for v in node if isinstance(v,list) and v and v[0]==name),[])


def inventory():
    sheets={name:c.sheet for name,c in all_boards(SOURCE).items()}
    sheets['BP1']=read_sheet(BACKPLANE)
    footprints={};packages=[];boards=[];source_hashes={};conflicts=[]
    for name,sheet in sheets.items():
        source=ROOT/sheet['source'];source_hashes[sheet['source']]=digest(source)
        target=HERE/'sources'/name/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        grouped=defaultdict(list)
        for c in sheet['components']:
            if c['power']:continue
            grouped[c['ref']].append(c)
        board_rows=[]
        for ref,units in sorted(grouped.items()):
            identities={(u['value'],u['footprint'],u['lib_id']) for u in units}
            if len(identities)!=1:
                conflicts.append(dict(board=name,reference=ref,identities=sorted(identities)));continue
            value,footprint,symbol=next(iter(identities))
            if footprint not in footprints:
                library,part=footprint.split(':');path=LIBRARY/(library+'.pretty')/(part+'.kicad_mod')
                if not path.is_file():
                    footprints[footprint]=dict(available=False,pads=[],numbered_pads=[],
                                               error='Exact named footprint missing from installed KiCad library',
                                               similarly_named=[p.stem for p in path.parent.glob(part.split('_')[0]+'*.kicad_mod')])
                else:
                    tree=parse(path.read_text());pads=[]
                    for pad in tree:
                        if not isinstance(pad,list) or not pad or pad[0]!='pad':continue
                        pads.append(dict(number=pad[1],type=pad[2],shape=pad[3],at=field(pad,'at'),
                                         size=field(pad,'size'),drill=field(pad,'drill')))
                    copy=HERE/'footprints'/(library+'.pretty')/path.name;copy.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(path,copy)
                    footprints[footprint]=dict(available=True,sha256=digest(path),archived=str(copy.relative_to(HERE)),pads=pads,
                                               numbered_pads=sorted({p['number'] for p in pads if p['number']}))
            pins=sorted({p['number'] for u in units for p in u['pins']})
            pad_numbers=footprints[footprint]['numbered_pads']
            notes=[]
            if ref.startswith('J'):notes.append('Exact connector, gender, mating orientation and interconnect capacitance unselected.')
            elif ref.startswith(('C','R')):notes.append('Generic passive value: exact part, tolerance, dielectric/power/voltage and geometry unselected.')
            if value=='SST39SF040-70-4I-NHE':notes.append('PCB footprint represents a socket; eight separate sockets are needed in addition to eight flash ICs. Installed 0.80 mm-hole footprint is not qualified for Adam Tech PLCC-32-AT.')
            if value.startswith('ECS-'):notes.append('Drawn oscillator is not the FD1 4 MHz target. Exact replacement needs circuit and footprint review.')
            missing=sorted(set(pins)-set(pad_numbers));extra=sorted(set(pad_numbers)-set(pins))
            row=dict(board=name,reference=ref,value=value,symbol=symbol,footprint=footprint,
                     footprint_available=footprints[footprint]['available'],
                     units=sorted(u['unit'] for u in units),symbol_pin_numbers=pins,
                     missing_pads=missing,extra_pads=extra,pad_number_coverage_passed=not missing and not extra,
                     notes=notes,physical_qualification=False)
            packages.append(row);board_rows.append(row)
        boards.append(dict(board=name,source=sheet['source'],symbol_instances=len(sheet['components']),
                           physical_references=len(board_rows),by_reference_prefix=dict(Counter(re.sub(r'\d.*','',r['reference']) for r in board_rows)),
                           pad_number_coverage_passed=all(r['pad_number_coverage_passed'] for r in board_rows)))
    bom=defaultdict(list)
    for row in packages:bom[row['value'],row['footprint']].append(row['board']+':'+row['reference'])
    groups=[dict(value=value,footprint=footprint,quantity=len(refs),references=refs) for (value,footprint),refs in sorted(bom.items())]
    assert sum(row['quantity'] for row in groups)==len(packages)
    totals=dict(Counter(re.sub(r'\d.*','',r['reference']) for r in packages))
    headers=contract(SOURCE)['headers'];external=sum(h['board']=='EXTERNAL' for h in headers)
    paired=len(headers)-external
    assert totals['J']==2*paired+external
    for path,want in source_hashes.items():assert digest(ROOT/path)==want,path
    return dict(scope='FD1 final 13 sheets plus BP1. Multiunit symbols collapse to one board/reference. '
                      'Pad-number equality checks installed library coverage only; geometry, pin-1 orientation, socket tails, '
                      'connector mating and package procurement are not qualified. No PCB layout is generated.',
                source_hashes=source_hashes,boards=boards,packages=packages,bom=groups,footprints=footprints,
                conflicts=conflicts,physical_references=len(packages),bom_groups=len(groups),totals_by_reference_prefix=totals,
                connectors=dict(board_backplane_pairs=paired,external_backplane_headers=external,total=totals['J']),
                pad_number_coverage_passed=not conflicts and all(r['pad_number_coverage_passed'] for r in packages),
                release_ready=False,
                exclusions=['Reset supervisor/conditioning frontend and exact 4 MHz oscillator replacement',
                            'Eight physical flash sockets as separately procured items; IC references carry socket land patterns',
                            'Optional DIP IC sockets, bulk decoupling, power-entry hardware, mechanics and display electronics'])


if __name__=='__main__':
    result=inventory();write_json(HERE/'inventory.json',result)
    for row in result['boards']:print(row['board'],row['physical_references'],'references;',row['by_reference_prefix'])
    print('Total:',result['physical_references'],'references,',result['bom_groups'],'BOM groups,',len(result['footprints']),'footprints')
    print('Pad-number coverage:',result['pad_number_coverage_passed'])
    for row in result['packages']:
        if not row['pad_number_coverage_passed']:print('Mismatch:',row)

"""Bounded mechanical comparison from visually reviewed TI package drawings.

Run with PYTHONPATH=Verification. Assembly tolerances remain unqualified.
"""
from decimal import Decimal as D
from pathlib import Path
import json
from dm02.common import digest,write_json
from dm02.sexpr import parse

HERE=Path(__file__).resolve().parent


def field(node,name):
    return next(v[1:] for v in node if isinstance(v,list) and v and v[0]==name)


def review():
    provenance=json.loads((HERE/'manufacturer/sources.json').read_text())
    for name,source in provenance.items():assert digest(HERE/'manufacturer'/(name+'.pdf'))==source['sha256']
    inventory=json.loads((HERE/'inventory.json').read_text());rows=[]
    for part,count,length,spacing,document,pages,drawing in [
        ('CD74HCT377M96',20,'12.8','9.3','cd74hct377',[17,18],'DW0020A, 4220724/A 05/2016'),
        ('CD74HCT154M96',24,'15.4','9.4','cd74hct154',[12,13],'DW R-PDSO-G24, 4040000-5/G 01/11; land 4209202-5/F 08/13')]:
        name=f'Package_SO:SOIC-{count}W_7.5x{length}mm_P1.27mm'
        footprint=inventory['footprints'][name];path=HERE/footprint['archived'];assert digest(path)==footprint['sha256']
        tree=parse(path.read_text());pads={int(p[1]):p for p in tree if isinstance(p,list) and p and p[0]=='pad' and p[1]}
        assert set(pads)==set(range(1,count+1))
        half=count//2;pitch=D('1.27');center=D('4.65');pad_length=D('2.05');pad_width=D('.6')
        for number,pad in pads.items():
            x,y=map(D,field(pad,'at')[:2]);sx,sy=map(D,field(pad,'size'))
            index=number-1 if number<=half else count-number
            assert x==(-center if number<=half else center)
            assert y==pitch*(D(index)-D(half-1)/2)
            assert (sx,sy)==(pad_length,pad_width)
        # F.Fab is nominal package body geometry, not the tolerance envelope.
        body=[]
        for node in tree:
            if isinstance(node,list) and node and node[0]=='fp_poly' and field(node,'layer')==['F.Fab']:
                body.extend([list(map(D,point[1:])) for point in field(node,'pts')])
        body_width=max(p[0] for p in body)-min(p[0] for p in body)
        body_length=max(p[1] for p in body)-min(p[1] for p in body)
        assert (body_width,body_length)==(D('7.5'),D(length))
        inner=center-pad_length/2;outer=center+pad_length/2
        rows.append(dict(part=part,footprint=name,source=document+'.pdf',source_pages=pages,drawing=drawing,
            package_identity='Exact M96 orderable is Active/Production, SOIC (DW), in archived TI packaging table.',
            pins=count,pitch_mm=pitch,pin_sequence_top_view_checked=True,
            body_nominal_mm=[body_width,body_length],body_width_limits_mm=[D('7.4'),D('7.6')],
            body_length_limits_mm=[D(length)-D('.2'),D(length)+D('.2')],
            pad_size_mm=[pad_length,pad_width],pad_row_spacing_mm=2*center,
            ti_example_pad_size_mm=[D('2'),D('.6')],ti_example_row_spacing_mm=D(spacing),
            row_spacing_difference_mm=2*center-D(spacing),pad_length_difference_mm=pad_length-D('2'),
            lead_span_limits_mm=[D('9.97'),D('10.63')],lead_width_limits_mm=[D('.31'),D('.51')],
            lead_length_limits_mm=[D('.40'),D('1.27')],
            centered_axis_only=dict(toe_extension_min_mm=outer-D('10.63')/2,
                heel_extension_min_mm=D('9.97')/2-D('1.27')-inner,
                side_extension_min_mm=(pad_width-D('.51'))/2,
                scope='Ideal centered axis-aligned arithmetic only. Lead true-position tolerance, component placement, copper/mask fabrication, corner radii and solder process are excluded.'),
            geometry_identity_passed=True,assembly_qualified=False,
            open=['Assembler acceptance of IPC land pattern versus TI example',
                  'Placement/lead-position tolerance stack, solder mask and stencil',
                  'Board-level courtyard clearance and physical sample fit']))
    return dict(rows=rows,source_hashes=provenance,scope='Identity, nominal body, pitch and numbered pad sequence reviewed. This is not a fabrication or solder-joint qualification.')


if __name__=='__main__':
    result=review()
    # Preserve decimal arithmetic internally; JSON uses millimetre numbers.
    (HERE/'geometry.json').write_text(json.dumps(result,indent=2,default=float)+'\n')
    for row in result['rows']:print(row['part'],'identity/pitch/numbering pass; TI example row-spacing difference',row['row_spacing_difference_mm'],'mm')

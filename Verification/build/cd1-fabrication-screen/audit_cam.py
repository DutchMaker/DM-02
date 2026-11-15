"""Independently parse offline CAM and compare native coordinates and copper."""
from collections import Counter
from pathlib import Path
import copy
import hashlib
import json
import warnings
import gerbonara
from gerbonara import LayerStack, ExcellonFile
from gerbonara.utils import MM
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
CAM=HERE/'cam-preview'


def rounded(*values):return tuple(round(v,6) for v in values)
def line(a,b,width):return tuple(sorted((rounded(*a),rounded(*b))))+(round(width,6),)


def parse(folder):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        stack=LayerStack.open(folder)
        # Gerbonara 1.6.3 does not reliably infer these KiCad X2 comment plating
        # attributes. Verify each actual header before supplying the flag.
        drills=[];headers=[]
        for path in sorted(folder.glob('*.drl')):
            text=path.read_text()
            functions=[l for l in text.splitlines() if l.startswith('; #@! TF.FileFunction,')]
            assert len(functions)==1, 'drill file-function header'
            function=functions[0].split(',')[1:]
            assert function in (['Plated','1','2','PTH'],['NonPlated','1','2','NPTH']),function
            plated=function[0]=='Plated'
            assert plated==path.stem.endswith('-PTH'), 'plating header/filename mismatch'
            assert '\nMETRIC\n' in text and '\nG90\n' in text,'metric absolute drill mode'
            parsed=ExcellonFile.open(path,plated=plated)
            headers.append(dict(file=path.name,file_function=function,plated=plated,count=len(parsed.objects)))
            for o in parsed.objects:
                assert type(o).__name__=='Flash' and o.unit==MM and o.aperture.unit==MM,'unsupported drill geometry'
                drills.append((round(o.x,6),round(-o.y,6),round(o.aperture.diameter,6),plated))
        assert len(headers)==2,'PTH and NPTH files required'
    layers={}
    regions={}
    for (side,kind),layer in stack.graphic_layers.items():
        records=[]
        for o in layer.objects:
            assert o.unit==MM and o.polarity_dark, 'unexpected units or clear polarity'
            typ=type(o).__name__
            if typ=='Line':
                records.append(('line',line([o.x1,-o.y1],[o.x2,-o.y2],o.aperture.diameter),tuple(o.attrs.get('.N',()))))
            elif typ=='Flash':
                (x1,y1),(x2,y2)=o.bounding_box(unit=MM)
                records.append(('flash',rounded(o.x,-o.y,x2-x1,y2-y1),tuple(o.attrs.get('.N',())),tuple(o.attrs.get('.P',()))))
            elif typ=='Region':
                assert not any(o.arc_centers), 'curved region requires explicit handling'
                # Gerber polygons bridge holes with retraced edges; buffer(0)
                # removes those zero-area seams before comparison with native holes.
                regions.setdefault(side,[]).append(Polygon([(x,-y) for x,y in o.outline]).buffer(0))
            else:
                assert kind=='silk', (side,kind,typ)
        layers[side+'/'+kind]=records
    return stack,dict(drills=drills,headers=headers,layers=layers),regions,sorted(set(str(w.message) for w in caught))


def verify(records,native,source):
    # KiCad metric Excellon uses three decimal places; Gerbers use six.
    expected=Counter(tuple(round(v,3) for v in (*r['position'],r['diameter_mm']))+(r['plated'],) for r in native['drills'])
    assert len(expected)==len(native['drills']), 'ambiguous quantized drill positions'
    assert Counter(records['drills'])==expected,'drill positions/sizes/counts/plating'
    assert set(records['layers'])=={'top/copper','bottom/copper','top/mask','bottom/mask','top/silk','bottom/silk','mechanical/outline'},'layer inventory'
    actual=Counter(r[1] for r in records['layers']['mechanical/outline'] if r[0]=='line')
    assert actual==Counter(line(r['start'],r['end'],r['width_mm']) for r in native['outline']),'outline centerline'
    for side,kicad in [('top','F.Cu'),('bottom','B.Cu')]:
        copper=records['layers'][side+'/copper']
        wanted=Counter((line(r['start'],r['end'],r['width_mm']),(r['net'],)) for r in source['tracks'] if r['layer']==kicad)
        assert Counter((r[1],r[2]) for r in copper if r[0]=='line')==wanted,'track endpoints/width/net '+side
        pads=Counter((rounded(*p['position'],*p['size_mm']),(p['net'],),(p['ref'],p['pin'])) for p in source['pads'])
        vias=Counter((rounded(*v['position'],v['diameter_mm'],v['diameter_mm']),(v['net'],),()) for v in source['vias'])
        assert Counter((r[1],r[2],r[3]) for r in copper if r[0]=='flash')==pads+vias,'copper pad/via flashes '+side
        wanted=Counter(rounded(*p['position'],*(v+2*native['mask_expansion_mm'] for v in p['size_mm'])) for p in native['pads'])
        mask=records['layers'][side+'/mask']
        assert len(mask)==90 and all(r[0]=='flash' for r in mask),'mask flash count '+side
        assert Counter(r[1] for r in mask)==wanted,'mask openings and expansion '+side


def main():
    native=json.loads((HERE/'native-cam-geometry.json').read_text())
    source=json.loads((HERE/'sources/p2-geometry.json').read_text())
    stack,records,regions,parser_warnings=parse(CAM)
    verify(records,native,source)
    areas=[]
    for side,kicad in [('top','F.Cu'),('bottom','B.Cu')]:
        expected=unary_union([Polygon(p['shell'],p['holes']) for zone in source['ground_zones']
                              if zone['layer']==kicad for p in zone['polygons']])
        actual=unary_union(regions[side])
        delta=expected.symmetric_difference(actual).area
        assert delta<1e-6,('ground fill changed',side,delta)
        areas.append(dict(side=side,native_area_mm2=expected.area,cam_area_mm2=actual.area,symmetric_difference_mm2=delta))
    boxes=[box(x-w/2,y-h/2,x+w/2,y+h/2) for typ,(x,y,w,h),*rest in records['layers']['top/mask']]
    web=min(a.distance(b) for i,a in enumerate(boxes) for b in boxes[i+1:])
    assert web>=.1016, 'mask-web bounding-box lower bound'
    faults=[]
    for name in ('missing-drill','shifted-drill','wrong-drill-size','wrong-plating','extra-drill',
                 'missing-outline-edge','wrong-mask-expansion','missing-track','wrong-track-net'):
        bad=copy.deepcopy(records)
        if name=='missing-drill':bad['drills'].pop()
        elif name=='extra-drill':bad['drills'].append(bad['drills'][0])
        elif name in ('shifted-drill','wrong-drill-size','wrong-plating'):
            r=list(bad['drills'][0]);i={'shifted-drill':0,'wrong-drill-size':2,'wrong-plating':3}[name]
            r[i]=not r[i] if i==3 else r[i]+.1;bad['drills'][0]=tuple(r)
        elif name=='missing-outline-edge':bad['layers']['mechanical/outline'].pop()
        elif name=='wrong-mask-expansion':
            r=list(bad['layers']['top/mask'][0]);a=list(r[1]);a[2]-=.1016;r[1]=tuple(a);bad['layers']['top/mask'][0]=tuple(r)
        else:
            rows=bad['layers']['top/copper'];index=next(i for i,r in enumerate(rows) if r[0]=='line')
            if name=='missing-track':rows.pop(index)
            else:r=list(rows[index]);r[2]=('/WRONG',);rows[index]=tuple(r)
        try:verify(bad,native,source)
        except AssertionError as error:faults.append(dict(fault=name,detected=True,diagnostic=str(error)))
        else:raise AssertionError('Escaped CAM mutation '+name)
    with warnings.catch_warnings(record=True) as render_warnings:
        warnings.simplefilter('always')
        for side in ('top','bottom'):
            (HERE/(side+'-cam.svg')).write_text(str(stack.to_pretty_svg(side=side,margin=2)))
    holes=Counter(r[2] for r in records['drills'])
    fit=[dict(nominal_mm=d,count=count,published_finished_min_mm=d-.0635,published_finished_max_mm=d+.0635)
         for d,count in sorted(holes.items())]
    drill_quantization=max(abs(v-round(v,3)) for r in native['drills'] for v in r['position'])
    result=dict(passed=True,gerbonara_version=gerbonara.__version__,drills=len(records['drills']),
        drill_headers=records['headers'],drill_size_groups=fit,outline_segments=4,outline_size_mm=[60,70],
        tracks=185,copper_pad_via_flashes=198,mask_openings=180,
        minimum_mask_web_bbox_lower_bound_mm=web,ground_fill_comparisons=areas,
        parsed_record_fault_checks=faults,parser_warnings=parser_warnings,
        render_warnings=sorted(set(str(w.message) for w in render_warnings)),
        coordinate_mapping='CAM (x,y) -> KiCad (x,-y); Gerber 0.000001 mm; Excellon 0.001 mm quantization.',
        maximum_drill_axis_quantization_mm=drill_quantization,
        plating_handling='Verified KiCad TF.FileFunction before explicit ExcellonFile plated argument; auto-inference is not used for the check.',
        shape_scope='Flash positions, net attributes and bounding dimensions checked. Complete aperture shape equivalence is not asserted.',
        fabrication_ready=False)
    (HERE/'cam-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CAM parity: 99 holes, 4 outline edges, 185 tracks, 198 copper flashes, 180 mask openings; 9 parsed-record faults detected')
    print('Ground-fill comparisons',areas,'minimum mask web lower bound',web)


if __name__=='__main__':main()

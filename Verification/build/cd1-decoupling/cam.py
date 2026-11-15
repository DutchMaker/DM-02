"""Export P3 preview and reuse the archived independent CAM parity checker."""
from pathlib import Path
import importlib.util
import json
import subprocess
import warnings
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
BOARD=HERE/'CD1-P3-decoupling.kicad_pcb'


def main():
    folder=HERE/'cam-preview';folder.mkdir(exist_ok=True)
    commands=[['kicad-cli','pcb','export','gerbers',str(BOARD),'--output',str(folder),'--layers',
        'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--precision','6','--check-zones'],
        ['kicad-cli','pcb','export','drill',str(BOARD),'--output',str(folder),'--format','excellon',
         '--drill-origin','absolute','--excellon-zeros-format','decimal','--excellon-units','mm','--excellon-separate-th']]
    for i,args in enumerate(commands):
        r=subprocess.run(args,capture_output=True,text=True);(HERE/f'cam-export-{i}.log').write_text(r.stdout+r.stderr)
        assert r.returncode==0,r.stderr
    spec=importlib.util.spec_from_file_location('cam_parser',HERE/'sources/cam-parser.py')
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    data=json.loads((HERE/'geometry.json').read_text())
    native=dict(drills=[dict(position=p['position'],diameter_mm=p['drill_mm'][0],plated=True) for p in data['pads']]+
                      [dict(position=v['position'],diameter_mm=v['drill_mm'],plated=True) for v in data['vias']],
                outline=data['outline'],pads=data['pads'],mask_expansion_mm=.0508)
    stack,records,regions,parse_warnings=parser.parse(folder)
    parser.verify(records,native,data)
    areas=[]
    for side,layer in [('top','F.Cu'),('bottom','B.Cu')]:
        expected=unary_union([Polygon(p['shell'],p['holes']).buffer(0) for z in data['ground_zones'] if z['layer']==layer for p in z['polygons']])
        actual=unary_union(regions[side]);delta=actual.symmetric_difference(expected).area
        assert delta<1e-6
        areas.append(dict(layer=layer,symmetric_difference_mm2=delta))
    with warnings.catch_warnings(record=True) as renderer:
        warnings.simplefilter('always')
        for side in ('top','bottom'):(HERE/f'{side}-cam.svg').write_text(str(stack.to_pretty_svg(side=side,margin=2)))
    result=dict(passed=True,board_sha256=data['board_sha256'],drills=len(native['drills']),tracks=len(data['tracks']),
        copper_pad_via_flashes=2*(len(data['pads'])+len(data['vias'])),mask_openings=180,
        ground_fill_comparisons=areas,parser_warnings=parse_warnings,
        renderer_warnings=sorted(set(str(w.message) for w in renderer)),
        checker_source='sources/cam-parser.py; previously exercised by nine record and four serialized CAM faults',
        scope='Offline Gerber/Excellon parity, including flash positions and dimensions. Supplier preview and full aperture-shape equivalence remain open.',
        fabrication_ready=False)
    (HERE/'cam-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CAM parity:',result['drills'],'drills,',result['tracks'],'tracks,',result['copper_pad_via_flashes'],'copper flashes; both ground fills match')


if __name__=='__main__':main()

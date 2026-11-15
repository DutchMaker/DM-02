"""Compare local feeds and ground connectivity; no impedance inference."""
from pathlib import Path
import importlib.util
import json
import math
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ground',HERE/'sources/ground-audit.py')
ground=importlib.util.module_from_spec(spec);spec.loader.exec_module(ground)


def copper_components(data,planes,layer):
    shapes=[planes[layer]]
    for p in data['pads']:
        if p['net']=='/GND':
            # Ground pads here are circular except DIP pin 1, a rounded-square.
            # Use an inscribed circle for every pad: connectivity is conservative.
            shapes.append(Point(p['position']).buffer(min(p['size_mm'])/2,quad_segs=64))
    shapes += [Point(v['position']).buffer(v['diameter_mm']/2,quad_segs=64) for v in data['vias'] if v['net']=='/GND']
    shapes += [LineString([t['start'],t['end']]).buffer(t['width_mm']/2,quad_segs=32) for t in data['tracks'] if t['net']=='/GND' and t['layer']==layer]
    result=unary_union(shapes)
    return list(result.geoms) if result.geom_type=='MultiPolygon' else [result]


def evaluate(data):
    planes,_=ground.plane_geometry(data)
    pads={(p['ref'],p['pin']):p for p in data['pads']}
    components={layer:copper_components(data,planes,layer) for layer in ('F.Cu','B.Cu')}
    rows=[]
    for i in range(1,4):
        cap,ic='C'+str(i),'U'+str(i)
        power,returnpad=pads[cap,'1'],pads[cap,'2']
        vcc,gnd=pads[ic,'20'],pads[ic,'10']
        assert power['net']==vcc['net']=='/5V' and returnpad['net']==gnd['net']=='/GND'
        contacts=[]
        for layer in ('F.Cu','B.Cu'):
            # Inscribed round ground copper is sufficient to connect through
            # thermal spokes; centers themselves are inside the actual holes.
            disk=Point(returnpad['position']).buffer(.8,quad_segs=64)
            overlap=planes[layer].intersection(disk).area
            common=any(c.covers(Point(returnpad['position'])) and c.covers(Point(gnd['position'])) for c in components[layer])
            contacts.append(dict(layer=layer,plane_to_cap_copper_overlap_mm2=overlap,shared_ground_component=common))
            assert overlap>1e-4 and common,(cap,layer,'ground connection')
        direct=[t for t in data['tracks'] if t['net']=='/5V' and
            (math.dist(t['start'],power['position'])<1e-6 and math.dist(t['end'],vcc['position'])<1e-6 or
             math.dist(t['end'],power['position'])<1e-6 and math.dist(t['start'],vcc['position'])<1e-6)]
        rows.append(dict(capacitor=cap,ic=ic,vcc_pin=20,ground_pin=10,
            vcc_distance_mm=math.dist(power['position'],vcc['position']),
            ground_pin_distance_mm=math.dist(returnpad['position'],gnd['position']),
            package_power_pin_distance_mm=math.dist(vcc['position'],gnd['position']),
            direct_feed_segments=direct,ground_contacts=contacts))
    coverage={}
    for t in data['tracks']:
        if t['net'] in ('/GND','/5V'):continue
        opposite={'F.Cu':'B.Cu','B.Cu':'F.Cu'}[t['layer']]
        line=LineString([t['start'],t['end']])
        row=coverage.setdefault(t['net'],dict(length_mm=0.,uncovered_mm=0.))
        row['length_mm']+=line.length
        row['uncovered_mm']+=line.difference(planes[opposite]).length
    return rows,coverage


def main():
    before=json.loads((HERE/'sources/p2-geometry.json').read_text())
    after=json.loads((HERE/'geometry.json').read_text())
    old,oldcoverage=evaluate(before);new,newcoverage=evaluate(after)
    changes=[]
    for a,b in zip(old,new):
        assert len(b['direct_feed_segments'])==1
        t=b['direct_feed_segments'][0]
        assert t['length_mm']<4 and t['width_mm']==.5
        changes.append(dict(capacitor=b['capacitor'],ic=b['ic'],before=a,after=b))
    coverage=[]
    for net in oldcoverage:
        a,b=oldcoverage[net],newcoverage[net]
        assert abs(a['length_mm']-b['length_mm'])<1e-8
        coverage.append(dict(net=net,length_mm=b['length_mm'],before_uncovered_mm=a['uncovered_mm'],
            after_uncovered_mm=b['uncovered_mm'],change_mm=b['uncovered_mm']-a['uncovered_mm']))
    # Geometric component-fit screen, explicitly not tolerance-complete insertion.
    hole_min=.8-.0635;lead_max=.51+.1
    fit=dict(part='C315C104K5R5TA',nominal_nf=100,tolerance_percent=10,rated_v=50,
        dielectric='X7R',body_max_mm=[3.81,2.54,3.14],pitch_nominal_mm=2.54,pitch_tolerance_mm=.78,
        lead_diameter_max_mm=lead_max,hole_nominal_mm=.8,published_finished_hole_min_mm=hole_min,
        diametral_clearance_at_max_lead_mm=hole_min-lead_max,
        centered_two_hole_pitch_accommodation_mm=hole_min-lead_max,
        full_unformed_pitch_tolerance_fits=(hole_min-lead_max)>=.78,
        lead_forming_required_for_tolerance_extremes=True,
        dc_bias_age_esr_esl_qualified=False,physical_fit_qualified=False)
    assert not fit['full_unformed_pitch_tolerance_fits']
    result=dict(passed=True,board_sha256=after['board_sha256'],decoupling=changes,
        signal_ground_coverage=coverage,native_containment_checks=len(after['native_zone_samples']),
        capacitor_fit_screen=fit,ground_contact_checks=12,
        package_drawing_applicability='TI mpdi096 retrieved under N0020A search is labelled NFH0020A/N20A Rev G. Exact SN74AHCT244N mechanical applicability remains unresolved; no package-fit qualification claimed.',
        scope='Native geometry and conservative filled-copper connectivity. Hole centers are filled only for topological component membership; no impedance, loop inductance or transient current extraction.',
        fabrication_ready=False)
    (HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Direct feeds',[round(r['after']['vcc_distance_mm'],6) for r in changes],
          'mm; ground contacts pass; unformed lead-pitch extremes do not fit guaranteed hole clearance')
    print('Signal uncovered change',sum(r['change_mm'] for r in coverage),'mm')


if __name__=='__main__':main()

"""Survey P2 root trace neighborhoods; do not infer full-board capacitance."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import xml.etree.ElementTree as ET
from shapely.geometry import LineString, Point

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ground_ray(center, direction, plane, width, helper):
    ray = LineString([center, [center[i]+3*direction[i] for i in range(2)]])
    intervals = []
    for part in helper.lines(ray.intersection(plane)):
        if part.is_empty:
            continue
        distances = [sum((point[i]-center[i])*direction[i] for i in range(2)) for point in part.coords]
        intervals.append((min(distances), max(distances)))
    if not intervals:
        return None
    low, high = min(intervals)
    return dict(gap_from_trace_edge_mm=low-width/2, contiguous_ground_span_mm=high-low,
                truncated_at_3mm=abs(high-3) < 1e-6)


def main():
    sources = HERE / 'sources'
    data = json.loads((sources / 'p2-geometry.json').read_text())
    assert data['board_sha256'] == sha(sources / 'CD1-P2-routed.kicad_pcb')
    spec = importlib.util.spec_from_file_location('prior_audit', sources / 'p1-audit.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    planes, _ = helper.plane_geometry(data)
    parts = json.loads((sources / 'pc-parts.json').read_text())
    input_cap = parts['devices']['SN74AHCT244N']['input_cap_pf']
    allocation = json.loads((sources / 'distribution-parts.json').read_text())['constraints']['local_trace_cap_pf']
    xml = ET.parse(sources / 'source.xml').getroot()
    reference_positions = [p['position'] for p in data['pads']]+[v['position'] for v in data['vias']]
    roots, samples = [], []
    for net in xml.findall('./nets/net'):
        name = net.attrib['name']
        if not name.startswith('/ROOT'):
            continue
        inputs = [p.attrib for p in net.findall('node') if p.attrib['pintype'] == 'input']
        outputs = [p.attrib for p in net.findall('node') if p.attrib['pintype'] in ('output', 'tri_state')]
        assert len(outputs) == 1
        segments = [t for t in data['tracks'] if t['net'] == name]
        length = sum(t['length_mm'] for t in segments)
        total_weight = eligible_weight = close_ground_weight = backed_weight = 0.
        for track in segments:
            assert abs(track['width_mm']-.25) < 1e-9
            count = max(1, math.ceil(track['length_mm']/.2))
            weight = track['length_mm']/count
            dx, dy = [b-a for a,b in zip(track['start'], track['end'])]
            normal = [-dy/track['length_mm'], dx/track['length_mm']]
            for index in range(count):
                f = (index+.5)/count
                center = [a+f*(b-a) for a,b in zip(track['start'], track['end'])]
                near_end = min(f,1-f)*track['length_mm'] < .5
                near_pad_via = min(math.dist(center, p) for p in reference_positions) < 1.5
                eligible = not near_end and not near_pad_via
                left = ground_ray(center, normal, planes[track['layer']], .25, helper)
                right = ground_ray(center, [-n for n in normal], planes[track['layer']], .25, helper)
                close = all(r is not None and .249 <= r['gap_from_trace_edge_mm'] <= .30 and
                            r['contiguous_ground_span_mm'] >= .5 for r in (left, right))
                opposite = planes[{'F.Cu':'B.Cu', 'B.Cu':'F.Cu'}[track['layer']]].covers(Point(center))
                total_weight += weight
                eligible_weight += weight*eligible
                close_ground_weight += weight*(eligible and close)
                backed_weight += weight*(eligible and close and opposite)
                samples.append(dict(net=name, track_id=track['id'], layer=track['layer'], position=center,
                                    weight_mm=weight, near_track_end=near_end, near_pad_or_via=near_pad_via,
                                    eligible=eligible, left=left, right=right,
                                    close_coplanar_ground=close, opposite_center_covered=opposite))
        assert abs(total_weight-length) < 1e-6
        roots.append(dict(net=name, length_mm=length, receiver_count=len(inputs),
                          receiver_capacitance_pf=len(inputs)*input_cap,
                          original_trace_allocation_pf=allocation,
                          original_allocated_load_pf=len(inputs)*input_cap+allocation,
                          driver_characterization_load_pf=50,
                          trace_pf_per_mm_at_5pf_allocation=allocation/length,
                          eligible_sample_weight_mm=eligible_weight,
                          close_coplanar_sample_weight_mm=close_ground_weight,
                          close_coplanar_and_opposite_sample_weight_mm=backed_weight,
                          inputs=inputs, driver=outputs[0]))
    assert len(roots) == 6
    result = dict(board_sha256=data['board_sha256'], roots=roots, samples=samples,
                  scope='Length-weighted neighborhood survey only. Neither field extraction nor integrated board capacitance.',
                  sample_max_spacing_mm=.2, excluded_track_end_distance_mm=.5,
                  excluded_pad_via_center_distance_mm=1.5, near_ground_gap_range_mm=[.249,.30],
                  required_ground_span_mm=.5, ray_length_mm=3.)
    (HERE / 'survey.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(roots)} root nets; {len(samples)} transverse survey samples')
    for root in roots:
        print(root['net'], round(root['length_mm'],3), 'mm;', round(root['close_coplanar_and_opposite_sample_weight_mm'],3), 'mm sample weight meets local neighborhood screen')


if __name__ == '__main__':
    main()

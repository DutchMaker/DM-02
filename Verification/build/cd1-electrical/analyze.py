"""CD1-P0 geometric return-plane audit and hypothetical microstrip sensitivity.

Requires shapely==2.1.2. This is a geometric screen, not a field extraction.
"""
from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import html
import json
import math
import xml.etree.ElementTree as ET
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.validation import explain_validity

HERE = Path(__file__).resolve().parent
OPPOSITE = {'F.Cu': 'B.Cu', 'B.Cu': 'F.Cu'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polygons(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from polygons(child)


def lines(geometry):
    if geometry.geom_type == 'LineString':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from lines(child)


def microstrip(width_mm, height_mm, er):
    """Schneider, Qucs eqs. 11.3 and 11.14; zero copper thickness.

    C' = 1/(Z0*v), v = c/sqrt(e_eff). F/m to pF/mm multiplies by 1e9.
    """
    assert width_mm > 0 and height_mm > 0 and er >= 1
    u = width_mm / height_mm
    ee = (er + 1) / 2 + (er - 1) / (2 * math.sqrt(1 + 10 / u))
    free_space = 376.730313668
    if u <= 1:
        z = free_space / (2 * math.pi * math.sqrt(ee)) * math.log(8 / u + u / 4)
    else:
        z = free_space / math.sqrt(ee) / (u + 2.42 - .44 / u + (1 - 1 / u) ** 6)
    velocity = 299792458 / math.sqrt(ee)
    return dict(effective_er=ee, impedance_ohm=z, capacitance_pf_per_mm=1e9 / (z * velocity),
                delay_ps_per_mm=1e9 / velocity)


def plane_geometry(data):
    planes = {}
    conversions = []
    for zone in data['ground_zones']:
        pieces = []
        for raw in zone['polygons']:
            original = Polygon(raw['shell'], raw['holes'])
            # KiCad encodes holes with zero-width bridges in its filled outlines.
            # GEOS splits these into area polygons; native containment is checked below.
            fixed = shapely.make_valid(original)
            area = unary_union(list(polygons(fixed)))
            assert area.is_valid and not area.is_empty
            assert abs(area.area - original.area) < 1e-6
            conversions.append(dict(layer=zone['layer'], original_validity=explain_validity(original),
                                    original_area_mm2=original.area, polygon_area_mm2=area.area,
                                    converted_type=fixed.geom_type))
            pieces.append(area)
        assert zone['layer'] not in planes
        planes[zone['layer']] = unary_union(pieces)
    assert set(planes) == set(OPPOSITE)
    for sample in data['native_zone_samples']:
        actual = planes[sample['layer']].covers(Point(sample['point']))
        assert actual == sample['inside'], sample
    return planes, conversions


def audit(data, planes):
    nets = defaultdict(lambda: dict(length_mm=0., uncovered_centerline_mm=0.,
                                   longest_segment_gap_mm=0., segments=0, gaps=[]))
    segments = []
    for track in data['tracks']:
        if track['net'] in ('/5V', '/GND'):
            continue
        line = LineString([track['start'], track['end']])
        assert abs(line.length - track['length_mm']) < 2e-6
        plane = planes[OPPOSITE[track['layer']]]
        missing = line.difference(plane)
        intervals = [dict(length_mm=g.length, points=[list(p) for p in g.coords])
                     for g in lines(missing) if g.length > 1e-8]
        row = nets[track['net']]
        row['length_mm'] += line.length
        row['uncovered_centerline_mm'] += missing.length
        row['longest_segment_gap_mm'] = max(row['longest_segment_gap_mm'],
                                          max([g['length_mm'] for g in intervals] + [0.]))
        row['segments'] += 1
        for gap in intervals:
            row['gaps'].append(dict(track_id=track['id'], layer=track['layer'], **gap))
        segments.append(dict(**track, uncovered_centerline_mm=missing.length, gaps=intervals))
    for row in nets.values():
        row['covered_percent'] = 100 * (1 - row['uncovered_centerline_mm'] / row['length_mm'])
    return dict(sorted(nets.items())), segments


def plot(data, planes, segments, layer):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 64 74">',
           '<rect x="20" y="20" width="60" height="70" fill="#fff" stroke="#243748" stroke-width=".2"/>']
    for poly in polygons(planes[OPPOSITE[layer]]):
        commands = []
        for ring in [poly.exterior, *poly.interiors]:
            points = list(ring.coords)
            commands.append('M' + ' L'.join(f'{x:.6f},{y:.6f}' for x, y in points) + ' Z')
        out.append(f'<path d="{" ".join(commands)}" fill="#c5ddd0" fill-rule="evenodd"/>')
    for track in segments:
        if track['layer'] != layer:
            continue
        a, b = track['start'], track['end']
        out.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" fill="none" stroke="#205e9b" stroke-width=".22"><title>{html.escape(track["net"])}</title></path>')
        for gap in track['gaps']:
            points = ' '.join(f'{x},{y}' for x, y in gap['points'])
            out.append(f'<polyline points="{points}" fill="none" stroke="#d12630" stroke-width=".5"><title>{html.escape(track["net"])}: {gap["length_mm"]:.3f} mm without opposite-layer ground fill</title></polyline>')
    for pad in data['pads']:
        x, y = pad['position']
        color = '#126b34' if pad['net'] == '/GND' else '#576777'
        out.append(f'<circle cx="{x}" cy="{y}" r=".35" fill="{color}"><title>{pad["ref"]}.{pad["pin"]}</title></circle>')
    for via in data['vias']:
        x, y = via['position']
        out.append(f'<circle cx="{x}" cy="{y}" r=".4" fill="none" stroke="#9425b7" stroke-width=".2"><title>Through via {html.escape(via["net"])}</title></circle>')
    out.append('</svg>')
    (HERE / ('front-return.svg' if layer == 'F.Cu' else 'back-return.svg')).write_text('\n'.join(out))


def main():
    global HERE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=HERE)
    HERE = parser.parse_args().directory.resolve()
    data = json.loads((HERE / 'geometry.json').read_text())
    inputs = HERE / 'inputs'
    for path, expected in data['input_hashes'].items():
        assert sha(inputs / Path(path).name) == expected
    baseline = json.loads((inputs / 'validation.json').read_text())
    assert baseline['board_sha256'] == data['board_sha256']
    straight_tracks = [t for t in data['tracks'] if t.get('kind', 'track') == 'track']
    assert len(straight_tracks) == baseline['segments']
    assert len(data['vias']) == baseline['vias']
    assert all(abs(t['width_mm'] - .25) < 1e-9 for t in straight_tracks if t['net'] not in ('/5V', '/GND'))
    xml = ET.parse(inputs / 'source.xml').getroot()
    expected = {(p.attrib['ref'], p.attrib['pin']): net.attrib['name']
                for net in xml.findall('./nets/net') for p in net.findall('node')}
    assert {(p['ref'], p['pin']): p['net'] for p in data['pads']} == expected
    planes, conversions = plane_geometry(data)
    nets, segments = audit(data, planes)
    assert len(nets) == 26
    for name, row in nets.items():
        assert abs(row['length_mm'] - baseline['net_geometry'][name]['length_mm']) < 5e-6
    pads = {(p['ref'], p['pin']): p for p in data['pads']}
    decoupling = []
    for index in range(1, 4):
        chip, cap = f'U{index}', f'C{index}'
        power, ground = pads[(chip, '20')], pads[(chip, '10')]
        cp, cg = pads[(cap, '1')], pads[(cap, '2')]
        assert power['net'] == cp['net'] == '/5V'
        assert ground['net'] == cg['net'] == '/GND'
        a = math.dist(power['position'], cp['position'])
        b = math.dist(ground['position'], cg['position'])
        decoupling.append(dict(chip=chip, capacitor=cap, vcc_pin='20', gnd_pin='10',
                               cap_to_vcc_center_distance_mm=a, cap_to_gnd_center_distance_mm=b,
                               summed_external_center_distances_mm=a+b,
                               capacitor_pin_spacing_mm=math.dist(cp['position'], cg['position'])))
    transitions = []
    ground_pads = [p for p in data['pads'] if p['net'] == '/GND' and p['through_hole']]
    for pad in data['pads']:
        if pad['net'] in ('/5V', '/GND') or not pad['through_hole']:
            continue
        layers = {t['layer'] for t in data['tracks'] if t['net'] == pad['net'] and
                  min(math.dist(pad['position'], t[k]) for k in ('start', 'end')) < 1e-5}
        if len(layers) != 2:
            continue
        nearest = min(ground_pads, key=lambda g: math.dist(g['position'], pad['position']))
        transitions.append(dict(ref=pad['ref'], pin=pad['pin'], net=pad['net'], position=pad['position'],
                                nearest_ground_barrel=f'{nearest["ref"]}.{nearest["pin"]}',
                                ground_barrel_distance_mm=math.dist(nearest['position'], pad['position'])))
    via_transitions = []
    for via in data['vias']:
        assert via['net'] != '/GND', 'Add ground vias to the nearest-reference search before using this audit'
        nearest = min(ground_pads, key=lambda g: math.dist(g['position'], via['position']))
        via_transitions.append(dict(**via, nearest_ground_barrel=f'{nearest["ref"]}.{nearest["pin"]}',
                                    ground_barrel_distance_mm=math.dist(nearest['position'], via['position'])))
    cap_budget = json.loads((inputs / 'distribution-parts.json').read_text())['constraints']['local_trace_cap_pf']
    scenarios = []
    for height in (1.53, .8, .4, .2):
        for er in (4., 4.8):
            model = microstrip(.25, height, er)
            roots = [dict(net=n, length_mm=r['length_mm'],
                          hypothetical_trace_pf=r['length_mm']*model['capacitance_pf_per_mm'],
                          allocation_pf=cap_budget,
                          allocation_remaining_pf=cap_budget-r['length_mm']*model['capacitance_pf_per_mm'])
                     for n, r in nets.items() if n.startswith('/ROOT')]
            scenarios.append(dict(height_mm=height, relative_permittivity=er, width_mm=.25,
                                  copper_thickness_mm=0, **model, root_nets=roots))
    result = dict(status='measured geometry; electrical qualification open', fabrication_ready=False,
                  board_sha256=data['board_sha256'], shapely_version=shapely.__version__,
                  geos_version=shapely.geos_version_string,
                  native_containment_checks=len(data['native_zone_samples']),
                  polygon_conversions=conversions, net_geometry=nets, signal_segments=segments,
                  signal_length_mm=sum(r['length_mm'] for r in nets.values()),
                  uncovered_centerline_mm=sum(r['uncovered_centerline_mm'] for r in nets.values()),
                  decoupling=decoupling, pad_center_layer_transitions=transitions, via_transitions=via_transitions,
                  sensitivity=scenarios,
                  scope=[
                      'Coverage intersects each routed signal centerline with the opposite-layer filled GND polygons.',
                      'Ground tracks and pads outside filled zones are omitted; pad thermal voids and signal pad antipads remain in the results.',
                      'Coverage proves neither a continuous low-inductance return to its driver nor an adequate reference corridor width.',
                      'Longest gap is per track segment; gaps spanning adjacent segments are not merged.',
                      'Layer transitions enumerate pad-center endpoints only; nearest GND barrel distance is geometric, not return impedance.',
                      'Decoupling measurements use the actual power pins (20 and 10), not grounded enable/input pins. Distances are pad-center distances, not routed loop lengths or inductance.',
                      'Microstrip results assume a uniform infinite ground plane and zero-thickness isolated straight traces. They are hypothetical sensitivities, not estimates or upper/lower bounds for this routed board.',
                      'The 1.6 mm board has no explicit manufacturer-qualified stackup. Dielectric heights and permittivities here are analyst-selected scenarios.',
                      'Copper thickness, solder mask, same-layer ground, pads, bends, barrels, connector capacitance, mutual coupling, discontinuities, loads and physical slew remain outside the microstrip model.',
                  ])
    (HERE / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    for layer in OPPOSITE:
        plot(data, planes, segments, layer)
    print(f'{len(nets)} signal nets; {result["uncovered_centerline_mm"]:.3f} / {result["signal_length_mm"]:.3f} mm without opposite-layer GND fill')
    print(f'{result["native_containment_checks"]} native point comparisons pass; {len(transitions)} pad-center layer transitions')


if __name__ == '__main__':
    main()

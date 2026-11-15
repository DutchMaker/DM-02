"""Compare persisted P1/P2 geometry and check ground-stitch intent."""
from copy import deepcopy
from pathlib import Path
import hashlib
import html
import json
import math
from shapely.geometry import Point
from plan import ground_barrels, load_helper, nearest, transitions

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stitch_contract(data, additions):
    actual = {v['id']: v for v in data['vias']}
    for addition in additions:
        assert addition['uuid'] in actual, f'Missing {addition["id"]}'
        via = actual[addition['uuid']]
        assert via['net'] == '/GND', f'Wrong net for {addition["id"]}'
        assert via['position'] == addition['position'], f'Wrong position for {addition["id"]}'
        assert abs(via['diameter_mm']-.8) < 1e-9 and abs(via['drill_mm']-.4) < 1e-9


def plot(data, planes, comparisons, additions, layer, helper):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 64 74">',
           '<rect x="20" y="20" width="60" height="70" fill="#fff" stroke="#243748" stroke-width=".2"/>']
    for poly in helper.polygons(planes[layer]):
        commands = []
        for ring in [poly.exterior, *poly.interiors]:
            commands.append('M' + ' L'.join(f'{x:.6f},{y:.6f}' for x, y in ring.coords) + ' Z')
        out.append(f'<path d="{" ".join(commands)}" fill="#c5ddd0" fill-rule="evenodd"/>')
    for track in data['tracks']:
        if track['layer'] != layer or track['net'] in ('/GND', '/5V'):
            continue
        a, b = track['start'], track['end']
        out.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="#205e9b" stroke-width=".22"><title>{html.escape(track["net"])}</title></path>')
    for pad in data['pads']:
        x, y = pad['position']
        color = '#126b34' if pad['net'] == '/GND' else '#576777'
        out.append(f'<circle cx="{x}" cy="{y}" r=".35" fill="{color}"/>')
    for row in comparisons:
        x, y = row['position']
        gx, gy = row['after']['position']
        color = '#b0440b' if not row['target_met'] else '#7338a8'
        out.append(f'<path d="M{x},{y} L{gx},{gy}" stroke="{color}" stroke-width=".25" stroke-dasharray=".4,.25"/>')
        out.append(f'<circle cx="{x}" cy="{y}" r=".6" fill="none" stroke="{color}" stroke-width=".15"><title>{row["id"]}: {row["after"]["distance_mm"]:.3f} mm</title></circle>')
    for via in additions:
        x, y = via['position']
        out.append(f'<circle cx="{x}" cy="{y}" r=".4" fill="#0c6b37" stroke="#fff" stroke-width=".12"/>')
        out.append(f'<text x="{x+.65}" y="{y-.5}" font-size="1" fill="#302336">{via["id"]}</text>')
    out.append('</svg>')
    (HERE / ('front-stitches.svg' if layer == 'F.Cu' else 'back-stitches.svg')).write_text('\n'.join(out))


def main():
    before = json.loads((HERE / 'sources/p1-geometry.json').read_text())
    after = json.loads((HERE / 'geometry.json').read_text())
    change = json.loads((HERE / 'change.json').read_text())
    plan = json.loads((HERE / 'plan.json').read_text())
    validation = json.loads((HERE / 'validation.json').read_text())
    assert after['board_sha256'] == change['candidate_sha256'] == validation['board_sha256'] == sha(HERE / 'CD1-P2-routed.kicad_pcb')
    assert before['board_sha256'] == change['baseline_sha256'] == sha(HERE / 'sources/CD1-P1-routed.kicad_pcb')
    for source, expected in after['input_hashes'].items():
        assert sha(HERE / 'inputs' / Path(source).name) == expected
    assert before['tracks'] == after['tracks'] and before['pads'] == after['pads']
    for via in before['vias']:
        assert via in after['vias']
    additions = change['added_ground_vias']
    stitch_contract(after, additions)
    assert len(after['vias']) == len(before['vias'])+len(additions) == 9
    helper = load_helper()
    planes_before, _ = helper.plane_geometry(before)
    planes_after, conversions = helper.plane_geometry(after)
    net_before, _ = helper.audit(before, planes_before)
    net_after, _ = helper.audit(after, planes_after)
    plane_changes = []
    for layer in planes_before:
        difference = planes_before[layer].symmetric_difference(planes_after[layer]).area
        plane_changes.append(dict(layer=layer, symmetric_difference_mm2=difference))
        assert difference < 1e-6
    assert net_before == net_after
    assert transitions(before) == transitions(after)
    comparisons = []
    for transition in transitions(after):
        old = nearest(transition['position'], ground_barrels(before))
        new = nearest(transition['position'], ground_barrels(after))
        assert new['distance_mm'] < old['distance_mm']
        comparisons.append(dict(**transition, before=old, after=new,
                                target_met=new['distance_mm'] <= plan['target_mm']))
    contacts = []
    for addition in additions:
        point = Point(addition['position'])
        for layer, plane in planes_after.items():
            assert plane.covers(point)
            margin = plane.boundary.distance(point)
            assert margin >= plan['copper_disk_radius_mm']-1e-6
            component = next(p for p in helper.polygons(plane) if p.covers(point))
            contacts.append(dict(stitch=addition['id'], layer=layer, center_to_fill_boundary_mm=margin,
                                 via_radius_mm=.4, connected_fill_component_area_mm2=component.area))
    faults = []
    for addition in additions:
        mutant = deepcopy(after)
        mutant['vias'] = [v for v in mutant['vias'] if v['id'] != addition['uuid']]
        try:
            stitch_contract(mutant, additions)
        except AssertionError as error:
            regression = max(nearest(t['position'], ground_barrels(mutant))['distance_mm']-
                             nearest(t['position'], ground_barrels(after))['distance_mm'] for t in transitions(after))
            assert regression > 0
            faults.append(dict(fault=f'missing-{addition["id"]}', detected=True,
                               greatest_reference_distance_increase_mm=regression, diagnostic=str(error)))
        else:
            raise AssertionError('Missing via escaped exported-geometry contract')
    for mode in ('wrong-net', 'shifted', 'small-annulus'):
        mutant = deepcopy(after)
        target = next(v for v in mutant['vias'] if v['id'] == additions[0]['uuid'])
        if mode == 'wrong-net':
            target['net'] = '/5V'
        elif mode == 'shifted':
            target['position'][0] += .1
        else:
            target['diameter_mm'] = .5
        try:
            stitch_contract(mutant, additions)
        except AssertionError:
            faults.append(dict(fault=mode, detected=True))
        else:
            raise AssertionError(f'{mode} escaped exported-geometry contract')
    result = dict(status='limited: geometric improvement verified; one 2 mm target remains unmet',
                  passed_geometric_checks=True, fabrication_ready=False, board_sha256=after['board_sha256'],
                  baseline_sha256=before['board_sha256'], target_mm=plan['target_mm'],
                  targets_met=sum(r['target_met'] for r in comparisons), transitions=comparisons,
                  worst_before_mm=max(r['before']['distance_mm'] for r in comparisons),
                  worst_after_mm=max(r['after']['distance_mm'] for r in comparisons),
                  signal_copper_unchanged=True, pads_unchanged=True, signal_gap_geometry_unchanged=True,
                  plane_changes=plane_changes, ground_via_contacts=contacts, new_ground_vias=len(additions),
                  native_containment_checks=len(before['native_zone_samples'])+len(after['native_zone_samples']),
                  polygon_conversions=conversions, geometry_faults=faults,
                  scope=[
                      'Distances are straight-line center-to-center distances to a ground-connected through barrel.',
                      'The 2 mm threshold is an analyst-selected layout target, not a datasheet requirement or an SI bound.',
                      'The 0.05 mm placement grid and 0.45 mm dual-ground disk are a bounded search, not a proof of global optimality.',
                      'Ground-fill coverage proves geometric contact around each new via on both layers, not frequency-dependent current return or impedance.',
                      'Ground projection and signal routing remain unchanged. Vertical ground connectivity is added at eight locations.',
                      'Added ground barrels change the electromagnetic environment. Loading, mutual coupling, inductance, slew, skew and EMI remain unqualified.',
                      'The eight 0.4 mm drills and 0.2 mm annuli need fabrication review with the chosen supplier.',
                      'Stackup, power/decoupling, exact capacitors/connectors, mounting, oscillator and reset remain open.'
                  ])
    assert result['targets_met'] == 7
    (HERE / 'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    for layer in planes_after:
        plot(after, planes_after, comparisons, additions, layer, helper)
    print(f'P2: {len(comparisons)} transitions improve, {result["targets_met"]}/8 meet 2 mm; worst {result["worst_before_mm"]:.3f} -> {result["worst_after_mm"]:.3f} mm')
    print(f'{len(contacts)} dual-layer contacts verified; {len(faults)} geometry mutations detected; original signal/ground-fill geometry unchanged')


if __name__ == '__main__':
    main()

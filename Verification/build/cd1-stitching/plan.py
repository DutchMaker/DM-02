"""Place a nearby ground via at each P1 signal layer transition.

The 2 mm target is a geometric experiment criterion, not an SI limit.
Candidates use a 0.05 mm grid and a 0.45 mm ground-copper disk on both sides.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
from shapely.geometry import Point

HERE = Path(__file__).resolve().parent
SOURCES = HERE / 'sources'
TARGET_MM = 2.
VIA_RADIUS_MM = .4
COPPER_DISK_MM = .45
SEARCH_RADIUS_MM = 3.
GRID_MM = .05


def load_helper():
    spec = importlib.util.spec_from_file_location('p1_audit', SOURCES / 'analyze.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transitions(data):
    rows = []
    for pad in data['pads']:
        if pad['net'] in ('/5V', '/GND') or not pad['through_hole']:
            continue
        layers = {t['layer'] for t in data['tracks'] if t['net'] == pad['net'] and
                  min(math.dist(pad['position'], t[k]) for k in ('start', 'end')) < 1e-5}
        if len(layers) == 2:
            rows.append(dict(id=f'{pad["ref"]}.{pad["pin"]}', net=pad['net'], position=pad['position']))
    for via in data['vias']:
        if via['net'] not in ('/5V', '/GND'):
            rows.append(dict(id=via['id'], net=via['net'], position=via['position']))
    return sorted(rows, key=lambda row: row['id'])


def ground_barrels(data):
    pads = [dict(id=f'{p["ref"]}.{p["pin"]}', position=p['position']) for p in data['pads']
            if p['net'] == '/GND' and p['through_hole']]
    return pads + [dict(id=v['id'], position=v['position']) for v in data['vias'] if v['net'] == '/GND']


def nearest(position, barrels):
    item = min(barrels, key=lambda b: math.dist(position, b['position']))
    return dict(id=item['id'], position=item['position'], distance_mm=math.dist(position, item['position']))


def candidate(position, common, selected):
    # Search a fixed board-coordinate grid, then pick the shortest distance.
    x, y = position
    candidates = []
    for ix in range(math.ceil((x-SEARCH_RADIUS_MM)/GRID_MM), math.floor((x+SEARCH_RADIUS_MM)/GRID_MM)+1):
        for iy in range(math.ceil((y-SEARCH_RADIUS_MM)/GRID_MM), math.floor((y+SEARCH_RADIUS_MM)/GRID_MM)+1):
            point = [round(ix*GRID_MM, 6), round(iy*GRID_MM, 6)]
            distance = math.dist(position, point)
            if distance > SEARCH_RADIUS_MM:
                continue
            candidates.append((distance, point))
    for distance, point in sorted(candidates):
        p = Point(point)
        if not common.covers(p) or common.boundary.distance(p) < COPPER_DISK_MM:
            continue
        if any(math.dist(point, row['position']) < 2*VIA_RADIUS_MM+.25 for row in selected):
            continue
        return dict(position=point, distance_mm=distance, dual_ground_edge_distance_mm=common.boundary.distance(p))
    raise AssertionError(f'No dual-ground placement within {SEARCH_RADIUS_MM} mm of {position}')


def main():
    helper = load_helper()
    data = json.loads((SOURCES / 'p1-geometry.json').read_text())
    planes, conversions = helper.plane_geometry(data)
    common = planes['F.Cu'].intersection(planes['B.Cu'])
    barrels = ground_barrels(data)
    selected, rows = [], []
    for transition in transitions(data):
        before = nearest(transition['position'], barrels)
        available = nearest(transition['position'], barrels+selected)
        if available['distance_mm'] <= TARGET_MM:
            placement = None
        else:
            placement = candidate(transition['position'], common, selected)
            selected.append(dict(id=f'G{len(selected)+1}', position=placement['position']))
            available = nearest(transition['position'], barrels+selected)
        rows.append(dict(**transition, before=before, proposed=available, placement=placement,
                         target_met=available['distance_mm'] <= TARGET_MM))
    result = dict(baseline_sha256=data['board_sha256'], target_mm=TARGET_MM,
                  criterion='Analyst-selected geometric target; no impedance, timing or capacitance acceptance implied.',
                  via_diameter_mm=2*VIA_RADIUS_MM, via_drill_mm=.4, grid_mm=GRID_MM,
                  copper_disk_radius_mm=COPPER_DISK_MM, search_radius_mm=SEARCH_RADIUS_MM,
                  transitions=rows, new_ground_vias=selected,
                  all_targets_met=all(r['target_met'] for r in rows),
                  native_containment_checks=len(data['native_zone_samples']), polygon_conversions=conversions)
    (HERE / 'plan.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(rows)} signal transitions; {len(selected)} ground vias; all 2 mm targets met: {result["all_targets_met"]}')
    for row in rows:
        print(row['id'], f'{row["before"]["distance_mm"]:.3f} -> {row["proposed"]["distance_mm"]:.3f} mm')


if __name__ == '__main__':
    main()

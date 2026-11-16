"""Reproducible package-area and crossing-net screen for a mechanical proposal.

This is not a placement, routing, socket-fit or electrical qualification result.
"""
from collections import defaultdict
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'Verification'))
from dm02.common import digest, write_json
from dm02.sexpr import parse

BUILD = ROOT/'Verification/build'
ARCHIVE = BUILD/'cp1-hct273'
GROUPS = {
    'control': ['CW1', 'SQ1'],
    'compute': ['AL1', 'RG1'],
    'counters': ['PC1', 'SP1'],
    'memory': ['MA1', 'ME1'],
    'active-backplane': ['C1', 'DT1', 'BF1', 'BP1'],
}


def main():
    lock = json.loads((ROOT/'Verification/targets/cp1/lock.json').read_text())
    if lock['revision'] != 'CP1-R2':
        raise ValueError('This proposal starts from R2')
    inputs = {}
    def checked(path):
        name = str(path.relative_to(BUILD))
        actual = digest(path)
        if actual != lock['artifacts'][name]:
            raise ValueError('Changed R2 input: '+name)
        inputs[name] = actual
        return path

    review = json.loads(checked(ARCHIVE/'physical-review.json').read_text())
    footprint_cache = {}
    def dimensions(name):
        if name not in footprint_cache:
            library, part = name.split(':')
            path = ARCHIVE/'footprints'/(library+'.pretty')/(part+'.kicad_mod')
            checked(path)
            if digest(path) != review['footprints'][name]['sha256']:
                raise ValueError('Footprint differs from accepted physical review: '+name)
            points = []
            for item in parse(path.read_text()):
                if isinstance(item, list) and item and item[0] in ('fp_line','fp_rect') and ['layer','F.CrtYd'] in item:
                    points.extend((float(p[1]),float(p[2])) for p in item
                                  if isinstance(p,list) and p and p[0] in ('start','end'))
            if not points:
                raise ValueError('No supported front courtyard: '+name)
            footprint_cache[name] = (max(p[0] for p in points)-min(p[0] for p in points),
                                     max(p[1] for p in points)-min(p[1] for p in points))
        return footprint_cache[name]

    rows = []
    net_groups = defaultdict(set)
    mapping = json.loads(checked(ARCHIVE/'candidate/Circuits/KiCad/Compact/candidates/connections.json').read_text())
    board_group = {board: group for group, boards in GROUPS.items() for board in boards}
    for connection in mapping:
        for net in connection['signals']:
            if net and net not in ('5V', 'GND'):
                net_groups[net].add(board_group[connection['board']])
    # External IO/operator ports are not module rows in connections.json.
    bp = ET.parse(checked(ARCHIVE/'native/BP1/BP1.xml')).getroot()
    for net in bp.findall('./nets/net'):
        name = net.get('name').removeprefix('/')
        if name not in ('5V','GND') and any(n.get('ref') in ('J901','J902','J903','J904') for n in net.findall('node')):
            net_groups[name].add('external')

    for group, boards in GROUPS.items():
        packages = []; excluded = []
        for board in boards:
            tree = ET.parse(checked(ARCHIVE/f'native/{board}/{board}.xml')).getroot()
            for part in tree.findall('./components/comp'):
                ref = part.get('ref'); footprint = part.findtext('footprint') or ''
                is_dip = footprint.startswith('Package_DIP:')
                if not is_dip and not ref.startswith('C'):
                    excluded.append(dict(board=board,ref=ref,value=part.findtext('value'),footprint=footprint))
                    continue
                width, height = dimensions(footprint)
                # 1 mm per side is an explicit planning allowance, not a socket dimension.
                margin = 2 if is_dip else 0
                packages.append(dict(board=board,ref=ref,value=part.findtext('value'),footprint=footprint,
                    courtyard_width_mm=width,courtyard_height_mm=height,
                    planning_width_mm=width+margin,planning_height_mm=height+margin,
                    area_mm2=(width+margin)*(height+margin),kind='DIP' if is_dip else 'capacitor'))
        area = sum(p['area_mm2'] for p in packages)
        crossing = sorted(n for n, groups in net_groups.items() if group in groups and len(groups)>1)
        rows.append(dict(group=group,logical_boards=boards,dip_count=sum(p['kind']=='DIP' for p in packages),
            capacitor_count=sum(p['kind']=='capacitor' for p in packages),planning_area_mm2=round(area,2),
            crossing_signal_count=len(crossing),crossing_signals=crossing,packages=packages,
            excluded_from_area=excluded,
            card_screens=[dict(board_mm=[w,h],planning_zone_mm=[w-10,h-35],
                occupancy_fraction=round(area/((w-10)*(h-35)),4)) for w,h in ((200,160),(250,160),(250,200))]
                if group!='active-backplane' else []))
    if sum(r['dip_count'] for r in rows) != 192:
        raise ValueError('Partition omitted or duplicated baseline DIP packages')
    result = dict(revision='CP1-MP1-proposal',design_revision='CP1-R2',owner_approved=False,
        physical_qualification=False,source_hashes=inputs,script_sha256=digest(Path(__file__)),groups=rows,
        proposal=dict(cpu_cards=4,cpu_card_mm=[250,200],active_backplane_mm=[270,270],
            card_positions=8,cpu_positions=4,peripheral_positions=4,
            first_peripheral='text',initial_spare_peripheral_positions=3,
            card_pitch_mm=30,provisional_assembly_envelope_mm=[270,270,230],
            layer_count=4,nominal_board_thickness_mm=1.6,
            planning_keepouts_mm=dict(side_rail_each=5,top_access=10,bottom_connector=25),
            power_entry='Single external regulated 5 V input at an accessible backplane edge through a keyed/polarised through-hole connector; rating/protection follow the power budget.',
            service_access='Remove one vertical card to access its sockets; test/control connectors face an accessible edge; qualify powered probing separately.',
            cost_constraint='No owner price ceiling supplied. Compare vendor quotes before fabrication; this screen contains no price estimate.',
            connector_direction='Vertical removable cards into a horizontal active backplane; keyed by slot role.',
            connector_provision='Evaluate two 96-contact through-hole connectors per CPU card and one per peripheral; exact parts/pins unselected.'),
        scope='Area sums and topological crossing counts only, not floorplanning, socket fit, route lengths, power or timing.',
        limitations=[
            'DIP courtyard plus 1 mm each side is a planning allowance, not the actual socket outline or extraction clearance.',
            'Capacitor area is counted but adjacency to supply pins is not placed or qualified.',
            'Legacy connectors, oscillator, resistors and other excluded parts are listed; production connector/mounting/test-access areas require placement.',
            'New IO bridge, text card, qualified reset/power circuitry and future peripheral packages are not included in the 192-DIP baseline.',
            'Crossing counts exclude supply/ground and count each signal once; they are not connector contact counts or a fanout/capacitance budget.',
            'The 230 mm height and 30 mm pitch need chosen connector/socket/rail and actual component clearance checks.',
            'The envelope excludes enclosure walls, external cables and extraction space. Powered card insertion/removal is not supported.',
            'Four layers are a proposed routing/return-path choice; vendor stackup, DFM and costs remain unquoted.',
            'Keeping MA1 and ME1 together avoids an address connector, but a larger card does not itself qualify same-cycle memory timing.',
        ])
    write_json(HERE/'screen.json',result)
    for row in rows:
        print(row['group'],row['dip_count'],'DIP;',row['planning_area_mm2'],'mm2;',row['crossing_signal_count'],'crossing signals')
    print('Proposal only; 192 baseline DIP packages accounted for.')


if __name__ == '__main__':
    main()

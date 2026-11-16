"""Native-linked connector planning; no fabricated PCB or electrical acceptance."""
from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from .common import ROOT, VROOT, BUILD, digest, write_json

MECHANICAL = VROOT/'mechanical-contract.json'
LOCK = VROOT/'targets/cp1/lock.json'
ARCHIVE = 'cp1-hct273/'
GROUPS = {'control': ['CW1','SQ1'], 'compute': ['AL1','RG1'],
          'counters': ['PC1','SP1'], 'memory': ['MA1','ME1'],
          'active-backplane': ['C1','DT1','BF1','BP1']}
CONTACTS = [f'{row}{n}' for n in range(1,33) for row in 'abc']
SIGNAL_PINS = [f'{row}{n}' for n in range(3,31) for row in 'ac']


def require(value, message):
    if not value:
        raise ValueError(message)


def mechanical():
    contract = json.loads(MECHANICAL.read_text())
    require(contract['revision']=='CP1-MC1' and contract['owner_approved'] is True
            and contract['physical_qualification'] is False, 'Mechanical selection is not physical acceptance')
    require(contract['partition']==GROUPS, 'Selected partition changed')
    require(contract['cpu_card_mm']==[250,200] and contract['backplane_mm']==[270,270]
            and contract['card_pitch_mm']==30 and contract['layers']==4, 'Selected geometry changed')
    require(contract['positions']==list(GROUPS)[:4]+['text','expansion-1','expansion-2','expansion-3'],
            'Selected slot roles changed')
    for name, expected in contract['evidence'].items():
        require(digest(ROOT/name)==expected, 'Changed mechanical proposal evidence: '+name)
    return contract


def native_boundary():
    """Resolve each old connector pin through its actual BP1 net and local net.

    A local /DATA0 and /BRANCH0_0 must not merge because their source boards
    share a physical card. Only the locked BP1 assembly creates net aliases.
    """
    lock = json.loads(LOCK.read_text())
    require(lock['revision']=='CP1-R2', 'Review connector mapping for new baseline')
    hashes = {}
    def checked(name):
        path = BUILD/name
        require(digest(path)==lock['artifacts'][name], 'Changed native source: '+name)
        hashes[name] = lock['artifacts'][name]
        return path
    nodes, nets = {}, {}
    for board in [b for boards in GROUPS.values() for b in boards]:
        nodes[board], nets[board] = {}, {}
        tree = ET.parse(checked(ARCHIVE+f'native/{board}/{board}.xml')).getroot()
        for net in tree.findall('./nets/net'):
            name = net.get('name').removeprefix('/')
            pins = [(n.get('ref'), n.get('pin')) for n in net.findall('node')]
            nets[board][name] = pins
            for pin in pins:
                require(pin not in nodes[board], 'Duplicate native pin')
                nodes[board][pin] = name
    rows = json.loads(checked(ARCHIVE+'candidate/Circuits/KiCad/Compact/candidates/connections.json').read_text())
    group_of = {b:g for g,boards in GROUPS.items() for b in boards}
    by_net = defaultdict(list)
    local_alias = {}
    mapped_bp = set()
    for row in rows:
        board = row['board']
        for number, expected in enumerate(row['signals'],1):
            if expected is None:
                continue
            bp_pin = row['backplane'], str(number)
            require(bp_pin not in mapped_bp, 'Duplicate assembly pin')
            mapped_bp.add(bp_pin)
            require(nodes['BP1'].get(bp_pin)==expected, 'Assembly map/native BP1 disagreement')
            local = nodes[board][row['connector'],str(number)]
            key = board, local
            require(local_alias.get(key,expected)==expected, 'Local net aliases different assembly nets')
            local_alias[key] = expected
            by_net[expected].append(dict(group=group_of[board],board=board,
                connector=row['connector'],pin=str(number),local_net=local,
                component_pins=[f'{ref}.{pin}' for ref,pin in nets[board][local] if not ref.startswith('J')]))
    for (ref,pin), net in nodes['BP1'].items():
        if ref in ('J901','J902','J903','J904'):
            by_net[net].append(dict(group='external',board='BP1',connector=ref,pin=pin,local_net=net,component_pins=[]))
        elif not net.startswith('unconnected-'):
            require((ref,pin) in mapped_bp, 'Unmapped native BP1 endpoint')
    crossings, internal = {}, {}
    for group in list(GROUPS)[:4]:
        crossings[group] = sorted(n for n,eps in by_net.items() if n not in ('5V','GND')
            and any(e['group']==group for e in eps) and any(e['group']!=group for e in eps))
        internal[group] = sorted(n for n,eps in by_net.items() if n not in ('5V','GND')
            and {e['group'] for e in eps}=={group})
    # Live MAR taps come from actual storage outputs, distinct from IO_ADDR.
    live_address = {}
    for bit in range(16):
        local = f'ADDRESS{bit}'
        require(local in nets['ME1'], 'Missing live address')
        live_address[local] = [f'{r}.{p}' for r,p in nets['ME1'][local] if not r.startswith('J')]
    return dict(source_hashes=hashes, nets=dict(by_net), crossings=crossings,
                internal=internal, live_address=live_address)


def natural(name):
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)',name)]


def din(ref, signals):
    require(len(signals)<=56, 'Connector signal capacity exceeded')
    assignment = dict(zip(SIGNAL_PINS, signals))
    pins = []
    for pin in CONTACTS:
        if pin.startswith('b'):
            kind, net = 'ground','GND'
        elif pin in ('a1','c1','a32','c32'):
            kind, net = 'power','5V'
        elif pin in assignment:
            kind, net = 'signal',assignment[pin]
        else:
            kind, net = 'nc',None
        pins.append(dict(pin=pin,kind=kind,net=net))
    return dict(ref=ref,pins=pins)


def service(ref, signals, positions):
    pins = []
    for index in range(positions):
        pins.append(dict(pin=str(index*2+1), kind='signal' if index<len(signals) else 'nc',
                         net=signals[index] if index<len(signals) else None))
        pins.append(dict(pin=str(index*2+2),kind='ground',net='GND'))
    return dict(ref=ref,rows=2,positions=positions,pitch_mm=2.54,pins=pins)


def generate(boundary=None):
    contract = mechanical()
    boundary = native_boundary() if boundary is None else boundary
    # Full live address supports both the read bridge and debugger observation.
    additions = [f'LIVE_ADDRESS{i}' for i in range(16)]+['IO_READ_VALID']
    cards = []
    for index,group in enumerate(list(GROUPS)[:4]):
        signals = sorted(boundary['crossings'][group],key=natural)
        if group=='memory':
            signals += additions
        cards.append(dict(role=group,position=index+1,baseline_signals=len(boundary['crossings'][group]),
            added_signals=len(additions) if group=='memory' else 0,
            connectors=[din('P1',signals[:56]),din('P2',signals[56:])]))
    # Each slot is independently buffered. Private returns may never be tied.
    logical = ([f'W_ADDR{i}' for i in range(8)]+[f'W_DATA{i}' for i in range(8)]+
               [f'R_ADDR{i}' for i in range(8)]+['W_STROBE','R_VALID','RESET_n']+
               [f'R_DATA{i}' for i in range(8)]+['PRESENT_n'])
    peripherals = [dict(role=role,position=i+5,
        connector=din('P1',[f'SLOT{i+5}_{n}' for n in logical]))
        for i,role in enumerate(contract['positions'][4:])]
    observed = ([f'DATA{i}' for i in range(8)]+[f'PH{i}' for i in range(4)]+
                ['ACTIVE','READY','HALTED','FETCH0','FETCH1','EXECUTING','PC_ADDRESS_n','ALU_ENABLE'])
    controls = ['RESET_REQUEST_n','RUN_REQUEST','HALT_REQUEST','RESUME_REQUEST','STEP_REQUEST']
    require(all(n in boundary['nets'] for n in observed+['RESET_n']), 'Missing service observation source')
    svc = [service('SVC_A',['OBS_'+n for n in observed],20),
           service('SVC_B',[f'OBS_ADDRESS{i}' for i in range(16)]+['OBS_RESET_n']+
                   ['DBG_'+n for n in controls],25)]
    return dict(revision='CP1-CN1-draft',mechanical_revision=contract['revision'],baseline_revision='CP1-R2',
        physical_qualification=False,manufacturing_release=False,
        status='provisional pin assignment; footprint, circuit and electrical qualification pending',
        source_hashes=boundary['source_hashes'],mechanical_sha256=digest(MECHANICAL),
        cpu_cards=cards,peripheral_cards=peripherals,service=svc,
        service_sources={**{'OBS_'+n:dict(direction='computer-to-debugger',native_bp_net=n,
            implementation='new buffered observation branch required') for n in observed+['RESET_n']},
            **{f'OBS_ADDRESS{i}':dict(direction='computer-to-debugger',extension_net=f'LIVE_ADDRESS{i}',
                implementation='new buffered observation branch required') for i in range(16)},
            **{'DBG_'+n:dict(direction='debugger-to-computer',
                implementation='new qualified command conditioner required') for n in controls}},
        native_boundary=boundary,
        layout=dict(coordinates='Planning datums in mm, viewed from above backplane; not drill coordinates.',
            card_planes_y_mm=[30+30*i for i in range(8)],
            card_x_extent_mm=[10,260],cpu_connector_centres_x_mm=[65,185],
            peripheral_connector_centre_x_mm=65,
            connector_max_planning_body_length_mm=100,
            card_bottom_strip_mm=25),
        extension_sources={**{f'LIVE_ADDRESS{i}':dict(board='ME1',local_net=f'ADDRESS{i}',
            component_pins=boundary['live_address'][f'ADDRESS{i}']) for i in range(16)},
            'IO_READ_VALID':dict(board='memory',implementation='pending',
                condition='valid supply/reset AND ADDRESS[15:8]==0xFF AND MEM_n==0 AND LOAD_n10==1; qualify hazards and latency')})


def validate(plan, boundary=None):
    boundary = native_boundary() if boundary is None else boundary
    require(plan['physical_qualification'] is False and plan['manufacturing_release'] is False,
            'Pin planning cannot release hardware')
    require(plan['source_hashes']==boundary['source_hashes'], 'Source provenance differs')
    require(plan['mechanical_sha256']==digest(MECHANICAL), 'Mechanical contract changed')
    cards = plan['cpu_cards']
    require([c['role'] for c in cards]==list(GROUPS)[:4], 'Missing or repeated CPU role')
    checked = 0
    def check_din(connector):
        nonlocal checked
        pins = connector['pins']
        require(Counter(p['pin'] for p in pins)==Counter(CONTACTS), 'Duplicate/missing DIN contact')
        for p in pins:
            pin,kind,net = p['pin'],p['kind'],p['net']
            if pin.startswith('b'):
                require((kind,net)==('ground','GND'), 'Ground contact collision')
            elif pin in ('a1','c1','a32','c32'):
                require((kind,net)==('power','5V'), 'Power contact collision')
            elif pin not in SIGNAL_PINS:
                require((kind,net)==('nc',None), 'Coding reserve occupied')
            else:
                require((kind=='nc' and net is None) or
                        (kind=='signal' and isinstance(net,str) and net not in ('5V','GND')), 'Invalid signal contact')
        checked += len(pins)
        return [p['net'] for p in pins if p['kind']=='signal']
    for i,card in enumerate(cards):
        require(card['position']==i+1 and [c['ref'] for c in card['connectors']]==['P1','P2'], 'CPU connector identity changed')
        actual = [n for c in card['connectors'] for n in check_din(c)]
        wanted = list(boundary['crossings'][card['role']])
        if card['role']=='memory':
            wanted += [f'LIVE_ADDRESS{i}' for i in range(16)]+['IO_READ_VALID']
        require(Counter(actual)==Counter(wanted), 'Missing/aliased/duplicate crossing signal: '+card['role'])
    require([c['role'] for c in plan['peripheral_cards']]==mechanical()['positions'][4:], 'Peripheral roles changed')
    reference = generate(boundary)
    for i,(card,expected) in enumerate(zip(plan['peripheral_cards'],reference['peripheral_cards']),5):
        actual = check_din(card['connector'])
        require(card['position']==i, 'Peripheral slot identity changed')
        require(card['connector']==expected['connector'], 'Private slot return or peripheral contact map changed')
        require(all(n.startswith(f'SLOT{i}_') for n in actual), 'Cross-slot signal short')
    for actual,expected in zip(plan['service'],reference['service']):
        require(actual==expected, 'Service contact/direction bank changed')
        checked += len(actual['pins'])
    require(len(plan['service'])==2, 'Missing service connector')
    require(plan['extension_sources']==reference['extension_sources'], 'Live/read extension source changed')
    require(plan['service_sources']==reference['service_sources'], 'Service source/direction changed')
    require(plan['layout']==reference['layout'], 'Planning geometry changed')
    return dict(passed=True,contacts_checked=checked,
        baseline_crossings={c['role']:len(boundary['crossings'][c['role']]) for c in cards},
        memory_total_signals=sum(p['kind']=='signal' for c in cards[-1]['connectors'] for p in c['pins']),
        scope='Contact allocation and native connectivity boundary only',
        physical_qualification=False)


def render(plan):
    lines = ['# CP1-CN1 draft contact tables', '',
        'Generated by `python3 -m dm02.connector_plan --output <new-directory>`. Pin names are manufacturer contact identities; mating faces mirror visually. Footprint orientation remains unqualified.', '',
        '[Contract and electrical semantics](../../Connector-plan.md)', '']
    for card in plan['cpu_cards']+plan['peripheral_cards']:
        lines += [f'## Position {card["position"]}: {card["role"]}', '']
        for conn in card.get('connectors',[card.get('connector')]):
            lines += [f'### {conn["ref"]}', '', '| Position | a | b | c |', '| --- | --- | --- | --- |']
            pins = {p['pin']:p['net'] or 'NC' for p in conn['pins']}
            lines += [f'| {n} | {pins[f"a{n}"]} | {pins[f"b{n}"]} | {pins[f"c{n}"]} |' for n in range(1,33)]
            lines += ['']
    for conn in plan['service']:
        lines += [f'## {conn["ref"]}', '', '| Pin | Signal | Pin | Return |', '| --- | --- | --- | --- |']
        for a,b in zip(conn['pins'][::2],conn['pins'][1::2]):
            lines.append(f'| {a["pin"]} | {a["net"] or "NC"} | {b["pin"]} | GND |')
        lines += ['']
    return '\n'.join(lines)


def evaluate(output=None):
    out = BUILD/'cp1-connectors' if output is None else Path(output)
    require(not (out/'manifest.json').exists(), 'Preserve published study; choose a new --output directory')
    plan = generate()
    check = validate(plan)
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'pin-plan.json',plan)
    write_json(out/'check.json',check)
    (out/'pin-tables.md').write_text(render(plan))
    return plan,check


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='New output directory; existing published studies cannot be overwritten')
    args = parser.parse_args()
    _,check = evaluate(args.output)
    print(json.dumps(check,indent=2))

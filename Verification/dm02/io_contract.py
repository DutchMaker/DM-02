"""CP1 IO protocol reference model and audit of the frozen native boundary.

This is not a model of implemented peripheral circuitry or physical timing.
"""
from copy import deepcopy
import json
import xml.etree.ElementTree as ET
from .common import BUILD, VROOT, digest

PATH = VROOT/'io-interface.json'
LOCK = VROOT/'targets/cp1/lock.json'
NATIVE = 'cp1-hct273/native/{board}/{board}.xml'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(contract):
    require(contract['schema_version'] == 1, 'Unsupported IO contract schema')
    require(contract['physical_qualification'] is False, 'Logical IO contract cannot qualify hardware')
    require(contract['baseline_revision'] == 'CP1-R2' and contract['operating_contract'] == 'CP1-OC1',
            'IO contract needs review against the selected baseline/envelope')
    addressing = contract['addressing']
    require((addressing['io_base'], addressing['io_size']) == (0xff00, 256), 'Wrong IO page')
    expected = {
        'text_data': (0, 'write', 'text'),
        'graphics_data': (1, 'write', 'graphics-reserved'),
        'graphics_command': (2, 'write', 'graphics-reserved'),
        'text_status': (3, 'read', 'text'),
        'text_control': (4, 'write', 'text'),
    }
    registers = addressing['registers']
    require(len(registers) == len(expected), 'Missing or duplicate IO register')
    observed = {}
    for register in registers:
        offset = register['offset']
        require(type(offset) is int and 0 <= offset < 256, 'Invalid register offset')
        require(register['name'] not in observed, 'Duplicate IO register name')
        observed[register['name']] = (offset, register['access'], register['owner'])
    require(observed == expected, 'IO map changes require an ABI revision and affected verification')
    require(addressing['reserved_offsets'] == [5, 15] and addressing['expansion_offsets'] == [16, 255],
            'Reserved and expansion address allocation changed')
    require(addressing['unmapped_read_value'] == 0 and addressing['unmapped_write'] == 'ignore',
            'Unallocated IO must have defined inactive behaviour')
    text = contract['text']
    require((text['ready_mask'], text['overrun_mask'], text['present_mask'], text['control_w1c_mask'],
             text['mailbox_capacity_bytes']) == (1, 2, 128, 2, 1), 'Unsupported text protocol revision')
    return contract


def load(path=PATH):
    return validate(json.loads(path.read_text()))


class RegisterFixture:
    """A second logical endpoint for address-isolation tests, not a hardware card."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = 0

    def read(self):
        return self.value

    def write(self, value):
        self.value = value


class Interface:
    """Serialized transaction semantics; no pin delay, CDC or baud-rate model."""
    def __init__(self, contract, text_present=True):
        self.contract = deepcopy(validate(contract))
        self.text_present = text_present
        self.endpoints = {}
        addressing = contract['addressing']
        self.base = addressing['io_base']
        self.registers = {r['name']: self.base+r['offset'] for r in addressing['registers']}
        self.assert_reset()

    def _address(self, address):
        require(type(address) is int and 0 <= address <= 0xffff, 'Address must be a 16-bit integer')
        return address >= self.base

    def attach(self, address, endpoint):
        self._address(address)
        low, high = self.contract['addressing']['expansion_offsets']
        require(self.base+low <= address <= self.base+high, 'Endpoint overlaps reserved IO')
        require(address not in self.endpoints, 'Duplicate endpoint address owner')
        require(self.reset_asserted, 'Attach endpoints only while reset; model does not support hot plug')
        endpoint.reset()
        self.endpoints[address] = endpoint

    def assert_reset(self):
        self.reset_asserted = True
        self.initialized = False
        self.pending = None
        self.overrun = False
        self.last_write_address = None
        for endpoint in self.endpoints.values():
            endpoint.reset()

    def release_reset(self):
        self.reset_asserted = False

    def initialize_text(self):
        require(not self.reset_asserted and self.text_present, 'Cannot initialize inactive text endpoint')
        self.initialized = True

    def read(self, address):
        if not self._address(address):
            return None
        if self.reset_asserted:
            return 0
        if address == self.registers['text_status'] and self.text_present:
            text = self.contract['text']
            return (text['present_mask'] |
                    (text['overrun_mask'] if self.overrun else 0) |
                    (text['ready_mask'] if self.initialized and self.pending is None else 0))
        if address in self.endpoints:
            return self.endpoints[address].read()
        return self.contract['addressing']['unmapped_read_value']

    def write(self, address, value):
        is_io = self._address(address)
        require(type(value) is int and 0 <= value <= 255, 'Write data must be a byte')
        if not is_io or self.reset_asserted:
            return False
        self.last_write_address = address  # Diagnostic observation; never used for read decode.
        if address in self.endpoints:
            self.endpoints[address].write(value)
            return True
        if not self.text_present:
            return False
        if address == self.registers['text_control']:
            if value & self.contract['text']['control_w1c_mask']:
                self.overrun = False
            return True
        if address == self.registers['text_data']:
            if not self.initialized or self.pending is not None:
                self.overrun = True
                return False
            self.pending = value
            return True
        return False

    def transmit(self):
        """Serializer accepts one byte; caller must prove real serializer readiness."""
        if self.reset_asserted or not self.initialized:
            return None
        value = self.pending
        self.pending = None
        return value


def audit_boundary(lock=None, build=BUILD):
    lock = json.loads(LOCK.read_text()) if lock is None else lock
    require(lock['revision'] == 'CP1-R2', 'Boundary audit requires R2 evidence')
    source_hashes = {}
    boards = {}
    for board in ('ME1', 'BP1'):
        name = NATIVE.format(board=board)
        path = build/name
        expected = lock['artifacts'][name]
        require(path.is_file() and digest(path) == expected, 'Missing or changed IO boundary evidence: '+name)
        source_hashes[name] = expected
        root = ET.parse(path).getroot()
        nodes = {}
        for net in root.findall('./nets/net'):
            for node in net.findall('node'):
                key = (node.get('ref'), node.get('pin'))
                require(key not in nodes, 'Duplicate native pin: '+str(key))
                nodes[key] = net.get('name').removeprefix('/')
        boards[board] = (root, nodes)

    checked = []
    def pin(board, ref, number, expected):
        actual = boards[board][1].get((ref, str(number)))
        require(actual == expected, f'{board} {ref}.{number}: expected {expected}, got {actual}')
        checked.append(dict(board=board, ref=ref, pin=str(number), net=actual))

    def connector(board, ref, expected):
        actual = {int(p): n for (r, p), n in boards[board][1].items() if r == ref}
        require(actual == dict(enumerate(expected, 1)), f'Changed {board} {ref} connector boundary')
        for number, net in enumerate(expected, 1):
            pin(board, ref, number, net)

    bits = lambda prefix: [prefix+str(i) for i in range(8)]
    connector('ME1', 'J4', ['5V','GND','IO_STROBE']+bits('IO_DATA')+bits('IO_ADDR'))
    connector('ME1', 'J5', ['5V','GND']+bits('IO_INPUT'))
    connector('BP1', 'J902', ['5V','GND','IO_STROBE']+bits('IO_DATA')+bits('IO_ADDRESS'))
    connector('BP1', 'J903', ['5V','GND']+bits('IO_INPUT'))
    connector('BP1', 'J42', ['5V','GND','IO_STROBE']+bits('IO_DATA')+bits('IO_ADDRESS'))
    connector('BP1', 'J43', ['5V','GND']+bits('IO_INPUT'))
    for ref, prefix, clock in (('U11','IO_DATA','DATA_CLOCK'), ('U15','IO_ADDR','ADDR_CLOCK')):
        component = next(c for c in boards['ME1'][0].findall('./components/comp') if c.get('ref') == ref)
        require(component.findtext('value') == 'CD74HCT273E', 'Unexpected R2 IO storage device')
        for i, number in enumerate((2,5,6,9,12,15,16,19)):
            pin('ME1', ref, number, prefix+str(i))
        pin('ME1', ref, 11, clock)
    # Address storage feeds back through mux A; only a write request selects live MAR at B.
    for half, ref in enumerate(('U16','U18')):
        pin('ME1', ref, 1, 'IO_ADDR_LOAD')
        for bit, (a,b,y) in enumerate(zip((2,5,11,14),(3,6,10,13),(4,7,9,12))):
            i = half*4+bit
            pin('ME1', ref, a, 'IO_ADDR'+str(i))
            pin('ME1', ref, b, 'ADDRESS'+str(i))
            pin('ME1', ref, y, 'IO_ADDR_D'+str(i))
    for ref, number, net in (('U10',17,'IO_REQUEST'),('U10',3,'IO_ADDR_LOAD'),
                             ('U24',4,'WRITE'),('U24',5,'IO_SELECT'),('U24',6,'IO_REQUEST'),
                             ('U24',11,'IO_STROBE'),('U24',12,'IO_READY'),('U24',13,'PH0')):
        pin('ME1', ref, number, net)
    return dict(passed=True, source_hashes=source_hashes, checked_pins=checked,
        existing_read_address=False, existing_read_strobe=False,
        write_address_is_registered=True,
        required_extension='Buffered live MAR read address, qualified read condition, private card returns and central selection into IO_INPUT.',
        scope='Native R2 connector/storage connectivity; not propagation, qualification or a new circuit implementation.')


def exercise(contract):
    model = Interface(contract)
    model.release_reset()
    model.initialize_text()
    # Independent literal oracle for the selected IO1 ABI, including ordinary memory.
    for address in range(65536):
        expected = None if address < 0xff00 else 0x81 if address == 0xff03 else 0
        require(model.read(address) == expected, f'Read alias or wrong default at {address:04X}')
    write_cases = 0
    for address in range(0xff00, 0x10000):
        for value in (0, 0x55, 0xaa, 0xff):
            model.assert_reset(); model.release_reset(); model.initialize_text()
            accepted = model.write(address, value)
            require(accepted == (address in (0xff00,0xff04)), 'Write decoded to wrong endpoint')
            require(model.pending == (value if address == 0xff00 else None), 'Unrelated write changed text mailbox')
            write_cases += 1
    model.assert_reset()
    fixture = RegisterFixture()
    model.attach(0xff10, fixture)
    model.release_reset(); model.initialize_text()
    require(model.write(0xff10, 0xa5), 'Second endpoint write failed')
    require(model.read(0xff03) == 0x81, 'Read used stale write address')
    require(model.read(model.last_write_address) == 0xa5, 'Stale-address negative control ineffective')
    require(model.write(0xff00, 0x41), 'Ready credit was not accepted')
    require(not model.write(0xff00, 0x42), 'Busy write was accepted')
    require(model.read(0xff03) == 0x82 and model.pending == 0x41, 'Busy write overwrote queued byte')
    require(model.read(0xff10) == 0xa5, 'Text write changed second endpoint')
    model.write(0xff04, 2)
    require(model.read(0xff03) == 0x80 and model.pending == 0x41, 'W1C changed pending data')
    require(model.transmit() == 0x41 and model.read(0xff03) == 0x81, 'Serializer handoff lost credit/data')
    model.write(0xff00, 0x43)
    model.assert_reset()
    require(not model.write(0xff00, 0x44) and model.transmit() is None, 'Reset did not suppress events')
    model.release_reset()
    require(model.read(0xff03) == 0x80 and model.read(0xff10) == 0, 'Reset/init isolation failed')
    absent = Interface(contract, text_present=False)
    absent.release_reset()
    require(absent.read(0xff03) == 0 and not absent.write(0xff00, 65), 'Absent endpoint appeared ready')
    return dict(passed=True, full_address_reads=65536, io_write_cases=write_cases,
        scenarios=['second-endpoint-isolation','stale-write-address-negative-control','ready-credit',
                   'busy-write-preserves-byte','overrun-write-one-clear','serializer-handoff',
                   'reset-abort','release-before-initialization','absent-text-device'],
        scope='Serialized logical transactions only; no implemented endpoint, edge timing, CDC or serial waveform qualification.')


def evaluate():
    contract = load()
    return dict(contract=contract, boundary=audit_boundary(), protocol=exercise(contract),
                physical_qualification=False, hardware_implementation='pending')

"""Replay the separate bridge candidate without promoting it into CP1-R2."""
import json
from .common import ROOT,VROOT,BUILD,digest
from . import io_bridge, io_bridge_boundary

LOCK=VROOT/'bridge-evidence.json'
MUTATIONS={'stale-read-address','return-slot-alias','reset-release-write','missing-page-qualifier'}


def source_paths():
    names=['Verification/'+n for n in ('designs/io_bridge_candidate.py','designs/drawing.py',
        'dm02/io_bridge.py','dm02/io_bridge_boundary.py','dm02/io_bridge_evidence.py',
        'dm02/connector_plan.py','dm02/common.py','dm02/legacy.py','dm02/native_migrate.py',
        'dm02/migrate.py','dm02/sexpr.py','dm02/electrical.py','hdl/io_bridge_tb.sv',
        'bridge-parts.json','mechanical-contract.json','targets/cp1/lock.json')]
    names += [str(p.relative_to(ROOT)) for p in io_bridge.SOURCE.glob('*') if p.is_file()]
    for board in ('MQ1','BR1'):
        names += [c['library_source'] for c in io_bridge.read_sheet(io_bridge.SOURCE/(board+'.sch'))['components']]
    return sorted(set(names))


def verify(lock,build=BUILD,source_root=ROOT):
    if lock['revision']!='CP1-BR1' or lock['physical_qualification'] is not False:
        raise ValueError('Bridge evidence is not physical acceptance')
    required={'cp1-bridge/summary.json','cp1-bridge/boundary-audit.json'}|{f'cp1-bridge/profile-{p}/simulation.log' for p in range(4)}|{
        f'cp1-bridge/mutations/{name}/simulation.log' for name in MUTATIONS}
    required |= {f'cp1-bridge/native/{b}/{b}.{ext}' for b in ('MQ1','BR1') for ext in ('xml','kicad_sch')}
    required |= {f'cp1-bridge/native/{b}/comparison.json' for b in ('MQ1','BR1')}
    required |= {f'cp1-bridge/profile-{p}/bridge.sv' for p in range(4)}
    required |= {f'cp1-bridge/mutations/{name}/bridge.sv' for name in MUTATIONS}
    parts=json.loads(io_bridge.PARTS.read_text())
    required |= {'cp1-bridge/sources/'+p['file'] for p in parts['devices'].values()}
    if not required<=lock['artifacts'].keys():raise ValueError('Missing required bridge artifacts')
    if not set(source_paths())<=lock['source_hashes'].keys():raise ValueError('Missing required bridge sources')
    for base,records in ((source_root,lock['source_hashes']),(build,lock['artifacts'])):
        for name,expected in records.items():
            path=(base/name).resolve()
            if not path.is_relative_to(base.resolve()):raise ValueError('Bridge evidence path escapes root')
            if not path.is_file() or digest(path)!=expected:raise ValueError('Changed bridge evidence: '+name)
    result=json.loads((build/'cp1-bridge/summary.json').read_text())
    if (result['revision']!='CP1-BR1' or result['baseline_revision']!='CP1-R2' or
        result['passed'] is not True or result['physical_qualification'] is not False or result['integrated_into_R2'] is not False):
        raise ValueError('Bridge candidate status invalid')
    if set(result['profiles'])!={'0','1','2','3'} or set(result['mutations'])!=MUTATIONS:
        raise ValueError('Incomplete bridge profiles/mutations')
    for profile,record in result['profiles'].items():
        log=(build/f'cp1-bridge/profile-{profile}/simulation.log').read_text()
        if record['passed'] is not True or 'PASS bridge read_cases=70020 write_cases=256' not in log:
            raise ValueError('Bridge profile failed: '+profile)
    for name,record in result['mutations'].items():
        log=(build/f'cp1-bridge/mutations/{name}/simulation.log').read_text()
        if record['passed'] is not False or 'FATAL:' not in log:
            raise ValueError('Bridge mutation not detected: '+name)
    if result['package_load_audit']['over_50pf']:
        raise ValueError('Bridge internal load screen incomplete')
    boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
    circuit=io_bridge.Circuit(build/'cp1-bridge/native',boundary)
    if json.loads(json.dumps(circuit.audit()))!=result['package_load_audit']:
        raise ValueError('Bridge audit differs from native replay')
    binding=io_bridge_boundary.audit(circuit)
    if binding!=result['boundary_audit'] or binding!=json.loads((build/'cp1-bridge/boundary-audit.json').read_text()):
        raise ValueError('Bridge boundary differs from R2 replay')
    if not binding['source_hashes'].items()<=lock['artifacts'].items():
        raise ValueError('Missing locked R2 boundary dependencies')
    for profile in range(4):
        if circuit.hdl(profile)!=(build/f'cp1-bridge/profile-{profile}/bridge.sv').read_text():
            raise ValueError('Bridge HDL differs from native replay')
    for name in MUTATIONS:
        if circuit.fault(name).hdl(1)!=(build/f'cp1-bridge/mutations/{name}/bridge.sv').read_text():
            raise ValueError('Bridge mutation HDL differs from native replay')
    for board in ('MQ1','BR1'):
        if result['native'][board]['status']!='pass' or result['structure'][board]['findings']:
            raise ValueError('Bridge native/structural acceptance incomplete')
    return result


def load(build=BUILD):
    lock=json.loads(LOCK.read_text())
    return lock,verify(lock,build)

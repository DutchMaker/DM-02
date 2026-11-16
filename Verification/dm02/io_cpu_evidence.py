"""Fail-closed replay of the separate CPU/BR1 diagnostic study."""
import json
from .common import ROOT,VROOT,BUILD,digest
from . import io_cpu,io_bridge,io_bridge_evidence

LOCK=VROOT/'io-cpu-evidence.json'
PREFIX='cp1-io-cpu/'
FAULTS={'disconnected-return','stale-read-address','return-slot-alias'}
CASES=({f'cpu-{c}' for c in range(12)}|{f'bridge-{p}' for p in (0,2,3)}|
       {f'absent-{p}' for p in (1,2,4,8,15)}|{f'endpoint-{n}' for n in (0,80,120,160,200,400)}|
       {'slow-400'}|{f'duty-{d}-ppm-{p}' for d in (.37,.63) for p in (-30,30)}|
       {'fault-'+f for f in FAULTS})
NEGATIVE={'endpoint-200','endpoint-400'}|{'fault-'+f for f in FAULTS}


def require(condition,message):
    if not condition:raise ValueError(message)


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-BI1' and lock['physical_qualification'] is False,'Invalid CPU bridge evidence scope')
    require({'Verification/dm02/io_cpu.py','Verification/dm02/io_cpu_evidence.py',
             'Verification/hdl/io_cpu_probe.sv','Verification/build/cp1-io-cpu/run_study.py'}<=lock['source_hashes'].keys(),
            'Missing CPU bridge source dependency')
    required={PREFIX+'matrix.json'}
    for name in CASES:
        required |= {PREFIX+f'profiles/{name}/'+n for n in
            ('result.json','simulation.log','tb.sv','bridge.sv','program.hex','echo-expected.hex','diagnostic.bin')}
    require(required<=lock['artifacts'].keys(),'Missing CPU bridge artifacts')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,expected in hashes.items():
            path=(base/name).resolve()
            require(path.is_relative_to(base.resolve()),'CPU bridge path escapes evidence root')
            require(path.is_file() and digest(path)==expected,'Changed CPU bridge evidence: '+name)
    matrix=json.loads((build/PREFIX/'matrix.json').read_text())
    require(matrix['revision']=='CP1-BI1' and matrix['physical_qualification'] is False and
            matrix['promoted_into_R2'] is False and matrix['autonomous_rom_boot'] is False,'CPU bridge scope changed')
    require(set(matrix['results'])==CASES,'Incomplete CPU bridge matrix')
    require(digest(ROOT/'Verification/build/cp1-io-cpu/run_study.py')==matrix['study_script_sha256'],
            'Changed CPU bridge matrix script')
    io_bridge_evidence.load(build)
    boundary=json.loads((io_bridge.SOURCE/'boundary.json').read_text())
    circuit=io_bridge.Circuit(build/'cp1-bridge/native',boundary)
    for name,result in matrix['results'].items():
        folder=build/PREFIX/'profiles'/name
        require(result==json.loads((folder/'result.json').read_text()),'Matrix/profile disagreement')
        require(result['passed']==(name not in NEGATIVE),'Unexpected CPU bridge profile result: '+name)
        require(result['physical_qualification'] is False and result['boot_injected'] is True,'Diagnostic preload scope changed')
        require(result['source_hashes'].items()<=lock['source_hashes'].items(),'Missing CPU bridge source dependency')
        require(result['input_hashes'].items()<=lock['artifacts'].items(),'Missing locked CPU input dependency')
        require(result['bridge_lock_sha256']==digest(io_bridge_evidence.LOCK),'BR1 dependency changed')
        for file,sha in {**result['model_hashes'],**result['fixture_hashes']}.items():
            require(lock['artifacts'].get(PREFIX+f'profiles/{name}/'+file)==sha,'Missing profile model/fixture lock')
        old=next(n for n in result['input_hashes'] if n.endswith('/tb.sv'))
        require(io_cpu.compose_bench((build/old).read_text(),result['fault'])==(folder/'tb.sv').read_text(),
                'CPU bridge bench regeneration differs')
        c=circuit.fault(result['fault']) if result['fault'] in FAULTS-{'disconnected-return'} else circuit
        require(c.hdl(result['bridge_profile'])==(folder/'bridge.sv').read_text(),'Native bridge regeneration differs')
        image,echo,size=io_cpu.diagnostic(result['present_n'])
        require((folder/'program.hex').read_text()==''.join(f'{b:02x}\n' for b in image) and
                (folder/'echo-expected.hex').read_text()==''.join(f'{b:02x}\n' for b in echo) and
                (folder/'diagnostic.bin').read_bytes()==image[:size],'CPU diagnostic regeneration differs')
        log=(folder/'simulation.log').read_text()
        if name in NEGATIVE:
            reason='sampled setup reserve below 10 ns' if name=='endpoint-200' else 'echo mismatch'
            require(result['exit_code']!=0 and 'FATAL:' in log and reason in log,'Negative control failed for wrong reason')
        else:
            require(result['exit_code']==0 and 'PASS CPU bridge echoes=14 reads=12 cycles=334' in log and
                    'PASS CPU bridge reset' in log,'CPU bridge simulation incomplete')
            require(result['observations']['min_setup_ns']>=35 and result['observations']['min_hold_ns']>=5,
                    'CPU bridge sampled timing failed')
            require(all(f'ECHO {i} {b:02x}' in log for i,b in enumerate(echo)),'Missing echoed diagnostic result')
    return matrix


def load(build=BUILD):
    lock=json.loads(LOCK.read_text())
    return lock,verify(lock,build)

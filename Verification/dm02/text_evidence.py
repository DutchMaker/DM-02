"""Fail-closed bounded replay for the separate CP1-TX1 candidate study."""
import json
import re
from .common import ROOT,VROOT,BUILD,digest
from . import text_card,text_cpu,io_bridge,io_bridge_evidence

LOCK=VROOT/'text-evidence.json'
PREFIX='cp1-text/'
FAULTS={'mailbox-overwrite':'serial mismatch','early-credit':'TX1 status',
        'reversed-bits':'serial mismatch','stale-read-address':'TX1 status'}
SERIAL={**{f'logic-{p}':(p,0,None) for p in range(4)},
        **{f'ppm-{p}':(1,p,None) for p in (-30,30)},**{'fault-'+f:(1,0,f) for f in FAULTS}}
CPU={'cpu-max':(1,1,1,False,0),'cpu-zero':(0,0,0,False,0),
     'cpu-mixed2':(2,2,2,False,0),'cpu-mixed3':(3,3,3,False,0),
     'cpu-fast':(1,1,1,False,30),'cpu-absent':(1,1,1,True,0)}
require=text_card.require


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-TX1' and lock['physical_qualification'] is False,'Invalid TX1 scope')
    required_sources=set(text_card.SOURCES)|{'Verification/dm02/text_cpu.py','Verification/dm02/text_evidence.py',
        'Verification/hdl/text_tb.sv','Verification/hdl/text_cpu_probe.sv','Verification/build/cp1-text/run_study.py'}
    require(required_sources<=lock['source_hashes'].keys(),'Missing TX1 source dependency')
    required={PREFIX+'final/matrix.json',PREFIX+'final/audit.json',PREFIX+'iteration-2/native/TX1/TX1.xml',
              PREFIX+'iteration-2/native/TX1/comparison.json',PREFIX+'iteration-2/structure.json'}
    for name in SERIAL.keys()|CPU.keys():
        required|={PREFIX+f'final/{name}/'+file for file in ('text.sv','result.json','simulation.log','compile.log')}
    require(required<=lock['artifacts'].keys(),'Missing TX1 evidence artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,expected in hashes.items():
            path=(base/name).resolve()
            require(path.is_relative_to(base.resolve()),'TX1 path escape')
            require(path.is_file() and digest(path)==expected,'Changed TX1 evidence: '+name)
    folder=build/PREFIX;matrix=json.loads((folder/'final/matrix.json').read_text())
    require(matrix['revision']=='CP1-TX1' and matrix['accepted_revision']=='CP1-R2' and
            matrix['physical_qualification'] is False and matrix['autonomous_rom_boot'] is False,'TX1 matrix scope changed')
    require(set(matrix['standalone'])==SERIAL.keys() and set(matrix['cpu'])==CPU.keys(),'Incomplete TX1 matrix')
    require(matrix['script_sha256']==digest(ROOT/'Verification/build/cp1-text/run_study.py'),'Changed TX1 matrix script')
    require(matrix['native_folder']=='iteration-2/native/TX1','Changed TX1 native selection')
    native=folder/matrix['native_folder'];c=text_card.Circuit(native)
    audit=json.loads(json.dumps(c.audit()))
    require(audit==json.loads((folder/'final/audit.json').read_text()),'Changed TX1 native audit')
    require(audit['dip_count']==37 and not audit['over_screen'],'TX1 package/load screen changed')
    require(not json.loads((folder/'iteration-2/structure.json').read_text())['findings'],'TX1 structural findings')
    parity=json.loads((native/'comparison.json').read_text())
    require(parity['status']=='pass' and parity['source_hash']==digest(text_card.SOURCE/'TX1.sch'),'TX1 native parity stale')
    from designs.text_candidate import candidate
    require(candidate().finish()==(text_card.SOURCE/'TX1.sch').read_text(),'TX1 generator differs')
    for provenance in json.loads((native/'libraries.json').read_text()):
        require(lock['source_hashes'].get(provenance['source'])==provenance['sha256'],'Missing TX1 native library source')
    io_bridge_evidence.load(build)
    bridge=io_bridge.Circuit(build/'cp1-bridge/native',json.loads((io_bridge.SOURCE/'boundary.json').read_text()))
    for name,r in {**matrix['standalone'],**matrix['cpu']}.items():
        run=folder/'final'/name;saved=json.loads((run/'result.json').read_text())
        require((dict(saved,fault=r['fault']) if name in SERIAL else saved)==r,'TX1 matrix/result disagreement')
        require(r['source_hashes'].items()<=lock['source_hashes'].items(),'TX1 source dependency omitted')
        require(r['physical_qualification'] is False and r['timing_violations']==0,'TX1 scope/timing result changed')
        log=(run/'simulation.log').read_text()
        actual_violations=sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log)))
        require(actual_violations==0 and 'TIMING_SUMMARY' in log,'TX1 missing timing observations')
        if name in SERIAL:
            p,ppm,fault=SERIAL[name]
            require((r['profile'],r['ppm'],r['fault'])==(p,ppm,fault),'TX1 serial parameters changed')
            model=c.fault(fault) if fault else c
            require(model.hdl(p)==(run/'text.sv').read_text(),'TX1 serial model regeneration differs')
            for file,sha in r['hashes'].items():require(lock['artifacts'].get(PREFIX+f'final/{name}/'+file)==sha,'TX1 profile hash omitted')
            if fault:
                require(r['passed'] is False and r['exit_code']!=0 and 'FATAL:' in log and FAULTS[fault] in log,'TX1 mutation failed for wrong reason')
            else:
                require(r['passed'] is True and r['exit_code']==0 and 'PASS TX1 bytes=256 busy_checks=15' in log,'TX1 serial incomplete')
                received=re.findall(r'^RX (\d+) ([0-9a-f]{2})$',log,re.M)
                require(received==[(str(i),f'{i:02x}') for i in range(256)],'TX1 serial transcript incomplete')
        else:
            corner,bp,tp,absent,ppm=CPU[name]
            require((r['corner'],r['bridge_profile'],r['text_profile'],r['absent'],r['ppm'],r['period_ns'])==
                    (corner,bp,tp,absent,ppm,250),'TX1 CPU parameters changed')
            require(r['passed'] is True and r['exit_code']==0 and r['autonomous_rom_boot'] is False,'TX1 CPU scope/result changed')
            require(r['input_hashes'].items()<=lock['artifacts'].items(),'Missing R2 inputs for TX1')
            for file,sha in r['artifact_hashes'].items():require(lock['artifacts'].get(PREFIX+f'final/{name}/'+file)==sha,'Missing TX1 CPU artifact')
            old=next(n for n in r['input_hashes'] if n.endswith('/tb.sv'))
            require(text_cpu.bench((build/old).read_text())==(run/'tb.sv').read_text(),'TX1 CPU bench regeneration differs')
            require(c.hdl(tp)==(run/'text.sv').read_text() and bridge.hdl(bp)==(run/'bridge.sv').read_text(),'TX1 CPU model regeneration differs')
            code=text_cpu.diagnostic();image=code+bytes(65536-len(code))
            require((run/'diagnostic.bin').read_bytes()==code and
                (run/'program.hex').read_text()==''.join(f'{b:02x}\n' for b in image) and
                (run/'serial-expected.hex').read_text()==''.join(f'{b:02x}\n' for b in text_cpu.TRANSCRIPT),'TX1 CPU fixture regeneration differs')
            if absent:require('PASS TX1 CPU absent-device diagnostic' in log,'TX1 CPU absence check missing')
            else:
                require('PASS TX1 CPU received=5' in log,'TX1 CPU terminal transcript missing')
                require(re.findall(r'^CPU_RX (\d+) ([0-9a-f]{2})$',log,re.M)==
                        [(str(i+1),f'{b:02x}') for i,b in enumerate(text_cpu.TRANSCRIPT)],'TX1 CPU bytes differ')
                o=r['observations'];require(o['setup_ns']>=35 and o['hold_ns']>=5 and
                    o['final_stop_ns']>o['halted_ns'],'TX1 CPU timing/HALT observation failed')
    return matrix,audit


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());matrix,audit=verify(lock,build)
    return lock,matrix,audit

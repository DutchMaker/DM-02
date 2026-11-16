"""Bounded source/model/fixture replay of the CP1-TB1 ROM-only startup study."""
import json
import re
from .common import ROOT,VROOT,BUILD,digest
from . import text_boot,text_card,text_cpu,text_evidence,io_bridge

LOCK=VROOT/'text-boot-evidence.json'
PREFIX='cp1-text-boot/'
CASES={'guarded-max':(1,1,1,165,None),'seed-0':(1,1,1,0,None),'seed-255':(1,1,1,255,None),
       'zero':(0,0,0,90,None),'mixed2':(2,2,2,165,None),'mixed3':(3,3,3,165,None),
       **{'fault-'+f:(1,1,1,165,f) for f in ('wrong-loader-byte','wrong-loader-address','skip-loader')}}
REASONS={'wrong-loader-byte':'TB1 loader write data','wrong-loader-address':'TB1 loader write address',
         'skip-loader':'TB1 incomplete reconstruction'}
require=text_boot.require


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-TB1' and lock['physical_qualification'] is False,'Invalid TB1 scope')
    require((set(text_boot.SOURCES)|{'Verification/dm02/text_boot_evidence.py',
        'Verification/build/cp1-text-boot/run_study.py'})<=lock['source_hashes'].keys(),'Missing TB1 source')
    required={PREFIX+'matrix.json'}
    for name in CASES:
        required|={PREFIX+name+'/'+file for file in ('result.json','simulation.log','compile.log','oracle.json',
            'tb.sv','ME1.sv','support.sv','text.sv','bridge.sv','boot-rom.bin','boot-rom.hex',
            'sram-power-on.bin','sram-power-on.hex','payload.bin','payload.hex','loader.lst','serial-expected.hex')}
    require(required<=lock['artifacts'].keys(),'Missing TB1 artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            path=(base/name).resolve();require(path.is_relative_to(base.resolve()),'TB1 path escape')
            require(path.is_file() and digest(path)==sha,'Changed TB1 evidence: '+name)
    matrix=json.loads((build/PREFIX/'matrix.json').read_text())
    require(matrix['revision']=='CP1-TB1' and matrix['accepted_revision']=='CP1-R2' and
            matrix['physical_qualification'] is False and matrix['rom_only_startup'] is True and
            matrix['host_boot_injected'] is False,'TB1 matrix scope changed')
    require(set(matrix['results'])==CASES.keys(),'Incomplete TB1 matrix')
    require(matrix['script_sha256']==digest(ROOT/'Verification/build/cp1-text-boot/run_study.py'),'Changed TB1 matrix script')
    text_evidence.load(build)
    c=text_card.Circuit(build/'cp1-text/iteration-2/native/TX1')
    bridge=io_bridge.Circuit(build/'cp1-bridge/native',json.loads((io_bridge.SOURCE/'boundary.json').read_text()))
    for name,r in matrix['results'].items():
        folder=build/PREFIX/name
        require(r==json.loads((folder/'result.json').read_text()),'TB1 matrix/result disagreement')
        corner,bp,tp,seed,fault=CASES[name]
        require((r['corner'],r['bridge_profile'],r['text_profile'],r['seed'],r['fault'])==(corner,bp,tp,seed,fault),'TB1 parameters changed')
        require(r['physical_qualification'] is False and r['rom_only_startup'] is True and
                r['host_boot_injected'] is False,'TB1 result scope changed')
        require(r['source_hashes'].items()<=lock['source_hashes'].items(),'Missing TB1 run source')
        require(r['input_hashes'].items()<=lock['artifacts'].items(),'Missing TB1 R2 input')
        for file,sha in r['hashes'].items():require(lock['artifacts'].get(PREFIX+name+'/'+file)==sha,'Missing TB1 run artifact')
        data=text_boot.image(seed);proof=text_boot.oracle(data)
        require(proof==json.loads((folder/'oracle.json').read_text()),'TB1 architectural oracle differs')
        rom=bytearray(data['rom'])
        if fault=='wrong-loader-byte':rom[4]^=1
        elif fault=='wrong-loader-address':rom[7]^=1
        elif fault=='skip-loader':rom[:3]=bytes([0xc3,0x40,0])
        for stem,raw in [('boot-rom',rom),('sram-power-on',data['poison']),('payload',data['payload'])]:
            require((folder/(stem+'.bin')).read_bytes()==raw and (folder/(stem+'.hex')).read_text()==
                    ''.join(f'{b:02x}\n' for b in raw),'TB1 fixture regeneration differs: '+stem)
        require((folder/'loader.lst').read_text()==data['listing'],'TB1 listing differs')
        require((folder/'serial-expected.hex').read_text()==''.join(f'{b:02x}\n' for b in text_cpu.TRANSCRIPT),'TB1 terminal oracle differs')
        old=next(n for n in r['input_hashes'] if n.endswith('/tb.sv'));parent=(build/old).parent
        require(text_boot.bench((build/old).read_text(),len(data['payload']))==(folder/'tb.sv').read_text(),'TB1 bench regeneration differs')
        memory,support=text_boot.models((parent/'ME1.sv').read_text(),(parent/'support.sv').read_text())
        require(memory==(folder/'ME1.sv').read_text() and support==(folder/'support.sv').read_text(),'TB1 memory initialization differs')
        require(c.hdl(tp)==(folder/'text.sv').read_text() and bridge.hdl(bp)==(folder/'bridge.sv').read_text(),'TB1 endpoint/bridge model differs')
        for file in text_boot.io_cpu.BOARDS:
            if file!='ME1':require((parent/(file+'.sv')).read_bytes()==(folder/(file+'.sv')).read_bytes(),'TB1 CPU model differs')
        log=(folder/'simulation.log').read_text()
        require('TIMING_SUMMARY' in log and not sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log))) and
                r['timing_violations']==0,'TB1 timing observations failed')
        if fault:require(r['passed'] is False and r['exit_code']!=0 and 'FATAL:' in log and REASONS[fault] in log,'TB1 mutation failed for wrong reason')
        else:
            require(r['passed'] is True and r['exit_code']==0 and
                    'PASS TB1 ROM reconstruction bytes=160 writes=160 pc=4000' in log,'TB1 reconstruction missing')
            require(re.findall(r'^CPU_RX (\d+) ([0-9a-f]{2})$',log,re.M)==
                    [(str(i+1),f'{b:02x}') for i,b in enumerate(text_cpu.TRANSCRIPT)],'TB1 transcript differs')
            match=re.search(r'PASS TX1 CPU received=5 reads=(\d+) setup_ns=([\d.]+) hold_ns=([\d.]+) halted_ns=([\d.]+) final_stop_ns=([\d.]+)',log)
            require(match,'TB1 CPU completion missing')
            reads,setup,hold,halt,stop=map(float,match.groups())
            require(reads>0 and setup>=35 and hold>=5 and stop>halt>25000000,'TB1 sampled timing/guard/HALT failed')
    return matrix


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

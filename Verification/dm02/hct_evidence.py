"""Fail-closed HP1 sourcing review and HB1 conditional digital evidence replay."""
import json
import re
from .common import ROOT, VROOT, BUILD, digest
from . import hct_preference as hp, hct_buffers as hb, mar_distribution_evidence as mde

LOCK=VROOT/'hct-evidence.json'
SOURCES=['Verification/dm02/hct_preference.py','Verification/dm02/hct_buffers.py',
    'Verification/dm02/hct_evidence.py','Verification/mar-distribution-evidence.json',
    'Verification/text-boot-evidence.json','Verification/operating-contract.json','Verification/hdl/text_cells.sv']
PREFIX='cp1-hct-buffers/iteration-1/'
require=hb.require


def replay(build=BUILD):
    review=hp.review(build)
    require(review==json.loads((build/'cp1-hct-preference/review.json').read_text()),'HP1 review replay differs')
    folder=build/PREFIX;c=hb.Candidate()
    for name,text in c.documents().items():
        require((hb.CANONICAL/name).read_text()==text,'HB1 canonical differs: '+name)
        require((folder/'native'/name).read_text()==text,'HB1 generated source differs: '+name)
    summary=json.loads((folder/'summary.json').read_text())
    require(summary['revision']=='CP1-HB1' and summary['physical_qualification'] is False and
        summary['promoted_into_R2'] is False,'Invalid HB1 scope')
    native=c.compare(folder/'native/HB1.xml');require(native['passed'] and native==summary['native'],'HB1 native replay differs')
    require(set(summary['native_faults'])==set(hb.md.FAULTS),'Incomplete HB1 native fault set')
    for fault,result in summary['native_faults'].items():
        require(c.compare(folder/fault/'HB1.xml')==result and not result['passed'],'HB1 fault replay differs')
    inventory=hb.loads(c,folder/'native/HB1.xml')
    require(inventory==json.loads((folder/'loads.json').read_text()),'HB1 load replay differs')
    bindings=c.bindings(folder/'native/HB1.xml')
    require(bindings==json.loads((folder/'bindings.json').read_text()),'HB1 binding replay differs')
    require(all(r['enabled'] and r['bit']==r['source_bit'] for r in bindings),'HB1 address transfer differs')
    require(set(summary['mapping'])=={'0','1','2','3'} and set(summary['mapping_faults'])=={'swapped-address','disabled-buffer'},'Incomplete HB1 mapping coverage')
    for name,r in list(summary['mapping'].items())+list(summary['mapping_faults'].items()):
        fault=name in summary['mapping_faults'];sub='mapping-'+name if fault else 'all-addresses-'+name
        log=(folder/sub/'simulation.log').read_text()
        arcs=c.bindings(folder/name/'HB1.xml') if fault else bindings
        require((folder/sub/'tb.sv').read_text()==hb.mapping_source(arcs,r['profile']),'HB1 mapping source differs')
        require(r['bindings']==arcs and r['physical_qualification'] is False,'Changed HB1 mapping scope')
        require(r['passed']==(not fault) and (r['exit_code']==0)==(not fault),'Unexpected HB1 mapping result')
        require(('HB1 address mapping got=' if fault else 'PASS HB1 all 65536 address words') in log,'HB1 mapping log differs')
    expected={'boot-guarded-max':('guarded-max',1),'boot-zero':('zero',0),
        'boot-mixed2':('mixed2',2),'boot-mixed3':('mixed3',3),'boot-swapped':('guarded-max',1),'memory':('guarded-max',1)}
    require(set(summary['results'])==set(expected),'Incomplete HB1 simulation set')
    for name,(case,profile) in expected.items():
        r=summary['results'][name];run=folder/name;memory=name=='memory';fault=name=='boot-swapped'
        require(r==json.loads((run/'result.json').read_text()),'HB1 result/summary differs')
        require(r['physical_qualification'] is False and r['case']==case and r['profile']==profile,'HB1 run scope differs')
        require(r['passed']==(not fault) and (r['exit_code']==0)==(not fault),'Unexpected HB1 simulation result')
        arcs=c.bindings(folder/'swapped-address/HB1.xml') if fault else bindings
        require(r['bindings']==arcs and r['buffer_delays_ns']=={str(k):v for k,v in hb.delays(arcs,profile).items()},'HB1 delay/transfer differs')
        model='module.sv' if memory else 'ME1.sv'
        for key,sha in r['input_hashes'].items():
            require(digest(build/key)==sha,'Changed HB1 original input: '+key)
            name_only=key.rsplit('/',1)[-1]
            if name_only==model:
                require((run/model).read_text()==hb.memory_model((build/key).read_text(),arcs,profile),'HB1 regenerated HDL differs')
            else:require(digest(run/name_only)==sha,'Changed HB1 copied input: '+name_only)
        for key,sha in r['model_hashes'].items():require(digest(run/key)==sha,'HB1 model hash differs')
        log=(run/'simulation.log').read_text()
        require(not re.search(r'TIMING_SUMMARY .*violations=[1-9]',log),'HB1 timing violations')
        if fault:require('FATAL' in log,'Missing HB1 swapped-address failure')
        elif memory:require('DONE memory-io' in log and r['quick'] is False,'Incomplete HB1 memory exercise')
        else:
            require('PASS TB1 ROM reconstruction' in log and 'PASS TX1 CPU received=5' in log,'Incomplete HB1 ROM/text boot')
            match=re.search(r'PASS TX1 CPU received=5 reads=\d+ setup_ns=([\d.]+) hold_ns=([\d.]+)',log)
            require(match and float(match[1])==r['cpu_io_setup_ns'] and float(match[2])==r['cpu_io_hold_ns'],'HB1 measured model margin differs')
            require(r['cpu_io_setup_ns']>=10 and r['cpu_io_hold_ns']>0,'HB1 sampled IO reserve failed')
    return dict(review=review,candidate=summary,loads=inventory,physical_qualification=False)


def verify(lock,build=BUILD):
    require(lock.get('revision')=='CP1-HP1/HB1' and lock.get('physical_qualification') is False,'Invalid HCT evidence scope')
    required=set(SOURCES)|{str(p.relative_to(ROOT)) for p in hb.CANONICAL.glob('*.kicad_sch')}
    require(required<=lock['source_hashes'].keys(),'Missing HCT source')
    artifacts={'cp1-hct-preference/review.json',PREFIX+'summary.json',PREFIX+'bindings.json',PREFIX+'loads.json'}
    artifacts|={'cp1-hct-preference/sources/'+n for n in ('retrieval.json','conditions-review.pdf','review-pages.pdf')}
    for table in hp.TABLES.values():
        artifacts|={'cp1-hct-preference/sources/'+table['source']+ext for ext in ('.pdf','.txt')}
    for sub in ('native',*hb.md.FAULTS):
        artifacts.add(PREFIX+sub+'/HB1.xml')
        artifacts|={PREFIX+sub+'/'+name for name in hb.Candidate().documents()}
    for sub in ('all-addresses-0','all-addresses-1','all-addresses-2','all-addresses-3','mapping-swapped-address','mapping-disabled-buffer'):
        artifacts|={PREFIX+sub+'/'+name for name in ('tb.sv','compile.log','simulation.log','result.json')}
    for sub in ('boot-guarded-max','boot-zero','boot-mixed2','boot-mixed3','boot-swapped','memory'):
        artifacts|={PREFIX+sub+'/'+name for name in ('compile.log','simulation.log','result.json')}
        names=(['module.sv','clock.sv','support.sv','tb.sv','program.hex'] if sub=='memory' else
            [b+'.sv' for b in hb.io_cpu.BOARDS]+['support.sv','bridge.sv','text.sv','tb.sv','alu.bin','control.hex',
             'boot-rom.hex','sram-power-on.hex','payload.hex','serial-expected.hex'])
        artifacts|={PREFIX+sub+'/'+name for name in names}
    require(artifacts<=lock['artifacts'].keys(),'Missing HCT artifact')
    for root,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            path=(root/name).resolve();require(path.is_relative_to(root.resolve()),'HCT path escape')
            require(path.is_file() and digest(path)==sha,'Changed HCT evidence: '+name)
    mde.load(build)
    return replay(build)


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

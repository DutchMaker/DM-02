"""Fail-closed HR1 native/model/diagnostic replay; no physical promotion."""
import json
import re
from .common import ROOT,VROOT,BUILD,digest
from . import hct_registers as hr
from . import hct_register_paths as paths

LOCK=VROOT/'hct-register-evidence.json'
PREFIX='cp1-hct-registers/iteration-3/'
SOURCES=['Verification/dm02/hct_registers.py','Verification/dm02/hct_register_evidence.py',
    'Verification/hdl/hct377.sv','Verification/hct-evidence.json','Verification/targets/cp1/lock.json',
    'Verification/text-boot-evidence.json','Verification/operating-contract.json','Verification/dm02/hct_register_paths.py']
REASONS={'data-hold':'HR1 data hold','disabled-data-hold':'HR1 data hold',
    'enable-hold':'HR1 enable hold','data-setup':'HR1 data setup','enable-setup':'HR1 enable setup',
    'high-pulse':'HR1 high pulse','low-pulse':'HR1 low pulse','missing-init':'HR1 missing synchronous init','reset-no-recovery':'HR1 missing synchronous init'}
require=hr.require
LEGACY_INPUTS={f'cp1-hct273/candidate/Circuits/KiCad/Compact/candidates/{b}.sch' for b in hr.TARGETS}


def replay(build=BUILD):
    folder=build/PREFIX;c=hr.Candidate();summary=json.loads((folder/'summary.json').read_text())
    require(summary['revision']=='CP1-HR1' and summary['physical_qualification'] is False and
        summary['promoted_into_R2'] is False,'HR1 scope changed')
    for name,text in c.documents().items():
        require((hr.CANONICAL/name).read_text()==text==(folder/'native'/name).read_text(),'HR1 native source differs')
    require(c.compare(folder/'native/HR1.xml')==summary['native'] and summary['native']['passed'],'HR1 native replay')
    require(set(summary['native_faults'])==set(hr.NATIVE_FAULTS),'HR1 native fault coverage')
    for fault,result in summary['native_faults'].items():
        require(c.compare(folder/fault/'HR1.xml')==result and not result['passed'],'HR1 native fault not detected')
        for name,text in c.documents(fault).items():require((folder/fault/name).read_text()==text,'HR1 native mutation changed')
    # The frozen legacy parser requires repository-relative source paths. An
    # isolated evidence tree must contain identical copies, then the parser can
    # safely use the separately hash-checked canonical originals.
    for key in LEGACY_INPUTS:require(digest(build/key)==digest(BUILD/key),'HR1 isolated legacy source differs')
    arcs=hr.bindings(c,folder/'native/HR1.xml');buffers=c.bindings(folder/'native/HR1.xml')
    require(arcs==json.loads((folder/'bindings.json').read_text()),'HR1 binding replay')
    require(buffers==json.loads((folder/'buffer-bindings.json').read_text()),'HR1 buffer binding replay')
    inventory=hr.loads(c,folder/'native/HR1.xml');require(inventory==json.loads((folder/'loads.json').read_text()),'HR1 load replay')
    require(paths.review(inventory,build)==json.loads((folder/'path-review.json').read_text()),'HR1 path review differs')
    require(inventory['families']==dict(HCT=134,AHCT=115,AHC=9,ACT=10,memory=4),'HR1 package count')
    require(set(summary['model_tests'])==set(hr.MODEL_CASES),'HR1 monitor coverage')
    for case,r in summary['model_tests'].items():
        run=folder/('model-'+case);log=(run/'simulation.log').read_text()
        require(r==json.loads((run/'result.json').read_text()),'HR1 model result differs')
        valid=case in ('valid','reset-recovery')
        require(r['passed']==valid and (r['exit_code']==0)==valid,'HR1 model outcome')
        require(('PASS HR1 model' if valid else REASONS[case]) in log,'HR1 missing monitor evidence')
        require((run/'hct377.sv').read_text()==hr.MODEL.read_text(),'HR1 monitor source differs')
        for name,sha in r['model_hashes'].items():require(digest(run/name)==sha,'HR1 unit source hash')
    require(set(summary['results'])=={j[0] for j in hr.JOBS},'HR1 diagnostic coverage')
    minima={k:1e9 for k in ('data_setup','enable_setup','data_hold','enable_hold','high_pulse','low_pulse')}
    for name,kind,case,profile in hr.JOBS:
        run=folder/name;r=summary['results'][name];log=(run/'simulation.log').read_text()
        fault=name in ('registers-enable','registers-init-clock')
        require(r==json.loads((run/'result.json').read_text()),'HR1 diagnostic result differs')
        require((r['kind'],r['case'],r['profile'])==(kind,case,profile) and r['physical_qualification'] is False,'HR1 profile changed')
        require(r['passed']==(not fault) and (r['exit_code']==0)==(not fault),'HR1 unexpected diagnostic outcome')
        for key,sha in r['input_hashes'].items():
            require(digest(build/key)==sha,'HR1 pinned input changed')
            fn=key.rsplit('/',1)[-1];original=(build/key).read_text() if fn.endswith('.sv') else None
            board=({'registers.sv':'RG1'} if kind=='registers' else {'module.sv':'AL1'} if kind=='alu' else {'AL1.sv':'AL1','RG1.sv':'RG1'}).get(fn)
            if board:require((run/fn).read_text()==hr.model_text(original,board,arcs,profile,'enable' if name=='registers-enable' else None),'HR1 model regeneration')
            elif fn=='ME1.sv':require((run/fn).read_text()==hr.hb.memory_model(original,buffers,1),'HR1 HB1 delay differs')
            else:require(digest(run/fn)==sha,'HR1 copied fixture changed')
        require((run/'hct377.sv').read_text()==hr.MODEL.read_text(),'HR1 cell differs')
        for fn,sha in r['model_hashes'].items():require(digest(run/fn)==sha,'HR1 HDL hash differs')
        rows=[]
        for line in log.splitlines():
            if line.startswith('HR1_SUMMARY '):
                fields=line.split();rows.append(dict(instance=fields[1],**{k:float(v) for k,v in (f.split('=') for f in fields[2:])}))
        require(rows==r['timing'],'HR1 timing log differs')
        if fault:require('RG1 stored state' in log,'HR1 missing register fault')
        else:
            require(r['marker'] in log and 'FATAL' not in log,'HR1 incomplete diagnostic')
            require(len(rows)==(4 if kind=='registers' else 2 if kind=='alu' else 6),'HR1 timing instance coverage')
            for row in rows:
                require(row['captures']>0,'HR1 inactive target')
                for key in minima:minima[key]=min(minima[key],row[key])
            require(not re.search(r'TIMING_SUMMARY .*violations=[1-9]',log),'HR1 inherited timing violation')
            if kind=='boot':
                require('PASS TX1 CPU received=5' in log and 'PASS TB1 ROM reconstruction' in log,'HR1 incomplete ROM/text boot')
                m=re.search(r'PASS TX1 CPU received=5 reads=\d+ setup_ns=([\d.]+) hold_ns=([\d.]+)',log)
                require(m and float(m[1])>=10 and float(m[2])>0,'HR1 CPU/IO reserve')
    require(minima['data_setup']>=10 and minima['enable_setup']>=10,'HR1 sampled setup reserve')
    require(all(minima[k]>0 for k in ('data_hold','enable_hold','high_pulse','low_pulse')),'HR1 sampled hold/pulse reserve')
    return dict(summary=summary,loads=inventory,sampled_minimum_reserve_ns=minima,physical_qualification=False)


def verify(lock,build=BUILD):
    require(lock.get('revision')=='CP1-HR1' and lock.get('physical_qualification') is False,'Invalid HR1 scope')
    required=set(SOURCES)|{str(p.relative_to(ROOT)) for p in hr.CANONICAL.glob('*.kicad_sch')}
    require(required<=lock['source_hashes'].keys(),'Missing HR1 source')
    required={PREFIX+n for n in ('summary.json','loads.json','bindings.json','buffer-bindings.json','path-review.json')}
    required|=set(paths.SOURCES.values())
    required|=LEGACY_INPUTS
    for sub in ('native',*hr.NATIVE_FAULTS):
        required|={PREFIX+sub+'/'+n for n in ('HR1.xml',*hr.Candidate().documents())}
    folder=build/PREFIX;summary=json.loads((folder/'summary.json').read_text())
    for name,r in [('model-'+k,v) for k,v in summary['model_tests'].items()]+list(summary['results'].items()):
        required|={PREFIX+name+'/'+n for n in ('result.json','compile.log','simulation.log',*r['model_hashes'])}
        required|={PREFIX+name+'/'+n.rsplit('/',1)[-1] for n in r.get('input_hashes',{})}
        required|=set(r.get('input_hashes',{}))
    require(required<=lock['artifacts'].keys(),'Missing HR1 artifact')
    for root,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            p=(root/name).resolve();require(p.is_relative_to(root.resolve()) and p.is_file() and digest(p)==sha,'Changed HR1 evidence: '+name)
    hr.he.load(build)
    return replay(build)


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

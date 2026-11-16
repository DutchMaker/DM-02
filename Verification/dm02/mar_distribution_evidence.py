"""MD1 native isolation, conditional loading and affected simulation replay."""
import json
import re
from .common import ROOT,VROOT,BUILD,digest
from . import mar_distribution as md,mar_distribution_sim as sim,link_loads_evidence as lle,text_boot_evidence

LOCK=VROOT/'mar-distribution-evidence.json'
SOURCES=sim.SOURCES+['Verification/dm02/mar_distribution_evidence.py','Verification/link-loads-evidence.json',
    'Verification/connector-assembly-evidence.json']
PREFIX='cp1-mar-distribution/'
require=md.require


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-MD1' and lock['physical_qualification'] is False,'Invalid MD1 scope')
    required=set(SOURCES)
    required|={str(p.relative_to(ROOT)) for folder in (md.CANONICAL,md.ca.CANONICAL) for p in folder.glob('*.kicad_sch')}
    require(required<=lock['source_hashes'].keys(),'Missing MD1 source')
    artifacts={PREFIX+'final/'+n for n in ('summary.json','loads.json','bindings.json','canonical.xml','canonical-comparison.json')}
    for name in ('native',*md.FAULTS):
        artifacts|={PREFIX+'final/'+name+'/'+n for n in ('MD1.xml','comparison.json','provenance.json','export.log')}
        artifacts|={PREFIX+'final/'+name+'/'+p.name for p in md.CANONICAL.glob('*.kicad_sch')}
    runs=('all-addresses','swapped-address','disabled-buffer','boot-guarded-max','boot-zero','boot-mixed2','boot-mixed3','boot-swapped','memory')
    artifacts.add(PREFIX+'simulation-1/matrix.json')
    for run in runs:
        artifacts|={PREFIX+'simulation-1/'+run+'/'+n for n in ('result.json','simulation.log','compile.log')}
    require(artifacts<=lock['artifacts'].keys(),'Missing MD1 artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            p=(base/name).resolve();require(p.is_relative_to(base.resolve()),'MD1 path escape')
            require(p.is_file() and digest(p)==sha,'Changed MD1 evidence: '+name)
    lle.load(build);text_boot_evidence.load(build);candidate=md.Candidate();folder=build/PREFIX
    summary=json.loads((folder/'final/summary.json').read_text())
    for name,fault in [('native',None)]+[(f,f) for f in md.FAULTS]:
        run=folder/'final'/name
        for file,text in candidate.documents(fault).items():
            require((run/file).read_text()==text,'MD1 native regeneration differs: '+file)
            if fault is None:require((md.CANONICAL/file).read_text()==text,'MD1 canonical file differs: '+file)
        actual=candidate.compare(run/'MD1.xml')
        require(actual==json.loads((run/'comparison.json').read_text()),'MD1 native result differs')
        require(actual==(summary['native'] if fault is None else summary['mutations'][fault]),'MD1 native matrix differs')
        require(actual['passed']==(fault is None),'Unexpected MD1 native parity')
    canonical=candidate.compare(folder/'final/canonical.xml')
    require(canonical['passed'] and canonical==json.loads((folder/'final/canonical-comparison.json').read_text()),'MD1 canonical export differs')
    bindings=candidate.bindings(folder/'final/native/MD1.xml')
    require(bindings==json.loads((folder/'final/bindings.json').read_text()),'MD1 buffer transfer bindings differ')
    loads=md.LoadInventory(candidate,folder/'final/native/MD1.xml').audit(candidate)
    require(loads==json.loads((folder/'final/loads.json').read_text()),'MD1 load replay differs')
    matrix=json.loads((folder/'simulation-1/matrix.json').read_text())
    require(set(matrix['results'])==set(runs[3:]),'Incomplete MD1 affected simulation matrix')
    require(set(matrix['mutations'])=={'swapped-address','disabled-buffer'},'Incomplete MD1 address fault matrix')
    for name in runs:
        run=folder/'simulation-1'/name;r=json.loads((run/'result.json').read_text())
        fault='swapped-address' if name in ('swapped-address','boot-swapped') else 'disabled-buffer' if name=='disabled-buffer' else None
        arcs=candidate.bindings(folder/'final'/fault/'MD1.xml') if fault else bindings
        require(r['bindings']==arcs,'MD1 simulation not bound to native pins')
        require(r['passed']==(fault is None) and r['physical_qualification'] is False,'Unexpected MD1 simulation result')
        if name=='all-addresses':require(matrix['exhaustive']==r,'MD1 exhaustive matrix differs')
        elif name in matrix['mutations']:require(matrix['mutations'][name]==r,'MD1 address mutation matrix differs')
        if name in matrix['results']:
            require(matrix['results'][name]==r,'MD1 saved simulation differs')
            require(set(r['input_hashes'])<=lock['artifacts'].keys(),'Missing MD1 original simulation dependency')
            for source,sha in r['input_hashes'].items():require(digest(build/source)==sha,'Changed MD1 model input')
            for source,sha in r['source_hashes'].items():require(digest(ROOT/source)==sha,'Changed MD1 simulation source')
            for file,sha in r['model_hashes'].items():require(digest(run/file)==sha,'Changed MD1 emitted model')
            model='module.sv' if name=='memory' else 'ME1.sv';profile=1 if name=='memory' else r['buffer_profile']
            original=next(p for p in r['input_hashes'] if p.endswith('/'+model))
            require((run/model).read_text()==sim.memory_model((build/original).read_text(),arcs,profile),'MD1 inserted buffer model differs')
            # Every other model/fixture must remain the actual pinned baseline file.
            for source,sha in r['input_hashes'].items():
                file=source.rsplit('/',1)[1]
                if file!=model:require(digest(run/file)==sha,'MD1 unrelated model or fixture changed')
        log=(run/'simulation.log').read_text()
        if fault:require('FATAL' in log,'MD1 fault did not fail electrically/functionally')
        elif name=='memory':require('DONE memory-io' in log,'Missing MD1 memory completion')
        elif name=='all-addresses':require('PASS MD1 all 65536 address words' in log,'Missing MD1 exhaustive completion')
        else:
            require('PASS TB1 ROM reconstruction' in log and 'PASS TX1 CPU received=5' in log,'Missing MD1 ROM/text proof')
            require(not sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log))),'MD1 timing violations')
    return dict(native=summary,loads=loads,simulations=matrix,physical_qualification=False)


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

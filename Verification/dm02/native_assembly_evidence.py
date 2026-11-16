"""Bounded replay of NA1 hierarchy, component metadata and wiring mutations."""
import json
from .common import ROOT,VROOT,BUILD,digest
from . import native_assembly,text_boot_evidence

LOCK=VROOT/'native-assembly-evidence.json'
PREFIX='cp1-native-assembly/'
CANONICAL=ROOT/'Circuits/KiCad/Integrated/candidates/NA1'
FAULTS=('merged-reset','stale-read-address','private-return-alias')
require=native_assembly.require


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-NA1' and lock['physical_qualification'] is False,'Invalid NA1 scope')
    required=set(native_assembly.SOURCES)|{'Verification/dm02/native_assembly_evidence.py'}
    required|={str((CANONICAL/(b+'.kicad_sch')).relative_to(ROOT)) for b in (*native_assembly.BOARDS,'NA1')}
    require(required<=lock['source_hashes'].keys(),'Missing NA1 source')
    artifacts={PREFIX+'final/summary.json',PREFIX+'iteration-1/metadata-recheck.json',
        PREFIX+'final/canonical.xml',PREFIX+'final/canonical-comparison.json',PREFIX+'final/native/model-bindings.json'}
    for name in ('native',*FAULTS):
        artifacts|={PREFIX+'final/'+name+'/'+file for file in ('NA1.xml','comparison.json','provenance.json','export.log')}
        artifacts|={PREFIX+'final/'+name+'/'+b+'.kicad_sch' for b in (*native_assembly.BOARDS,'NA1')}
    require(artifacts<=lock['artifacts'].keys(),'Missing NA1 artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            p=(base/name).resolve();require(p.is_relative_to(base.resolve()),'NA1 path escape')
            require(p.is_file() and digest(p)==sha,'Changed NA1 evidence: '+name)
    text_boot_evidence.load(build)
    # Assembly reads the original restored native dependencies, all pinned above.
    a=native_assembly.Assembly();require(a.hashes.items()<=lock['artifacts'].items(),'Missing NA1 native dependency')
    folder=build/PREFIX;summary=json.loads((folder/'final/summary.json').read_text())
    require(summary['revision']=='CP1-NA1' and summary['accepted_revision']=='CP1-R2' and
        summary['physical_qualification'] is False and summary['promoted_into_R2'] is False,'NA1 summary scope changed')
    require(set(summary['mutations'])==set(FAULTS),'Incomplete NA1 mutation matrix')
    for name,fault in [('native',None)]+[(f,f) for f in FAULTS]:
        run=folder/'final'/name
        for file,text in a.documents(fault).items():
            require((run/file).read_text()==text,'NA1 native regeneration differs: '+file)
            if fault is None:require((CANONICAL/file).read_text()==text,'NA1 canonical source differs: '+file)
        require(json.loads((run/'provenance.json').read_text())==a.source_manifest(),'NA1 provenance differs')
        result=dict(a.compare(run/'NA1.xml'),fault=fault)
        require(result==json.loads((run/'comparison.json').read_text()),'NA1 saved comparison differs')
        require(result==(summary['native'] if fault is None else summary['mutations'][fault]),'NA1 matrix disagrees')
        require(result['passed']==(fault is None),'Unexpected NA1 parity result')
        if fault:require(result['differences'] and result['component_identity_match'] and
                         result['symbol_pin_metadata_match'],'NA1 mutation failed for wrong reason')
    binding=a.model_bindings(folder/'final/native/NA1.xml')
    require(binding==json.loads((folder/'final/native/model-bindings.json').read_text()),'NA1 model binding differs')
    canonical=a.compare(folder/'final/canonical.xml')
    require(canonical['passed'] and canonical==json.loads((folder/'final/canonical-comparison.json').read_text()),'NA1 canonical export differs')
    first=a.compare(folder/'iteration-1/native/NA1.xml')
    require(first==json.loads((folder/'iteration-1/metadata-recheck.json').read_text()) and
            first['passed'] is False and first['symbol_pin_metadata_match'] is False and
            not first['differences'],'NA1 preserved library collision is not detected')
    return summary,binding


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());summary,binding=verify(lock,build)
    return lock,summary,binding

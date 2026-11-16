"""Fail-closed CA1 separate-card and analytically mated native graph replay."""
import json
from .common import ROOT,VROOT,BUILD,digest
from . import connector_assembly as ca,native_assembly_evidence as nae

LOCK=VROOT/'connector-assembly-evidence.json'
PREFIX='cp1-connector-assembly/'
require=ca.require


def verify(lock,build=BUILD):
    require(lock['revision']=='CP1-CA1' and lock['physical_qualification'] is False,'Invalid CA1 scope')
    required=set(ca.SOURCES)|{'Verification/dm02/connector_assembly_evidence.py'}
    required|={str(p.relative_to(ROOT)) for p in nae.CANONICAL.glob('*.kicad_sch')}
    required|={str((ca.CANONICAL/(b+'.kicad_sch')).relative_to(ROOT)) for b in (*ca.na.BOARDS,'CN1','CA1')}
    require(required<=lock['source_hashes'].keys(),'Missing CA1 source')
    artifacts={PREFIX+'final/summary.json',PREFIX+'final/canonical.xml',PREFIX+'final/canonical-comparison.json'}
    for name in ('native',*ca.FAULTS):
        artifacts|={PREFIX+'final/'+name+'/'+file for file in ('CA1.xml','comparison.json','provenance.json','export.log')}
        artifacts|={PREFIX+'final/'+name+'/'+b+'.kicad_sch' for b in (*ca.na.BOARDS,'CN1','CA1')}
    require(artifacts<=lock['artifacts'].keys(),'Missing CA1 artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            p=(base/name).resolve();require(p.is_relative_to(base.resolve()),'CA1 path escape')
            require(p.is_file() and digest(p)==sha,'Changed CA1 evidence: '+name)
    nae.load(build);a=ca.Assembly();folder=build/PREFIX
    summary=json.loads((folder/'final/summary.json').read_text())
    require(summary['revision']=='CP1-CA1' and summary['accepted_revision']=='CP1-R2' and
        summary['physical_qualification'] is False and summary['promoted_into_R2'] is False and
        summary['new_dynamic_simulation'] is False,'CA1 summary scope changed')
    require(set(summary['mutations'])==set(ca.FAULTS),'Incomplete CA1 mutation matrix')
    for name,fault in [('native',None)]+[(f,f) for f in ca.FAULTS]:
        run=folder/'final'/name
        for file,text in a.documents(fault).items():
            require((run/file).read_text()==text,'CA1 regeneration differs: '+file)
            if fault is None:require((ca.CANONICAL/file).read_text()==text,'CA1 canonical source differs: '+file)
        require(json.loads((run/'provenance.json').read_text())==a.provenance(),'CA1 provenance differs')
        result=dict(a.compare(run/'CA1.xml'),fault=fault)
        require(result==json.loads((run/'comparison.json').read_text()),'CA1 saved comparison differs')
        require(result==(summary['native'] if fault is None else summary['mutations'][fault]),'CA1 matrix differs')
        require(result['passed']==(fault is None),'Unexpected CA1 parity result')
        if fault:
            require(result['component_identity_match'] and result['unmated_differences'],'CA1 mutation failed for wrong reason')
            require(bool(result['mated_functional_differences'])==(fault!='global-bypass'),'CA1 mated mutation result changed')
    canonical=a.compare(folder/'final/canonical.xml')
    require(canonical['passed'] and canonical==json.loads((folder/'final/canonical-comparison.json').read_text()),'CA1 canonical export differs')
    return summary


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

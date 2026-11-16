"""Fail-closed replay of LL1 physical-pin accounting and conditional load screens."""
import json
from .common import ROOT,VROOT,BUILD,digest
from . import link_loads as ll,connector_assembly_evidence as cae

LOCK=VROOT/'link-loads-evidence.json'
SOURCES=['Verification/dm02/link_loads.py','Verification/dm02/link_parts.py',
    'Verification/dm02/link_loads_evidence.py','Verification/connector-assembly-evidence.json',
    'Verification/operating-contract.json']
INPUTS=['cp1-connector-assembly/final/native/CA1.xml','cp1-connector-assembly/final/native/provenance.json',
    'cp1-hct273/component-review.json','cp1-hct273/loads.json','cp1-bridge/summary.json',
    'cp1-text/final/audit.json','cp1-text/iteration-2/native/TX1/TX1.xml']


def verify(lock,build=BUILD):
    require=ll.require
    require(lock['revision']=='CP1-LL1' and lock['physical_qualification'] is False,'Invalid LL1 scope')
    require(set(SOURCES)<=lock['source_hashes'].keys(),'Missing LL1 source')
    required={*INPUTS,'cp1-link-loads/final/inventory.json','cp1-link-loads/final/mutations.json',
        'cp1-link-loads/sources/manifest.json'}
    require(required<=lock['artifacts'].keys(),'Missing LL1 artifact')
    for base,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            path=(base/name).resolve();require(path.is_relative_to(base.resolve()),'LL1 path escape')
            require(path.is_file() and digest(path)==sha,'Changed LL1 evidence: '+name)
    # Validate the upstream separated-card graph and its accepted source locks.
    cae.load(build)
    actual=json.loads((build/'cp1-link-loads/final/inventory.json').read_text())
    for part in actual['parts'].values():
        require('cp1-link-loads/'+part['source'] in lock['artifacts'],'Unpinned manufacturer excerpt')
    expected=ll.Inventory().generate();ll.validate_report(actual,expected)
    faults=json.loads((build/'cp1-link-loads/final/mutations.json').read_text())
    require(faults==ll.mutations(expected),'Changed LL1 mutation evidence')
    return actual


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)

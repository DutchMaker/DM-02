"""Pin CA1 exports, mutations and the preserved boundary-marker iteration."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import connector_assembly as ca,connector_assembly_evidence as evidence
from dm02.common import digest,write_json


def main():
    assert not evidence.LOCK.exists(),'Preserve CA1 lock'
    sources=set(ca.SOURCES)|{'Verification/dm02/connector_assembly_evidence.py',
        'Verification/build/cp1-connector-assembly/lock_evidence.py'}
    for folder in (ca.CANONICAL,ca.nae.CANONICAL):
        sources|={str(p.relative_to(ROOT)) for p in folder.glob('*.kicad_sch')}
    artifacts={str(p.relative_to(ca.BUILD)):digest(p) for name in ('final','iteration-1')
        for p in (HERE/name).rglob('*') if p.is_file()}
    lock=dict(revision='CP1-CA1',accepted_revision='CP1-R2',physical_qualification=False,
        source_hashes={n:digest(ROOT/n) for n in sorted(sources)},artifacts=dict(sorted(artifacts.items())))
    evidence.verify(lock);write_json(evidence.LOCK,lock)
    print('Pinned CA1:',len(sources),'sources;',len(artifacts),'artifacts')


if __name__=='__main__':main()

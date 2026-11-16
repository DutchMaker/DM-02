"""Lock the final NA1 export and preserve both development iterations."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import native_assembly as na,native_assembly_evidence as evidence
from dm02.common import digest,write_json


def main():
    assert not evidence.LOCK.exists(),'Preserve NA1 lock'
    a=na.Assembly()
    sources=set(na.SOURCES)|{'Verification/dm02/native_assembly_evidence.py',
        'Verification/build/cp1-native-assembly/lock_evidence.py'}
    sources|={str(p.relative_to(ROOT)) for p in evidence.CANONICAL.glob('*.kicad_sch')}
    artifacts={str(p.relative_to(na.BUILD)):digest(p) for name in ('final','iteration-1','iteration-2','iteration-3')
        for p in (HERE/name).rglob('*') if p.is_file()}
    artifacts.update(a.hashes)
    lock=dict(revision='CP1-NA1',accepted_revision='CP1-R2',physical_qualification=False,
        source_hashes={n:digest(ROOT/n) for n in sorted(sources)},artifacts=dict(sorted(artifacts.items())))
    evidence.verify(lock);write_json(evidence.LOCK,lock)
    print('Pinned NA1:',len(sources),'sources;',len(artifacts),'artifacts')


if __name__=='__main__':main()

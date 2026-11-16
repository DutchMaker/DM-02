"""Pin the LL1 inventory, earlier attempts and manufacturer excerpts."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import BUILD,digest,write_json
from dm02 import link_loads_evidence as evidence


def main():
    assert not evidence.LOCK.exists(),'Preserve LL1 lock'
    sources=evidence.SOURCES+['Verification/build/cp1-link-loads/prepare_sources.py',
        'Verification/build/cp1-link-loads/lock_evidence.py']
    paths=[BUILD/p for p in evidence.INPUTS]
    for name in ('final','iteration-1','iteration-2','sources','sources-attempt-1','sources-attempt-2','sources-attempt-3'):
        paths += [p for p in (HERE/name).rglob('*') if p.is_file()]
    lock=dict(revision='CP1-LL1',physical_qualification=False,
        source_hashes={p:digest(ROOT/p) for p in sources},
        artifacts={str(p.relative_to(BUILD)):digest(p) for p in sorted(set(paths))})
    evidence.verify(lock);write_json(evidence.LOCK,lock)
    print('Pinned LL1:',len(sources),'sources;',len(paths),'artifacts')


if __name__=='__main__':main()

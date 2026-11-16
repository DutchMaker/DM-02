"""Pin MD1 source/export/load checks and affected memory/ROM simulations."""
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import BUILD,digest,write_json
from dm02 import mar_distribution as md,mar_distribution_evidence as evidence


def main():
    assert not evidence.LOCK.exists(),'Preserve MD1 lock'
    sources=set(evidence.SOURCES)|{'Verification/build/cp1-mar-distribution/lock_evidence.py'}
    for folder in (md.CANONICAL,md.ca.CANONICAL):sources|={str(p.relative_to(ROOT)) for p in folder.glob('*.kicad_sch')}
    paths=[p for name in ('iteration-1','final','simulation-1','failed-regression-1') for p in (HERE/name).rglob('*') if p.is_file()]
    matrix=json.loads((HERE/'simulation-1/matrix.json').read_text())
    paths += [BUILD/name for r in matrix['results'].values() for name in r['input_hashes']]
    paths=sorted(set(paths))
    lock=dict(revision='CP1-MD1',physical_qualification=False,source_hashes={p:digest(ROOT/p) for p in sorted(sources)},
        artifacts={str(p.relative_to(BUILD)):digest(p) for p in sorted(paths)})
    evidence.verify(lock);write_json(evidence.LOCK,lock)
    print('Pinned MD1:',len(sources),'sources;',len(paths),'artifacts')


if __name__=='__main__':main()

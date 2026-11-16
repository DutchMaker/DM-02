"""Archive RR1 inputs, accepted experiments and preserved compile failure."""
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import BUILD,digest,write_json
from dm02 import release_evidence as evidence


def main():
    assert not evidence.LOCK.exists(),'Preserve RR1 lock'
    write_json(HERE/'summary.json',evidence.summary())
    sources=set(evidence.SOURCES)|{'Verification/build/cp1-release/lock_evidence.py'}
    paths={p for name in ('iteration-1','iteration-2','replay-draft-1') for p in (HERE/name).rglob('*') if p.is_file()}
    paths.add(HERE/'summary.json')
    for result in (HERE/'iteration-2').glob('*/result.json'):
        paths|={BUILD/name for name in json.loads(result.read_text())['input_hashes']}
    for name in ('sn74hct245.txt','um61512a.txt','sn74ahct244.txt','sn74ahct04.txt','sn74ahct08.txt','sn74ahct00.txt','sn74ahct32.txt','manifest.json'):
        paths.add(BUILD/'cp1-link-loads/sources'/name)
    paths.add(BUILD/'sram-turnaround/review.json');paths.add(BUILD/'sram-turnaround/review.py')
    lock=dict(revision='CP1-RR1',physical_qualification=False,
        source_hashes={n:digest(ROOT/n) for n in sorted(sources)},
        artifacts={str(p.relative_to(BUILD)):digest(p) for p in sorted(paths)})
    evidence.verify(lock);write_json(evidence.LOCK,lock)
    print('Pinned RR1',len(lock['artifacts']),'artifacts')


if __name__=='__main__':main()

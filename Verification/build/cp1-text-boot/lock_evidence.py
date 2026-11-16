"""Pin completed TB1 runs and preserved elaboration failures, without rerunning."""
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import text_boot,text_boot_evidence
from dm02.common import digest,write_json


def main():
    assert not text_boot_evidence.LOCK.exists(),'Preserve accepted TB1 evidence lock'
    matrix=json.loads((HERE/'matrix.json').read_text())
    sources=set(text_boot.SOURCES)|{'Verification/dm02/text_boot_evidence.py',
        'Verification/build/cp1-text-boot/run_study.py','Verification/build/cp1-text-boot/lock_evidence.py'}
    artifacts={str(p.relative_to(text_boot.BUILD)):digest(p) for name in [*matrix['results'],'initial-max','max']
        for p in (HERE/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    artifacts['cp1-text-boot/matrix.json']=digest(HERE/'matrix.json')
    for result in matrix['results'].values():
        assert all(digest(ROOT/n)==h for n,h in result['source_hashes'].items())
        artifacts.update(result['input_hashes'])
    lock=dict(revision='CP1-TB1',accepted_revision='CP1-R2',physical_qualification=False,
        source_hashes={n:digest(ROOT/n) for n in sorted(sources)},artifacts=dict(sorted(artifacts.items())))
    text_boot_evidence.verify(lock)
    write_json(text_boot_evidence.LOCK,lock)
    print('Pinned TB1:',len(sources),'sources,',len(artifacts),'artifacts')


if __name__=='__main__':main()

"""Promote ACH staging only after the preceding normal run is archived."""
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    live=ROOT/'Verification/build/report.json';report=read(live)
    assert report['state']=='complete' and not any(r['status']=='error' for r in report['checks'])
    archive=ROOT/'Verification/build/experiments/2026-11-15-analog-integrated'
    assert sha(archive/'report.json')==sha(live)
    assert read(archive/'remote-validation.json')['passed'] and read(archive/'browser-check.json')['passed']
    for name in ('summary.json','remote-validation.json','browser-check.json'):assert read(HERE/name)['passed']
    for relative,row in read(HERE/'manifest.json')['files'].items():assert sha(HERE/relative)==row['sha256'],relative
    sources=read(HERE/'source-manifest.json')
    assert sources['baseline']==report['source_hashes']
    for relative,digest in sources['baseline'].items():assert sha(ROOT/relative)==digest,relative
    for relative,digest in sources['candidate'].items():assert sha(HERE/'candidate'/relative)==digest,relative
    for relative in sources['changed']:
        if relative not in sources['baseline']:assert not (ROOT/relative).exists(),relative
    for relative,digest in sources['changed'].items():
        target=ROOT/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(HERE/'candidate'/relative,target);assert sha(target)==digest
    (HERE/'promotion.json').write_text(json.dumps(dict(promoted=True,files=sources['changed'],
        previous_report_sha256=sha(live)),indent=2)+'\n')
    print('Promoted',len(sources['changed']),'ACH integration inputs; fresh normal verification required')


if __name__=='__main__':main()

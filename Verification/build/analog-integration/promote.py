"""Promote validated staging only after the preceding run has been archived."""
import json
from pathlib import Path
import shutil
from publish import HERE, ROOT, CANDIDATE, sha, read, write


def main():
    live=ROOT/'Verification/build/report.json'; report=read(live)
    assert report['state']=='complete','Wait for the original full-run completion event'
    assert not any(row['status']=='error' for row in report['checks']),'Review full-run harness errors first'
    archived=ROOT/'Verification/build/experiments/2026-11-15-refreshed-complete'
    assert sha(archived/'report.json')==sha(live),'Archive the complete original run before promotion'
    assert read(archived/'remote-validation.json')['passed'],'Verify the remote archive before promotion'
    assert read(HERE/'remote-validation.json')['passed'],'Verify the staged publication before promotion'
    assert read(HERE/'browser-check.json')['passed'],'Check staged desktop/mobile publication before promotion'
    manifest=read(HERE/'manifest.json')['files']
    for relative,row in manifest.items():assert sha(HERE/relative)==row['sha256'],relative
    sources=read(HERE/'source-manifest.json')
    assert sources['baseline']==report['source_hashes']
    for relative,digest in sources['baseline'].items():
        assert sha(ROOT/relative)==digest,'Normal source changed: '+relative
    for relative,digest in sources['candidate'].items():
        assert sha(CANDIDATE/relative)==digest,'Staged source changed: '+relative
    for relative in sources['changed']:
        if relative not in sources['baseline']:
            assert not (ROOT/relative).exists(),'Unrelated new source: '+relative
    # All preconditions are verified before the first normal input is changed.
    for relative,digest in sources['changed'].items():
        target=ROOT/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(CANDIDATE/relative,target)
        assert sha(target)==digest
    write(HERE/'promotion.json',dict(promoted=True,files=sources['changed'],previous_report_sha256=sha(live)))
    print('Promoted',len(sources['changed']),'validated sources. A fresh normal run is required.')


if __name__=='__main__':main()

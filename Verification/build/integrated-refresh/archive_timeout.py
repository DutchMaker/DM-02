"""Preserve the completed analogue run with its ALU-sequence timeout intact."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BUILD=HERE.parent
TARGET=BUILD/'experiments/2026-11-15-analog-timeout'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import freshness


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def main():
    live=BUILD/'report.json';raw=live.read_bytes();report=json.loads(raw)
    assert report['state']=='complete' and freshness(report)['fresh']
    errors=[r for r in report['checks'] if r['status']=='error']
    assert len(errors)==1 and errors[0]['id']=='alu-sequences'
    assert 'timed out after 180 seconds' in errors[0]['summary']
    assert not TARGET.exists(),'Refuse to overwrite a preserved run'
    inputs=[(live,'report.json',sha(live))]
    inputs += [(ROOT/p,'sources/'+p,h) for p,h in report['source_hashes'].items()]
    inputs += [(BUILD/p,p,h) for p,h in report['artifact_hashes'].items()]
    rows={}
    for source,relative,digest in inputs:
        assert sha(source)==digest,str(source)
        target=TARGET/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target);assert sha(target)==digest
        rows[relative]=dict(bytes=target.stat().st_size,sha256=digest)
    assert live.read_bytes()==raw and freshness(report)['fresh']
    counts=dict(Counter(r['status'] for r in report['checks']))
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),report_sha256=sha(live),
        source_files=len(report['source_hashes']),artifact_files=len(report['artifact_hashes']),
        status_counts=counts,errors=errors,milestones=[dict(passed=m['passed'],total=m['total']) for m in report['milestones']],
        acceptance_complete=False,local_hashes_verified=True,
        stale_failed_stage_artifacts=['alu/sequences/coverage.json','alu/sequences/slice.log'],
        scope='Failed run preserved without repair. ALU-sequence log and coverage predate this run; they are retained for provenance, not acceptance. The report correctly records an execution error.')
    write(TARGET/'archive.json',summary)
    (TARGET/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · analogue run timeout</title><link rel="icon" href="data:,">
<style>:root{color-scheme:dark}body{margin:24px auto;padding:0 16px;max-width:900px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}a{color:#8acfff;overflow-wrap:anywhere}.error{color:#ffad9f}</style>
<nav><a href="/">Live dashboard</a></nav><h1>Analogue-integrated run: ALU-sequence timeout</h1>
<p class="error">This run ended with a harness error. It is preserved as a failed run.</p>
<p>The ALU-sequence simulator exceeded its 180-second limit. Fresh nominal analogue evidence, FD1, boot execution and all 155 regressions passed. Counts: 22 pass, 16 limited, six blocked, one baseline timing failure and one harness error. Milestones: 3/5, 3/5, 7/9.</p>
<p>The ALU-sequence coverage and slice log predate this run. Their archived bytes preserve the original state and are not current acceptance evidence. The error is retained in the report.</p>
<p><a href="report.json">Original report</a> · <a href="alu-sequences-error.log">Timeout traceback</a> · <a href="archive.json">Archive scope</a> · <a href="manifest.json">File hashes</a> · <a href="remote-validation.json">Remote verification</a></p></html>''')
    for name in ('archive.json','index.html'):
        path=TARGET/name;rows[name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    write(TARGET/'manifest.json',dict(created_at=summary['created_at'],files=rows))
    print('Preserved failed run:',len(rows),'files;',counts)


if __name__=='__main__':main()

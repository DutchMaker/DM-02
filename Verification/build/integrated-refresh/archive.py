"""Freeze the completed normal run that includes fresh PILOT-03 evidence."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
BUILD=HERE.parent
ROOT=HERE.parents[2]
TARGET=BUILD/'experiments/2026-11-15-analog-integrated'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import freshness


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def copy_checked(source,dest,expected):
    assert sha(source)==expected,str(source)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==expected,'Archive collision: '+str(dest)
    else:shutil.copyfile(source,dest)
    assert sha(dest)==expected


def main():
    live=BUILD/'report.json';raw=live.read_bytes();report=json.loads(raw)
    assert report['state']=='complete' and report.get('finished_at')
    assert freshness(report)['fresh']
    by_id={r['id']:r for r in report['checks']}
    assert not any(r['status']=='error' for r in report['checks'])
    assert [r['id'] for r in report['checks'] if r['status']=='fail']==['timing']
    assert [(m['passed'],m['total']) for m in report['milestones']]==[(3,5),(3,5),(8,9)]
    assert by_id['analog']['status']=='pass' and by_id['analog-rc']['status']=='limited'
    assert by_id['harness']['status']=='pass' and '155 tests executed' in by_id['harness']['summary']
    acceptance=read(BUILD/'analog/loaded/acceptance.json')
    assert acceptance['requirement_status']=='pass'
    assert not acceptance['full_operating_envelope_qualified'] and not acceptance['physical_clock_qualified']
    assert acceptance['checks']==by_id['analog']['checks']
    assert all(report['source_hashes'][p]==h for p,h in acceptance['source_hashes'].items())
    experiment=read(BUILD/'analog/loaded/experiment.json')
    assert report['started_at']<=experiment['created_at']<=report['finished_at'],'Analogue evidence must come from this run'
    assert len([p for p in report['artifact_hashes'] if p.startswith('analog/loaded/traces/') and p.endswith('.csv')])==10
    TARGET.mkdir(parents=True,exist_ok=True)
    report_hash=hashlib.sha256(raw).hexdigest()
    lock=TARGET/'snapshot-lock.json'
    if lock.exists():assert read(lock)['report_sha256']==report_hash
    else:write(lock,dict(report_sha256=report_hash))
    copy_checked(live,TARGET/'report.json',report_hash)
    for relative,digest in report['source_hashes'].items():
        source=ROOT/relative;assert source.resolve().is_relative_to(ROOT) and not Path(relative).is_absolute()
        copy_checked(source,TARGET/'sources'/relative,digest)
    for relative,digest in report['artifact_hashes'].items():
        source=BUILD/relative;assert source.resolve().is_relative_to(BUILD) and not Path(relative).is_absolute()
        copy_checked(source,TARGET/relative,digest)
    assert live.read_bytes()==raw and freshness(report)['fresh']
    counts=dict(Counter(r['status'] for r in report['checks']))
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),report_finished_at=report['finished_at'],
        report_sha256=report_hash,source_files=len(report['source_hashes']),artifact_files=len(report['artifact_hashes']),
        status_counts=counts,milestones=report['milestones'],analog=acceptance,local_hashes_verified=True)
    write(TARGET/'archive.json',summary)
    rows=''.join(f'<tr><td>{html.escape(r["title"])}</td><td>{r["status"]}</td><td>{html.escape(r["summary"])}<p>'+
        ' · '.join(f'<a href="{html.escape(p,quote=True)}">{html.escape(p)}</a>' for p in r.get('artifacts',[]))+'</p></td></tr>' for r in report['checks'])
    (TARGET/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · integrated analogue full run</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1150px;margin:auto;padding:24px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%;table-layout:fixed}}th,td{{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}th:first-child{{width:20%}}th:nth-child(2){{width:10%}}.pass{{color:#88e2b0}}@media(max-width:700px){{td,th{{padding:4px;font-size:12px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../2026-11-15-refreshed-complete/">Previous complete run</a> · <a href="../../analog-integration/">Staging validation</a></nav>
<h1>Analogue experiment integrated into the full run</h1><p id="verdict" class="pass">PILOT-03 passes from fresh normal-run execution. Milestone 2 advances to 3/5 accepted gates. All 155 regression tests pass.</p>
<p>Completed {report['finished_at']}. {summary['source_files']} sources and {summary['artifact_files']} artifacts are archived with hashes. The nominal 5 V / 25 °C loaded-output experiment has {acceptance['checks']['minimum_setup_margin_ns']:.3f} ns minimum margin; nine faults were detected. Physical/full-envelope qualification remains open under PILOT-05.</p>
<p>{counts.get('pass',0)} pass · {counts.get('limited',0)} limited · {counts.get('blocked',0)} blocked · {counts.get('fail',0)} documented baseline timing failure · {counts.get('error',0)} harness errors.</p>
<nav><a href="report.json">Full report</a> · <a href="archive.json">Archive summary</a> · <a href="manifest.json">All hashes</a> · <a href="remote-validation.json">Remote verification</a></nav>
<table id="checks"><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></main></html>''')
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','live-desktop.png','live-mobile.png'}
    files={str(p.relative_to(TARGET)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(TARGET.rglob('*'))
        if p.is_file() and not(p.parent==TARGET and p.name in excluded)}
    write(TARGET/'manifest.json',dict(created_at=summary['created_at'],files=files))
    print('Archived',summary['source_files'],'sources and',summary['artifact_files'],'artifacts;',counts)


if __name__=='__main__':main()

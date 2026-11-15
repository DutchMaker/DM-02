"""Freeze a completed, fresh normal run; refuse changed or mixed evidence."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import html
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BUILD=HERE.parent
TARGET=BUILD/'experiments/2026-11-15-refreshed-complete'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import freshness


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_checked(source,dest,expected):
    assert sha(source)==expected,f'Changed input: {source}'
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==expected,f'Archive collision: {dest}'
    else:shutil.copyfile(source,dest)
    assert sha(dest)==expected


def main():
    report_path=BUILD/'report.json';report_bytes=report_path.read_bytes()
    report=json.loads(report_bytes);report_hash=hashlib.sha256(report_bytes).hexdigest()
    assert report['state']=='complete' and report.get('finished_at'),'Normal run is incomplete'
    assert freshness(report)['fresh'],'Normal sources are stale'
    assert not any(c['status']=='error' for c in report['checks']),'Harness errors require review'
    assert [c['id'] for c in report['checks'] if c['status']=='fail']==['timing'],'Unexpected failing check'
    assert [(m['passed'],m['total']) for m in report['milestones']]==[(3,5),(2,5),(8,9)]
    TARGET.mkdir(parents=True,exist_ok=True)
    lock=TARGET/'snapshot-lock.json'
    if lock.exists():assert json.loads(lock.read_text())['report_sha256']==report_hash,'Archive already belongs to another run'
    else:lock.write_text(json.dumps(dict(report_sha256=report_hash),indent=2)+'\n')
    copy_checked(report_path,TARGET/'report.json',report_hash)
    for relative,digest in report['source_hashes'].items():
        source=ROOT/relative
        assert source.resolve().is_relative_to(ROOT) and not Path(relative).is_absolute()
        copy_checked(source,TARGET/'sources'/relative,digest)
    for relative,digest in report['artifact_hashes'].items():
        source=BUILD/relative
        assert source.resolve().is_relative_to(BUILD) and not Path(relative).is_absolute()
        copy_checked(source,TARGET/relative,digest)
    assert report_path.read_bytes()==report_bytes,'Live report changed during snapshot'
    assert freshness(report)['fresh'],'Normal sources changed during snapshot'
    counts=dict(Counter(c['status'] for c in report['checks']))
    archive=dict(created_at=datetime.now(timezone.utc).isoformat(),report_finished_at=report['finished_at'],
        report_sha256=report_hash,source_files=len(report['source_hashes']),artifact_files=len(report['artifact_hashes']),
        local_hashes_verified=True,status_counts=counts,milestones=report['milestones'],
        scope='Complete normal-run source and artifact snapshot. Physical qualification remains open.')
    (TARGET/'archive.json').write_text(json.dumps(archive,indent=2)+'\n')
    checks=''
    for check in report['checks']:
        links=' · '.join(f'<a href="{html.escape(p,quote=True)}">{html.escape(p)}</a>' for p in check.get('artifacts',[]))
        checks+=f'<tr><td>{html.escape(check["title"])}</td><td>{check["status"]}</td><td>{html.escape(check["summary"])}<p>{links}</p></td></tr>'
    milestones=''.join(f'<li>{html.escape(m["title"])}: {m["passed"]}/{m["total"]}. {html.escape(m["summary"])}</li>' for m in report['milestones'])
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · refreshed full-system archive</title><link rel="icon" href="data:,"><style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1150px;margin:auto;padding:25px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%;table-layout:fixed}}th,td{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}th:first-child{{width:20%}}th:nth-child(2){{width:10%}}.notice{{color:#ffd082}}@media(max-width:700px){{td,th{{padding:5px;font-size:12px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../../clock-ach/">Isolated ACH oscillator candidate</a> · <a href="../../cd1-decoupling/">P3 placement study</a></nav>
<h1>Refreshed full-system archive</h1><p>Completed {report['finished_at']}. This snapshot includes the repaired schematic footprints and current dashboard sources: {archive['source_files']} source files and {archive['artifact_files']} verification artifacts.</p>
<p>{counts.get('pass',0)} pass · {counts.get('limited',0)} limited · {counts.get('blocked',0)} blocked · {counts.get('fail',0)} documented baseline timing failure · {counts.get('error',0)} harness errors.</p>
<p class="notice">Functional and conditional timing evidence is preserved here. Exact assembly, oscillator/reset, SRAM turnaround, PCB loads and physical qualification remain open.</p><ul>{milestones}</ul>
<nav><a href="report.json">Full report</a> · <a href="archive.json">Snapshot summary</a> · <a href="manifest.json">All archive hashes</a> · <a href="remote-validation.json">Remote validation</a></nav>
<table id="checks"><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table></main></html>'''
    (TARGET/'index.html').write_text(page)
    # Files nested inside source/artifact trees can legitimately have those
    # names; only publication metadata at the archive root is excluded.
    files={str(p.relative_to(TARGET)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(TARGET.rglob('*')) if p.is_file()
        and not(p.parent==TARGET and p.name in ('manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'))}
    (TARGET/'manifest.json').write_text(json.dumps(dict(created_at=archive['created_at'],files=files),indent=2)+'\n')
    print('Archived',archive['source_files'],'sources and',archive['artifact_files'],'artifacts;',counts)


if __name__=='__main__':main()

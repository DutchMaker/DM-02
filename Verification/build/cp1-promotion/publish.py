"""Freeze this promotion's new evidence; retain links to immutable prior releases."""
from pathlib import Path
import hashlib
import html
import json
import shutil

BUILD=Path(__file__).resolve().parents[1]
HERE=BUILD/'cp1-promotion'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    report=json.loads((BUILD/'report.json').read_text())
    assert report['target']=='cp1' and report['state']=='complete'
    assert not any(c['status']=='error' for c in report['checks'])
    HERE.mkdir(exist_ok=True)
    for name in ('equivalence.json','equivalence.log','smoke.log'):
        shutil.copyfile(BUILD/'cp1'/name,HERE/name)
    shutil.copyfile(BUILD/'tests.log',HERE/'tests.log')
    shutil.copyfile(BUILD/'report.json',HERE/'original-report.json')
    if Path(__file__).resolve() != (HERE/'publish.py').resolve():
        shutil.copyfile(Path(__file__),HERE/'publish.py')
    mapping={'cp1/'+n:'cp1-promotion/'+n for n in ('equivalence.json','equivalence.log','smoke.log')}
    mapping['tests.log']='cp1-promotion/tests.log'
    report['artifact_hashes']={mapping.get(n,n):v for n,v in report['artifact_hashes'].items()}
    for c in report['checks']:
        c['artifacts']=[mapping.get(n,n) for n in c.get('artifacts',[])]
    report['equivalence']['fresh_smoke']['log']='cp1-promotion/smoke.log'
    report['archival_scope']='New promotion evidence copied here; reused CP1 and reference evidence remains pinned in its original immutable release directories. original-report.json preserves the live report verbatim.'
    (HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    rows=''.join(f'<tr><td>{m["number"]}</td><td>{html.escape(m["title"])}</td><td>{m["passed"]}/{m["total"]}</td></tr>' for m in report['milestones'])
    checks=''.join(f'<li><strong>{html.escape(c["status"])}: {html.escape(c["title"])}</strong><p>{html.escape(c["summary"])}</p>'+''.join(f'<a href="/build/{html.escape(p,quote=True)}">{html.escape(Path(p).name)}</a> ' for p in c.get('artifacts',[]))+'</li>' for c in report['checks'])
    (HERE/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 CP1 active verification</title>
<style>body{max-width:960px;margin:40px auto;padding:0 20px;background:#101923;color:#e6edf3;font:16px/1.6 system-ui}a{color:#63dfdc;overflow-wrap:anywhere}td,th{padding:8px;text-align:left;border-bottom:1px solid #425266}li{margin:24px 0}p{overflow-wrap:anywhere}table{width:100%}</style>
<h1>CP1 active verification</h1><p>192 DIP logic/memory packages, down from 288. The default runner now selects CP1.</p>
<p id="state">Digital acceptance replay passed. Physical qualification remains open.</p>
<p>430 source files, 446 regenerated HDL artifacts and ten clock models match the accepted snapshot. A fresh CPU integration profile and the current harness tests passed. Full boot evidence is reused from the verified CP1 release.</p>
<table id="milestones"><thead><tr><th>Milestone</th><th>Scope</th><th>Passed</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<p><a href="/">Live dashboard</a> · <a href="report.json">Archived report</a> · <a href="original-report.json">Original live report</a> · <a href="equivalence.json">Model equivalence</a> · <a href="tests.log">Harness log</a> · <a href="../compact-design/">Complete CP1 design</a> · <a href="../cp1-timing-review/">HCT273 substitution study</a></p><h2>Checks</h2><ul>'''+checks+'</ul></html>')
    files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in HERE.iterdir() if p.is_file() and p.name not in ('manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png')}
    (HERE/'manifest.json').write_text(json.dumps(dict(files=files,depends_on=['compact-design-2026-11-16','analog-retry-timeout-2026-11-15']),indent=2)+'\n')
    print(HERE)


if __name__=='__main__':main()

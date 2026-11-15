"""Expose the immutable failed normal retry without changing its report."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;TARGET=HERE.parent/'experiments/2026-11-15-analog-retry-timeout'
def main():
    report=json.loads((TARGET/'report.json').read_text());assert report['state']=='complete'
    (TARGET/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 normal analogue retry</title><link rel="icon" href="data:,"><style>body{max-width:960px;margin:30px auto;padding:0 16px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}a{color:#8acfff;overflow-wrap:anywhere}#state{padding:16px;background:#3c2831}</style>
<nav><a href="/">Dashboard</a> · <a href="../../compact-design/">Compact CP1 design</a></nav>
<h1>Normal analogue retry: preserved timeout</h1><p id="state">Acceptance incomplete. The full graphics hardware simulation exceeded 3,600 seconds. Boot was blocked by that failed dependency. The completed run and its errors are preserved.</p>
<p>Milestones 1–3: 3/5, 3/5 and 7/9 accepted gates. The 155 harness regressions passed. The earlier ALU-sequence timeout did not recur; the 145,536-row sequence stage passed in this run.</p>
<p><a href="report.json">Original completed report</a> · <a href="archive.json">Archive receipt</a> · <a href="manifest.json">All source and artifact hashes</a></p></html>''')
    manifest=json.loads((TARGET/'manifest.json').read_text());p=TARGET/'index.html'
    manifest['files']['index.html']=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (TARGET/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Published preserved normal retry')
if __name__=='__main__':main()

"""Publish the isolated replay result alongside the retained failed full run."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result=json.loads((HERE/'summary.json').read_text());assert result['passed']
    for relative,digest in result['source_hashes'].items():assert sha(HERE/'replay'/relative)==digest
    previous=HERE.parent/'experiments/2026-11-15-refreshed-complete'
    comparison={p:sha(previous/p)==digest for p,digest in result['source_hashes'].items() if p.endswith(('.sv','.hex'))}
    assert all(comparison.values())
    (HERE/'comparison.json').write_text(json.dumps(dict(previous_successful_run=str(previous.relative_to(HERE.parent)),identical= comparison),indent=2)+'\n')
    (HERE/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · ALU timeout diagnosis</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:24px auto;padding:0 16px;max-width:900px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}a{{color:#8acfff;overflow-wrap:anywhere}}</style>
<h1>ALU timeout: isolated replay passes</h1><p id="verdict">All {result['expected_rows']:,} rows passed in {result['wall_seconds']:.3f} seconds ({result['cpu_seconds']:.3f} CPU seconds).</p>
<p>The full run exceeded its 180-second ALU-sequence limit. An isolated replay of the exact binary completed under that limit, with {180-result['wall_seconds']:.3f} seconds to spare. This diagnostic allowed up to 600 seconds. Competing work may explain the earlier timeout; the replay does not establish the cause.</p>
<p>The HDL, ROM and vectors match the preceding successful run byte for byte. This result is diagnostic only. The failed full-run report is preserved, including its error and stale ALU log/coverage. A fresh full run is required.</p>
<p><a href="../experiments/2026-11-15-analog-timeout/">Archived failed run</a> · <a href="summary.json">Measured replay</a> · <a href="comparison.json">Input comparison</a> · <a href="replay.log">Simulator output</a> · <a href="manifest.json">File hashes</a> · <a href="remote-validation.json">Remote verification</a></p></html>''')
    paths=[p for p in HERE.rglob('*') if p.is_file() and p.name not in {'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'} and '__pycache__' not in p.parts]
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)}
    (HERE/'manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print('Published',len(files),'diagnostic artifacts')


if __name__=='__main__':main()

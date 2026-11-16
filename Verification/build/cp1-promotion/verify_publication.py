"""Check published promotion/study bytes and every reused report artifact."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request
import urllib.parse

BUILD=Path(__file__).resolve().parents[1]
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/'


def check(item):
    name,expected=item
    h=hashlib.sha256()
    with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
        while chunk:=response.read(1024*1024):h.update(chunk)
    if h.hexdigest()!=expected:raise ValueError('Remote hash mismatch: '+name)
    return name


def main():
    report=json.loads((BUILD/'cp1-promotion/report.json').read_text())
    expected=dict(report['artifact_hashes'])
    for name in ('cp1-promotion','cp1-timing-review'):
        manifest=json.loads((BUILD/name/'manifest.json').read_text())
        expected.update({name+'/'+p:r['sha256'] for p,r in manifest['files'].items()})
    with ThreadPoolExecutor(max_workers=6) as pool:
        checked=list(pool.map(check,expected.items()))
    result=dict(passed=True,checked_hashes=len(checked),base_url=BASE,
                scope='Published promotion/study manifests and every artifact pinned by the promoted report.')
    for name in ('cp1-promotion','cp1-timing-review'):
        (BUILD/name/'remote-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__=='__main__':main()

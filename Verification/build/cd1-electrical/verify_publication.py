"""Check every manifest artifact locally and through the remote dashboard."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from urllib.parse import quote
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
BASE = 'https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cd1-electrical/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest_bytes = (HERE / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    with urlopen(BASE + 'manifest.json', timeout=60) as response:
        assert response.read() == manifest_bytes
    def check(item):
        name, expected = item
        content = (HERE / name).read_bytes()
        assert len(content) == expected['bytes'] and sha(content) == expected['sha256'], name
        with urlopen(BASE + quote(name), timeout=60) as response:
            remote = response.read()
        assert len(remote) == expected['bytes'] and sha(remote) == expected['sha256'], name
        return dict(file=name, sha256=expected['sha256'], bytes=len(remote), matched=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, manifest['files'].items()))
    result = dict(passed=True, checked_at=datetime.now(timezone.utc).isoformat(), base_url=BASE,
                  manifest_sha256=sha(manifest_bytes), files_checked=len(rows), files=rows)
    (HERE / 'remote-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    with urlopen(BASE + 'remote-validation.json', timeout=60) as response:
        assert response.read() == (HERE / 'remote-validation.json').read_bytes()
    print(f'{len(rows)} local and remote artifact hashes match; remote result downloaded and verified')


if __name__ == '__main__':
    main()

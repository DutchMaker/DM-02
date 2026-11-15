#!/usr/bin/env python3
"""Fetch a pinned historical symbol set. Subsequent runs verify the saved hashes."""
import json
import urllib.request
from dm02.common import VROOT, digest, write_json

COMMIT = '2777f4341e7d96346cb8c78574350d64033c615c'
LIBRARIES = ['74xx', 'Connector', 'Connector_Generic', 'Device', 'Mechanical',
             'Memory_EPROM', 'Power_Supervisor', 'Switch', 'power']


def main():
    dest = VROOT / 'vendor' / 'kicad5'
    dest.mkdir(parents=True, exist_ok=True)
    lock = dest / 'manifest.json'
    previous = json.loads(lock.read_text()) if lock.exists() else {}
    entries = []
    for name in [x + '.lib' for x in LIBRARIES] + ['LICENSE.md']:
        url = f'https://raw.githubusercontent.com/KiCad/kicad-symbols/{COMMIT}/{name}'
        p = dest / name
        if not p.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                p.write_bytes(response.read())
        sha = digest(p)
        old = next((x for x in previous.get('files', []) if x['name'] == name), None)
        if old and old['sha256'] != sha:
            raise SystemExit(f'Pinned library modified: {p}')
        entries.append(dict(name=name, url=url, sha256=sha))
    write_json(lock, dict(commit=COMMIT, tag='5.1.6', files=entries))
    print(f'Historical KiCad symbols ready: {len(entries)} files, commit {COMMIT}')


if __name__ == '__main__':
    main()

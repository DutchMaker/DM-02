"""Archive supplier publications and immutable P2 inputs for a local screen."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
URLS = {
    'oshpark-two-layer.html': 'https://docs.oshpark.com/services/two-layer/',
    'oshpark-kicad.html': 'https://docs.oshpark.com/design-tools/kicad/',
    'oshpark-rules.html': 'https://docs.oshpark.com/design-tools/kicad/kicad-design-rules/',
    'oshpark-drills.html': 'https://docs.oshpark.com/submitting-orders/drill-specs/',
    'kingboard-kb6167f.pdf': 'https://docs.oshpark.com/resources/two-layer-substrate-Kingboard-KB6167F.pdf',
    'taiyo-psr4000bn.pdf': 'https://docs.oshpark.com/resources/rigid-soldermask-taiyo-PSR-4000BN.pdf',
    'jlcpcb-capabilities.html': 'https://jlcpcb.com/capabilities',
    'jlcpcb-stackup-qa.html': 'https://jlcpcb.com/help/answers/detail/15-various-stackups',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = HERE/'sources'
    sources.mkdir(exist_ok=True)
    old = json.loads((sources/'manifest.json').read_text()) if (sources/'manifest.json').exists() else {}
    cached = {row['file']: row for row in old.get('remote', [])}
    retrievals = []
    for name, url in URLS.items():
        path = sources/name
        if name in cached and path.exists():
            assert sha(path) == cached[name]['sha256'] and cached[name]['url'] == url
            retrievals.append(cached[name])
            continue
        response = subprocess.run(['curl','-fLsS','--max-time','60','--output',str(path),
                                   '--write-out','%{url_effective}',url],capture_output=True,text=True)
        assert response.returncode == 0, (url,response.stderr)
        retrievals.append(dict(file=name, url=url, final_url=response.stdout,
                               retrieved_at=datetime.now(timezone.utc).isoformat(),
                               bytes=path.stat().st_size, sha256=sha(path)))
    local = {
        'Verification/build/cd1-stitching/CD1-P2-routed.kicad_pcb': 'CD1-P2-routed.kicad_pcb',
        'Verification/build/cd1-stitching/CD1-P2-routed.kicad_pro': 'CD1-P2-routed.kicad_pro',
        'Verification/build/cd1-stitching/CD1-P2-routed.kicad_dru': 'CD1-P2-routed.kicad_dru',
        'Verification/build/cd1-stitching/geometry.json': 'p2-geometry.json',
        'Verification/build/cd1-stitching/source.xml': 'source.xml',
        'Verification/build/cd1-capacitance/field.py': 'field.py',
        'Verification/build/cd1-capacitance/numerical-results.json': 'numerical-results.json',
        'Verification/build/cd1-capacitance/survey.json': 'survey.json',
    }
    originals = []
    for path, name in local.items():
        if (sources/name).exists():
            assert sha(ROOT/path) == sha(sources/name), path
        else:
            shutil.copyfile(ROOT/path, sources/name)
        originals.append(dict(source=path, file=name, sha256=sha(sources/name)))
    (sources/'manifest.json').write_text(json.dumps(dict(remote=retrievals, local=originals), indent=2)+'\n')
    print(f'Archived {len(retrievals)} supplier publications and {len(originals)} local inputs')


if __name__ == '__main__':
    main()

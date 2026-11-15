"""Archive the physical-layout and loading inputs for this numerical screen."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    sources = HERE / 'sources'
    sources.mkdir(exist_ok=True)
    paths = {
        'Verification/build/cd1-stitching/geometry.json': 'p2-geometry.json',
        'Verification/build/cd1-stitching/CD1-P2-routed.kicad_pcb': 'CD1-P2-routed.kicad_pcb',
        'Verification/build/cd1-stitching/source.xml': 'source.xml',
        'Verification/build/cd1-electrical/analyze.py': 'p1-audit.py',
        'Verification/distribution-parts.json': 'distribution-parts.json',
        'Verification/pc-parts.json': 'pc-parts.json',
    }
    rows = []
    for source, name in paths.items():
        target = sources / name
        shutil.copyfile(ROOT / source, target)
        rows.append(dict(source=source, file=name, sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (sources / 'manifest.json').write_text(json.dumps(dict(files=rows), indent=2)+'\n')
    print(f'Archived {len(rows)} inputs')


if __name__ == '__main__':
    main()

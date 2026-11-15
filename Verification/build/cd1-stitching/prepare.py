"""Snapshot the published P1 inputs and audit helpers without modifying them."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'cd1-electrical'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = HERE / 'sources'
    sources.mkdir(exist_ok=True)
    mapping = {
        OLD / 'candidate/CD1-P1-routed.kicad_pcb': 'CD1-P1-routed.kicad_pcb',
        OLD / 'candidate/CD1-P1-routed.kicad_dru': 'CD1-P1-routed.kicad_dru',
        OLD / 'candidate/CD1-P1-routed.kicad_pro': 'CD1-P1-routed.kicad_pro',
        OLD / 'candidate/geometry.json': 'p1-geometry.json',
        OLD / 'candidate/analysis.json': 'p1-analysis.json',
        OLD / 'candidate/validation.json': 'p1-validation.json',
        OLD / 'candidate/source.xml': 'source.xml',
        OLD / 'candidate/source.kicad_sch': 'source.kicad_sch',
        OLD / 'analyze.py': 'analyze.py',
        OLD / 'export_geometry.py': 'export_geometry.py',
        HERE.parent / 'cd1-layout/check.py': 'check.py',
    }
    expected = '377d60d886f0dba62903cb12b4920f084fb430f6f39c56b874fd873541035532'
    assert sha(OLD / 'candidate/CD1-P1-routed.kicad_pcb') == expected
    rows = []
    for source, name in mapping.items():
        target = sources / name
        shutil.copyfile(source, target)
        rows.append(dict(source=str(source.relative_to(HERE.parents[2])), file=name, sha256=sha(target)))
        assert sha(source) == sha(target)
    (sources / 'manifest.json').write_text(json.dumps(dict(files=rows), indent=2) + '\n')
    print(f'Archived {len(rows)} P1 inputs and helper files')


if __name__ == '__main__':
    main()

"""Freeze all BOM publication files into a remotely verifiable manifest."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result=json.loads((HERE/'validation.json').read_text());assert result['passed']
    assert result['current_references']==738 and result['current_ics_and_oscillator']==289
    for row in json.loads((HERE/'source-manifest.json').read_text())['sources']:
        assert sha(HERE/row['archived'])==row['sha256']
        assert sha(HERE.parents[2]/row['source'])==row['sha256']
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','smd-filter.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'
        and not(p.parent==HERE and p.name in excluded)}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n')
    print('Published',len(files),'BOM, workbook, source and method artifacts')


if __name__=='__main__':main()

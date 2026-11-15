"""Archive the manufacturer ACT175 evidence for the DIP logic candidate."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
URL='https://www.ti.com/lit/ds/symlink/cd74act175.pdf'
folder=HERE/'sources';folder.mkdir(parents=True,exist_ok=True)
path=folder/'cd74act175.pdf'
if not path.exists():
    with urlopen(Request(URL,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as response:data=response.read()
    assert data.startswith(b'%PDF');path.write_bytes(data)
pdf=PdfReader(path)
text='\n'.join(f'\n--- PDF page {i+1} ---\n'+p.extract_text(extraction_mode='layout') for i,p in enumerate(pdf.pages))
(folder/'cd74act175.txt').write_text(text)
(folder/'cd74act175-source.json').write_text(json.dumps(dict(url=URL,
    archived_at=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),
    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=len(pdf.pages)),indent=2)+'\n')
print('Archived ACT175 manufacturer datasheet:',len(pdf.pages),'pages')

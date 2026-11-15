"""Archive documentation for the latest exact reported DIP logic markings."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
SOURCES={
    'sn74hc377':'https://www.ti.com/lit/ds/symlink/sn74hc377.pdf',
    'sn74hct00':'https://www.ti.com/lit/ds/symlink/sn74hct00.pdf',
    'sn74hct08':'https://www.ti.com/lit/ds/symlink/sn74hct08.pdf',
    'philips-74hct154':'https://datasheet.octopart.com/74HC154N-Philips-datasheet-26590.pdf',
}
rows=[]
for name,url in SOURCES.items():
    path=HERE/'sources'/(name+'.pdf')
    if not path.exists():
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as response:data=response.read()
        assert data.startswith(b'%PDF');path.write_bytes(data)
    pdf=PdfReader(path)
    text='\n'.join(f'\n--- PDF page {i+1} ---\n'+p.extract_text(extraction_mode='layout') for i,p in enumerate(pdf.pages))
    (path.with_suffix('.txt')).write_text(text)
    rows.append(dict(name=name,url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=len(pdf.pages),
        archived_at=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()))
(HERE/'logic-sources.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Archived',len(rows),'logic datasheets')

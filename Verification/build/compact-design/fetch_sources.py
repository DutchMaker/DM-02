from pathlib import Path
import hashlib,json
from urllib.request import Request,urlopen
from pypdf import PdfReader
HERE=Path(__file__).resolve().parent
folder=HERE/'sources';folder.mkdir(exist_ok=True)
sources={'cd74hct191':'https://www.ti.com/lit/ds/symlink/cd74hct191.pdf',
         'sn74hct273':'https://www.ti.com/lit/ds/symlink/sn74hct273.pdf',
         'sn74hct245':'https://www.ti.com/lit/ds/symlink/sn74hct245.pdf'}
rows=[]
for name,url in sources.items():
    p=folder/(name+'.pdf')
    if not p.exists():
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as r:data=r.read()
        assert data.startswith(b'%PDF');p.write_bytes(data)
    pdf=PdfReader(p)
    p.with_suffix('.txt').write_text('\n'.join(f'\n--- PDF page {i+1} ---\n'+page.extract_text(extraction_mode='layout') for i,page in enumerate(pdf.pages)))
    rows.append(dict(url=url,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(pdf.pages)))
(folder/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Archived',len(rows),'component datasheets')

"""Archive manufacturer-origin memory datasheets for the reported owned stock."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
SOURCES={
    'um61512a':'https://www.silicon-ark.co.uk/datasheets/um61512ak%20datasheet%20umc.pdf',
    'w27c512':'https://media.digikey.com/pdf/Data%20Sheets/Winbond%20PDFs/W27C512.pdf',
    'm27c1024':'https://futurlec.com/Datasheet/Memory/27C1024.pdf',
}


def fetch(item):
    name,url=item;folder=HERE/'sources';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(name+'.pdf')
    if path.exists():data=path.read_bytes()
    else:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as response:data=response.read()
        assert data.startswith(b'%PDF');path.write_bytes(data)
    pdf=PdfReader(path)
    text='\n'.join(f'\n--- PDF page {i+1} ---\n'+p.extract_text(extraction_mode='layout') for i,p in enumerate(pdf.pages))
    (folder/(name+'.txt')).write_text(text)
    result=dict(id=name,url=url,archived_at=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),pages=len(pdf.pages),
        pdf_sha256=hashlib.sha256(data).hexdigest(),text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        scope='Manufacturer-origin archived datasheet via a third-party host. Family documentation does not establish exact markings or condition of owned parts.')
    (folder/(name+'-source.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,SOURCES.items()))
    (HERE/'sources.json').write_text(json.dumps(rows,indent=2)+'\n')
    print([(r['id'],r['pages']) for r in rows])

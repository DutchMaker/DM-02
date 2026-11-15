"""Extract manufacturer PDFs and render selected mechanical/pinout pages."""
from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
for path in (HERE/'sources').glob('*.pdf'):
    reader=PdfReader(path)
    path.with_suffix('.txt').write_text('\n'.join(f'--- Page {i+1} ---\n'+p.extract_text(extraction_mode='layout') for i,p in enumerate(reader.pages)))
    print(path.name,len(reader.pages),'pages')
    # Exact capacitor sheet page 1 and TI pinout/mechanical drawing pages.
    selected=[0] if path.name.startswith('kemet-c315') else []
    if path.name=='ti-sn74ahct244.pdf':
        selected=[2,9]
    if path.name=='ti-n0020a.pdf':selected=[0]
    if selected:
        doc=pdfium.PdfDocument(path);folder=HERE/'document-pages';folder.mkdir(exist_ok=True)
        for i in selected:doc[i].render(scale=1.5).to_pil().save(folder/f'{path.stem}-{i+1}.png')

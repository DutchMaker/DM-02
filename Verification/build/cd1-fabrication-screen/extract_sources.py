"""Extract supplier facts and render material datasheet pages for review."""
from html.parser import HTMLParser
from pathlib import Path
import json
from pypdf import PdfReader
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows=[]
        self.row=None
        self.cell=None
        self.text=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):
            self.skip+=1
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
        if tag in ('p','h1','h2','h3','tr','br'):self.text.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'):
            self.skip-=1
        if tag in ('td','th') and self.cell is not None:
            if self.row is not None:self.row.append(' '.join(''.join(self.cell).split()))
            self.cell=None
            self.text.append(' | ')
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row)
            self.row=None
            self.text.append('\n')
    def handle_data(self,data):
        if self.skip:return
        self.text.append(data)
        if self.cell is not None:self.cell.append(data)


def main():
    for path in (HERE/'sources').glob('*.html'):
        parser=Tables()
        parser.feed(path.read_text())
        path.with_suffix('.tables.json').write_text(json.dumps(parser.rows,indent=2)+'\n')
        text='\n'.join(' '.join(line.split()) for line in ''.join(parser.text).splitlines() if line.strip())
        path.with_suffix('.txt').write_text(text+'\n')
    for path in (HERE/'sources').glob('*.pdf'):
        reader=PdfReader(path)
        path.with_suffix('.txt').write_text('\n'.join(f'--- Page {i+1} ---\n'+page.extract_text(extraction_mode='layout')
                                                     for i,page in enumerate(reader.pages)))
        doc=pdfium.PdfDocument(path)
        folder=HERE/'document-pages'
        folder.mkdir(exist_ok=True)
        for index in range(len(doc)):
            page=doc[index]
            page.render(scale=1.5).to_pil().save(folder/f'{path.stem}-{index+1}.png')
        print(path.name,len(reader.pages),'pages extracted and rendered')


if __name__=='__main__':main()

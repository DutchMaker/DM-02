"""Collect existing manufacturer evidence without changing earlier studies."""
from pathlib import Path
import json
import shutil
from pypdf import PdfReader
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import digest,write_json


def main():
    dest=HERE/'sources';assert not dest.exists(),'Preserve source snapshot';dest.mkdir()
    models=json.loads((ROOT/'Verification/build/cp1-hct273/component-review.json').read_text())['selected_models']
    wanted={d['source'] for d in models.values()}
    wanted.update('cd74hct'+n for n in ('00','04','08','32','74','151','153','154','157','161','244','273'))
    wanted.add('abracon-ach-2016')
    records={}
    for stem in sorted(wanted):
        candidates=list((ROOT/'Verification/vendor').glob('*/'+stem+'.txt'))
        candidates+=list((ROOT/'Verification/build/cp1-hct273/sources').glob(stem+'.txt'))
        candidates+=list((ROOT/'Verification/build/cp1-text/sources').glob(stem+'.txt'))
        candidates+=list((ROOT/'Verification/build/component-followup').glob(stem+'.txt'))
        candidates+=list((ROOT/'Verification/build/dip-logic/sources').glob(stem+'.txt'))
        if candidates:
            source=candidates[0];shutil.copyfile(source,dest/(stem+'.txt'))
            records[stem]=dict(original=str(source.relative_to(ROOT)),sha256=digest(source))
            manifest=source.parent/'manifest.json'
            if manifest.exists():
                m=json.loads(manifest.read_text());rows=m.get('files',[]) if isinstance(m,dict) else m
                records[stem]['provenance']=[r for r in rows if isinstance(r,dict) and
                    (r.get('id')==stem or r.get('file') in (stem+'.txt',stem+'.pdf'))]
            pdf=source.with_suffix('.pdf')
            sidecar=source.with_name(stem+'-source.json')
            if sidecar.exists():records[stem]['source_record']=json.loads(sidecar.read_text())
        else:
            pdf=ROOT/'Verification/build/cp1-bridge/sources'/(stem+'.pdf');assert pdf.exists(),stem
            (dest/(stem+'.txt')).write_text('\n'.join(f'--- PDF page {i} ---\n'+p.extract_text(extraction_mode='layout')
                for i,p in enumerate(PdfReader(pdf).pages,1)))
            records[stem]=dict(original=str(pdf.relative_to(ROOT)),sha256=digest(pdf))
        if pdf.exists():shutil.copyfile(pdf,dest/pdf.name)
        records[stem]['snapshot_sha256']=digest(dest/(stem+'.txt'))
    write_json(dest/'manifest.json',records)


if __name__=='__main__':main()

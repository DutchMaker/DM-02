"""Revise only the three selected 273s and their BOM notes; preserve stock."""
from pathlib import Path
from collections import Counter
import hashlib,json
from openpyxl import load_workbook
from openpyxl.comments import Comment
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'compact-design/DM-02-compact-BOM.xlsx'
OUT=HERE/'DM-02-CP1-R2-BOM.xlsx'
OLD='SN74HCT273N';NEW='CD74HCT273E'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    w=load_workbook(BASE);allowed=set()
    for row in w['Compact instances'].iter_rows(min_row=2):
        if row[2].value==OLD:
            assert (row[0].value,row[1].value) in {('AL1','U2'),('ME1','U11'),('ME1','U15')}
            row[2].value=NEW;allowed.add(('Compact instances',row[2].coordinate))
    assert len(allowed)==3
    for row in w['Compact BOM'].iter_rows(min_row=2):
        if row[0].value==OLD:
            row[0].value=NEW;allowed.add(('Compact BOM',row[0].coordinate))
            assert row[3].value is None,'Preserve any entered user stock'
            row[5].value='CP1-R2: replaces SN74HCT273N at AL1 U2 and ME1 U11/U15. TI SCHS174D gives explicit 38 ns clock / 40 ns clear bounds at 4.5 V, -40..85 C, 50 pF; 3 ns data hold required. Model uses conservative 42 ns. Exact owned quantity remains unknown.'
            row[5].comment=Comment('Source: https://www.ti.com/lit/ds/symlink/cd74hct273.pdf, SCHS174D sections 5.5/5.6. Pin/load and monitor checks: cp1-hct273/part-qualification.json.','DM-02')
            allowed.add(('Compact BOM',row[5].coordinate))
    guide=w['Compact guide']
    for cell,value in {'A1':'CP1-R2 compact DIP candidate','B10':'See cp1-hct273/acceptance.json for this revision. Physical qualification remains open.','B13':'cp1-hct273/packages.json and candidate/Circuits/KiCad/Compact/candidates'}.items():
        guide[cell]=value;allowed.add((guide.title,cell))
    w.save(OUT)
    original=load_workbook(BASE)
    assert original.sheetnames==w.sheetnames
    for sheet in original:
        for row in sheet:
            for c in row:
                new=w[sheet.title][c.coordinate]
                if (sheet.title,c.coordinate) not in allowed:assert (c.value,c._style)==(new.value,new._style),(sheet.title,c.coordinate)
                if c.data_type=='f':assert new.value==c.value
    (HERE/'workbook-edit.json').write_text(json.dumps(dict(source_sha256=sha(BASE),changed_cells=sorted(allowed),sheets=w.sheetnames,formulas_preserved=True,stock_preserved=True),indent=2)+'\n')
    print(OUT)
def validate():
    w=load_workbook(OUT);cached=load_workbook(OUT,data_only=True);base=load_workbook(BASE)
    edited=json.loads((HERE/'workbook-edit.json').read_text());allowed={tuple(x) for x in edited['changed_cells']}
    assert sha(BASE)==edited['source_sha256']
    assert w.sheetnames==base.sheetnames
    for sheet in base:
        for row in sheet:
            for c in row:
                n=w[sheet.title][c.coordinate]
                if (sheet.title,c.coordinate) not in allowed:assert (c.value,c._style)==(n.value,n._style),(sheet.title,c.coordinate)
    errors=[(s.title,c.coordinate,c.value) for s in cached for row in s for c in row if c.data_type=='e'];assert not errors
    counts=Counter(p['value'] for p in json.loads((HERE/'packages.json').read_text()) if p['ic'])
    for row in cached['Compact BOM'].iter_rows(min_row=2,max_row=1+len(counts),values_only=True):assert row[1]==counts[row[0]],row
    assert counts[NEW]==3 and OLD not in counts and sum(counts.values())==192
    assert cached['Compact guide']['B3'].value==192
    result=dict(passed=True,sha256=sha(OUT),source_workbook_sha256=sha(BASE),preserved_sheets=base.sheetnames,
                formula_errors=errors,logic_memory_packages=192,changed_parts=3,unknown_quantities_preserved=True)
    (HERE/'workbook-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':
    import sys
    validate() if '--validate' in sys.argv else main()

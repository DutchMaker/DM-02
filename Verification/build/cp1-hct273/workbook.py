"""Append the source-derived CP1 BOM ahead of the preserved working inventory."""
from pathlib import Path
from collections import Counter
from copy import copy
import hashlib,json
from openpyxl import load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.comments import Comment
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'owned-inventory/DM-02-BOM-owned-stock-update.xlsx'
OUT=HERE/'DM-02-compact-BOM.xlsx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    w=load_workbook(BASE);original=sha(BASE)
    rows=json.loads((HERE/'packages.json').read_text());audit=json.loads((HERE/'audit.json').read_text())
    counts=Counter(p['value'] for p in rows if p['ic'])
    assert sum(counts.values())==audit['logic_memory_packages']
    sheets=[w.create_sheet(n,i) for i,n in enumerate(['Compact guide','Compact BOM','Compact instances'])]
    guide,bom,instances=sheets
    instances.append(['Board','Reference','Selected part','Footprint','Physical units','Logic or memory IC'])
    for p in rows:instances.append([p['board'],p['ref'],p['value'],p['footprint'],','.join(map(str,p['units'])),int(p['ic'])])
    bom.append(['Selected part','Required','Reported ownership','Confirmed exact quantity','Shortfall','Selection notes'])
    exact={'M27C322-100F1','M27C1024-10F1','UM61512AK-15','W27C512-45Z','CD74HCT161E','SN74HC377N'}
    family={'SN74HCT245N':'74HCT245','CD74HCT191E':'74HCT191','SN74HCT574N':'74HCT574'}
    alternatives={'CD74HCT154E':'74HCT154N','SN74AHCT157N':'one 74HCT157','SN74AHCT00N':'SN74HCT00N','SN74AHCT08N':'SN74HCT08N'}
    for i,part in enumerate(sorted(counts),2):
        ownership='Owned exact marking; count unknown' if part in exact else 'Owned family; manufacturer/suffix unconfirmed' if part in family else 'Zero owned' if part=='CD74ACT175E' else 'Owned alternative needs qualification' if part in alternatives else 'Ownership not established'
        note=('Reported family: '+family[part]+'. TI selected for reproducible timing bounds.' if part in family else
              'Reported alternative: '+alternatives[part]+'. Not counted as selected-part stock.' if part in alternatives else
              'User explicitly confirmed zero ACT175 owned.' if part=='CD74ACT175E' else
              'Source: CP1 physical KiCad package allocation; packages.json.')
        bom.append([part,f'=COUNTIF(\'Compact instances\'!$C$2:$C${instances.max_row},A{i})',ownership,
            0 if part=='CD74ACT175E' else None,f'=IF(ISNUMBER(D{i}),MAX(0,B{i}-D{i}),"Unknown")',note])
        bom.cell(i,2).number_format='0';bom.cell(i,4).number_format='0';bom.cell(i,5).number_format='0'
        bom.cell(i,4).comment=Comment('Reported stock: user confirmation in owned-inventory/stock.json. Blank means unknown, not zero. Enter an exact selected-part count only.','DM-02')
        bom.cell(i,4).fill=PatternFill('solid',fgColor='FFF2CC');bom.cell(i,4).font=Font(name='Arial',color='0000FF',size=11)
    total=bom.max_row+1;bom.append(['Logic/memory IC total',f'=SUM(B2:B{total-1})'])
    guide.append(['CP1 compact DIP candidate','Working BOM and verification scope'])
    guide.append(['Previous DL1 logic/memory ICs',288])
    guide.append(['CP1 logic/memory ICs',f"='Compact BOM'!B{total}"])
    guide.append(['Packages removed','=B2-B3'])
    guide.append(['Reduction','=B4/B2']);guide['B5'].number_format='0.0%'
    guide.append(['Oscillator','ACH-4.000MHZ-EK; one through-hole DIP-8 oscillator, outside the IC comparison'])
    guide.append(['Clock target','4 MHz oscillator / 8 = 500 kHz microcycles; conditional timing model'])
    guide.append(['Stock entry','Edit yellow quantity cells in Compact BOM. Blank means unknown. The existing inventory sheets are preserved.'])
    guide.append(['Counts','Each physical package is counted once. Reset, fanout, bus and counter support logic are included.'])
    guide.append(['Verification','See compact-design/index.html and verification-state.json for completed runs.'])
    guide.append(['Open electrical work','150 pF HCT245 delay table, but 50 pF disable table; IO capacitance, loaded edges and HC377 thresholds require qualification.'])
    guide.append(['Open physical work','Supply/startup coverage, programming/readback, independent review, PCB layout and bench tests.'])
    guide.append(['Source','compact-design/packages.json and candidate/Circuits/KiCad/Compact/candidates'])
    guide['B2'].comment=Comment('Source: dip-logic/packages.json. 288 distinct U-reference logic/memory packages; oscillator and passives excluded.','DM-02')
    for s in sheets:
        s.freeze_panes='B2';s.auto_filter.ref=s.dimensions;s.sheet_view.showGridLines=False
        for cell in s[1]:cell.fill=PatternFill('solid',fgColor='17354A');cell.font=Font(name='Arial',bold=True,color='FFFFFF',size=11)
        for row in s.iter_rows(min_row=2):
            for cell in row:
                if not (s==bom and cell.column==4):cell.font=Font(name='Arial',size=11,color='008000' if cell.data_type=='f' and '!' in cell.value else '000000')
                cell.alignment=Alignment(vertical='top',wrap_text=True)
        for col in ('A','B','C','D','E','F'):s.column_dimensions[col].width={'A':27,'B':20,'C':44,'D':36,'E':18,'F':70}[col]
    guide.column_dimensions['B'].width=105
    w.active=0;w.save(OUT)
    assert sha(BASE)==original
    print(OUT)

def validate():
    w=load_workbook(OUT);cached=load_workbook(OUT,data_only=True);base=load_workbook(BASE)
    for s in base:
        n=w[s.title];assert (s.max_row,s.max_column)==(n.max_row,n.max_column)
        for row in s:
            for c in row:assert n[c.coordinate].value==c.value and n[c.coordinate]._style==c._style,(s.title,c.coordinate)
    errors=[(s.title,c.coordinate,c.value) for s in cached for row in s for c in row if c.data_type=='e'];assert not errors,errors
    counts=Counter(p['value'] for p in json.loads((HERE/'packages.json').read_text()) if p['ic'])
    for row in cached['Compact BOM'].iter_rows(min_row=2,max_row=1+len(counts),values_only=True):assert row[1]==counts[row[0]],row
    assert cached['Compact guide']['B3'].value==sum(counts.values())
    assert cached['Compact guide']['B4'].value==288-sum(counts.values())
    assert abs(cached['Compact guide']['B5'].value-(288-sum(counts.values()))/288)<1e-12
    q={r[0]:r[3] for r in cached['Compact BOM'].iter_rows(min_row=2,max_row=1+len(counts),values_only=True) if r[3] is not None}
    assert q=={'CD74ACT175E':0},q
    result=dict(passed=True,sha256=sha(OUT),formula_errors=errors,source_workbook_sha256=sha(BASE),
        preserved_sheets=base.sheetnames,logic_memory_packages=sum(counts.values()),unknown_quantities_preserved=True)
    (HERE/'workbook-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':
    import sys
    validate() if '--validate' in sys.argv else main()

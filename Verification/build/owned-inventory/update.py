"""Record reported stock in a versioned workbook using its existing input cells."""
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import sys
from openpyxl import load_workbook
from openpyxl.comments import Comment

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=HERE.parent/'bom-inventory/DM-02-working-BOM-and-inventory.xlsx'
OUTPUT=HERE/'DM-02-BOM-owned-stock-update.xlsx'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import sources


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def main():
    before=sources();original_hash=sha(BASE);wb=load_workbook(BASE)
    stock=read(HERE/'stock.json');assessment=read(HERE/'assessment.json')
    assert len(stock['parts'])==11 and len({p['reported_marking'] for p in stock['parts']})==11
    assert all(p['quantity'] is None for p in stock['parts'])
    updates={
        'AS6C1008-55PCN':('UM61512AK-15','Owned alternative, not AS6C stock. 64K x8/15 ns; skinny DIP and pin 2 NC require changes. Count unknown.'),
        'AT27C512R-70PU':('W27C512-45Z; 27C1024','Owned ROM alternatives. W27C512 for program/byte lanes; 27C1024 could replace both control lanes. No AT27 stock confirmed; counts unknown.'),
        'CD74HCT161M96':('74HCT161','Owned family; exact vendor/package and count pending. Review DIP reuse for the five PC/sequencer positions.'),
        'CD74HCT377M96':('74HCT377','Owned family; vendor/package and count pending. Review DIP reuse for the two retained operand registers.'),
        'SN74HCT574N':('74HCT574','Owned family; vendor/package and count pending. Five current positions; original register-bank route also worth reviewing.'),
        'SN74AHCT244N':('74HCT245; 244 (family unknown)','245 plentiful; 244 scarcer. Alternatives, not confirmed AHCT244 stock. Different pinout/OE/timing; assess per role.'),
        'SN74AHCT157N':('157 (family unknown)','Scarcer stock; exact family/count unknown. 245 is not a direct mux substitute. Reconsider high mux count.'),
        'SST39SF040-70-4I-NHE':('27C322','Multiple owned 27C322s, not SST flash stock. Revisit one-ROM AL1 route; speed/package/programmer pending.'),
        'CD74ACT283E':('74HCT191','Owned counter alternative for stack/address architecture; not an ACT283 pin substitute. Count/vendor pending.'),
        '74HCT377':('74HCT377','Ownership confirmed by user; full marking/package/count pending. Same stock as candidate alternative, not additive.'),
        '74HCT574':('74HCT574','Ownership confirmed by user; full marking/package/count pending. Same stock as candidate alternative, not additive.'),
        '74HCT191':('74HCT191','Ownership confirmed by user; full marking/package/count pending. Review cascaded stack/address use.'),
        '74LS191':('74HCT191','Owned HCT alternative; LS ownership not reported. Counter behaviour and timing need review.'),
        '74HCT244':('244 (family unknown)','User reports scarce 244 stock; HCT/AHCT/HC family not supplied. Count unknown.'),
        '74HCT245':('74HCT245','User reports a lot; exact manufacturer/package and count pending.'),
        'M27C322':('27C322','User reports multiple; manufacturer and full speed/package marking pending.'),
        'UM61512AK-15':('UM61512AK-15','Owned exact reported type; count pending. Same stock as candidate alternative, not additive.'),
    }
    sheet=wb['IC inventory'];changed=[];matched=set()
    for row in range(2,sheet.max_row+1):
        part=sheet.cell(row,2).value
        if part not in updates:continue
        matched.add(part)
        for column,value in zip((8,10),updates[part]):
            cell=sheet.cell(row,column);assert cell.value is None,'Preserve existing user entry: '+cell.coordinate
            cell.value=value;cell.comment=Comment('Source: '+stock['source']+'. Ownership is reported, not a qualified substitution. Exact numeric quantities remain blank. See the accompanying assessment.json.','DM-02')
            changed.append(cell.coordinate)
    assert matched==set(updates)
    wb.save(OUTPUT)
    check=load_workbook(OUTPUT);original=load_workbook(BASE);cached=load_workbook(OUTPUT,data_only=True)
    assert check.sheetnames==original.sheetnames
    errors=[];formulas=0
    for name in original.sheetnames:
        old,new=original[name],check[name];assert (old.max_row,old.max_column)==(new.max_row,new.max_column)
        for row in old:
            for cell in row:
                got=new[cell.coordinate]
                if name!='IC inventory' or cell.coordinate not in changed:assert got.value==cell.value,(name,cell.coordinate)
                assert got._style==cell._style,(name,cell.coordinate,'style')
                formulas+=got.data_type=='f'
                if cached[name][cell.coordinate].data_type=='e':errors.append((name,cell.coordinate))
        assert {k:old.tables[k].ref for k in old.tables}=={k:new.tables[k].ref for k in new.tables}
    assert formulas==0 and not errors
    assert all(check['IC inventory'].cell(row,9).value is None for row in range(2,sheet.max_row+1))
    assert sha(BASE)==original_hash and sources()==before
    write(HERE/'validation.json',dict(passed=True,created_at=datetime.now(timezone.utc).isoformat(),
        original_workbook_sha256=original_hash,updated_workbook_sha256=sha(OUTPUT),
        changed_cells=changed,changed_rows=len(matched),all_other_cell_values_and_styles_preserved=True,
        formula_count=formulas,formula_errors=errors,quantity_cells_left_unknown=True,normal_sources_modified=False))
    entries=''.join(f'<tr><td>{html.escape(r["part"])}</td><td><strong>{html.escape(r["assessment"])}</strong><p>{html.escape(r["detail"])}</p></td></tr>' for r in assessment['parts'])
    (HERE/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · owned inventory update</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:24px auto;padding:0 16px;max-width:1100px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{width:100%;table-layout:fixed;border-collapse:collapse}}td,th{{vertical-align:top;text-align:left;border-bottom:1px solid #304156;padding:10px;overflow-wrap:anywhere}}th:first-child{{width:21%}}.note{{color:#ffd082}}@media(max-width:650px){{table,tbody,tr,td{{display:block}}thead{{display:none}}td:first-child{{font-weight:bold}}td{{padding:10px 0}}}}</style>
<nav><a href="/">Dashboard</a> · <a href="../bom-inventory/">Original BOM publication</a></nav><h1>Owned inventory changes the preferred parts</h1>
<p><a id="workbook" href="{OUTPUT.name}">Download the BOM with your stock notes</a></p>
<p>Eleven reported stock types are recorded; the repeated W27C512 mention is counted once. Numeric quantities remain blank. The workbook fills only its existing ownership/notes inputs; selected FD1 parts and design counts remain the original reference.</p>
<p id="scope" class="note">This is a suitability review and inventory update. An owned-parts circuit has not yet been simulated or promoted.</p>
<p>{html.escape(assessment['recommendation'])}</p><table id="parts"><thead><tr><th>Owned part</th><th>Recommended use and required changes</th></tr></thead><tbody>{entries}</tbody></table>
<h2>Needed to choose exact variants</h2><p>Full markings or clear photos (especially 27C322/27C1024 speed suffixes), approximate quantities and the programmer model/adapters.</p>
<p><a href="stock.json">Reported stock</a> · <a href="assessment.json">Assessment</a> · <a href="validation.json">Workbook validation</a> · <a href="sources/um61512a.pdf">UMC SRAM datasheet</a> · <a href="sources/w27c512.pdf">Winbond ROM datasheet</a> · <a href="sources/m27c1024.pdf">27C1024 family datasheet</a> · <a href="sources.json">Source hashes</a> · <a href="manifest.json">Publication hashes</a></p></html>''')
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*')) if p.is_file() and not(p.parent==HERE and p.name in excluded) and '__pycache__' not in p.parts}
    write(HERE/'manifest.json',dict(files=files))
    print('Updated',len(matched),'inventory rows;',len(changed),'input cells; quantities unknown; all other cell values/styles unchanged')


if __name__=='__main__':main()

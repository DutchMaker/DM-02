"""Publish DL1's schematic-derived BOM and bounded verification results."""
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import csv
import hashlib
import html
import json
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.comments import Comment
from openpyxl.worksheet.table import Table,TableStyleInfo
from openpyxl.utils import get_column_letter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def esc(value):return html.escape(str(value))


def add_sheet(wb,name,headers,rows,widths):
    sheet=wb.create_sheet(name);sheet.append(headers)
    for row in rows:sheet.append(row)
    for row in sheet:
        for cell in row:
            cell.font=Font(name='Arial',size=11,color='202D3B')
            cell.alignment=Alignment(vertical='top',wrap_text=True)
    for cell in sheet[1]:
        cell.font=Font(name='Arial',bold=True,color='FFFFFF',size=11)
        cell.fill=PatternFill('solid',fgColor='203D57')
    for i,width in enumerate(widths,1):sheet.column_dimensions[get_column_letter(i)].width=width
    sheet.freeze_panes='A2';sheet.sheet_view.showGridLines=False
    table=Table(displayName='DL1'+str(len(wb.worksheets)),ref=sheet.dimensions)
    table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
    sheet.add_table(table)
    return sheet


def main():
    summary=read('summary.json');config=read('choices.json');packages=read('packages.json');review=read('register-review.json')
    assert summary['passed'] and summary['remaining_soic']==0
    assert all(sha(HERE/b['candidate'])==b['sha256'] for b in summary['boards'])
    assert all(sha(ROOT/p)==digest for p,digest in summary['source_hashes'].items())
    choices=config['choices'];bynew={c['part']:c for c in choices.values()}
    grouped=defaultdict(list)
    for p in packages:grouped[(p['value'],p['footprint'])].append(p['board']+':'+p['ref'])
    bom=[]
    for (part,footprint),refs in sorted(grouped.items()):
        if part in bynew:status=bynew[part]['reason']+' '+bynew[part]['sourcing']
        elif part=='SST39SF040-70-4I-NHE':status='OPEN DIP REQUIREMENT: eight PLCC flash ICs remain in this package-conversion stage. Owned M27C322-100F1 ALU conversion is still required.'
        else:status='Retained reference FD1 item. Owned-memory and oscillator changes still require integration; exact passive/connector selections remain open.'
        assembly='DIP' if footprint.startswith('Package_DIP:') else 'PLCC IC / THT socket' if 'PLCC' in footprint else 'Through-hole footprint'
        bom.append([part,len(refs),assembly,footprint,', '.join(refs),status])
    with (HERE/'candidate-BOM.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['Selected part / value','Quantity','Assembly','Footprint','References','Status']);writer.writerows(bom)
    wb=Workbook();wb.remove(wb.active)
    notes=[
        ['Design','DL1: SOIC-to-DIP logic candidate. All 91 SOIC logic packages have concrete DIP selections and staged schematic edits.'],
        ['48 flip-flops','CD74AC175M96 becomes CD74ACT175E, DIP-16. The part number is 175; a 157 is a mux. This route retains 48 packages.'],
        ['Verification','Native KiCad pin/net parity, package identity and through-hole pad coverage passed. Integrated timing and physical qualification are pending.'],
        ['574 reuse','All 48 positions use asynchronous reset; three use complementary outputs. A 574 has neither feature. Reuse requires a register redesign.'],
        ['Count reduction',f"{summary['potential_273_pairs']} pairs share a clock and physical reset net with no used complementary outputs. These are possible 273-style consolidation sites; no chip-count reduction has been implemented."],
        ['Decoder stock','74HCT154N DIP decoders are owned. Four positions; count and manufacturer/logo still needed for exact vendor pin/timing review. CD74HCT154E remains the staged selected identity.'],
        ['Flip-flop sourcing','Zero CD74ACT175E owned. Source 48 for the current DL1 candidate; supplier availability unconfirmed.'],
        ['Exact counter stock','CD74HCT161E is owned and matches the selected DIP part. Five positions; owned count unknown.'],
        ['Register stock correction','Owned SN74HC377N corrects the earlier HCT377 report. CMOS-output drivers make reuse plausible, but input/load/timing checks remain pending for the two positions.'],
        ['Gate stock','Owned SN74HCT00N and SN74HCT08N have 25 ns / 30 ns delay bounds at 4.5 V, 50 pF, -40..85 C. The selected AHCT models use 9 ns; substitution requires a timing review.'],
        ['Remaining DIP requirement','Eight PLCC flash ICs remain in this stage. The owned M27C322 ALU conversion removes that architecture; it has not been implemented here.'],
        ['Owned memories','M27C322-100F1, M27C1024-10F1, UM61512AK-15 and W27C512-45Z remain the preferred owned-memory path.'],
        ['Quantities','Candidate quantities are extracted from physical board/reference pairs, with multi-unit symbols counted once. They are not a purchase order.'],
        ['Inventory','Reported stock includes one HCT157 and zero ACT175. Other numeric counts remain blank. Literal HC/HCT/AHCT markings are retained; ownership does not establish interchangeability.'],
        ['Reproduce','python3 Verification/build/dip-logic/check.py, then publish.py, verify.py and browser_check.cjs.'],
        ['Evidence','https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/dip-logic/'],
    ]
    add_sheet(wb,'Start',['Topic','Details'],notes,[24,125])
    sheet=add_sheet(wb,'Candidate BOM',['Selected part / value','Quantity','Assembly','Footprint','References','Status'],bom,[30,12,26,57,70,100])
    for row in range(2,sheet.max_row+1):
        sheet.cell(row,2).comment=Comment('Source: packages.json, generated from staged DL1 schematics; physical board/reference count.','DM-02')
        if sheet.cell(row,1).value in ('SST39SF040-70-4I-NHE','CD74HCT154E'):
            for cell in sheet[row]:cell.fill=PatternFill('solid',fgColor='FFF0CC')
    replacement_rows=[[old,c['part'],c['quantity'],c['footprint'],c['reason'],c['sourcing']] for old,c in choices.items()]
    add_sheet(wb,'SOIC replacements',['Previous SOIC','Selected DIP','Quantity','Footprint','Engineering change','Sourcing'],replacement_rows,[27,25,12,45,90,90])
    add_sheet(wb,'175 positions',['Board','Reference','Clock net','Reset net','Used inverted output pins','574 substitution'],
        [[r['board'],r['reference'],', '.join(r['clock']),', '.join(r['reset']),', '.join(map(str,r['complement_pins_used'])),r['reason']] for r in review['positions']],[12,15,30,30,25,85])
    stock=json.loads((HERE.parent/'owned-inventory/stock.json').read_text())
    stock_sheet=add_sheet(wb,'Owned stock',['Reported marking','Package','Owned','Owned quantity','Quantity description','Remaining details'],
        [[p['reported_marking'],p['package'],'Yes' if p['owned'] else 'No',p['quantity'],p['quantity_description'],p['missing']] for p in stock['parts']],[30,22,12,18,65,70])
    for row in range(2,stock_sheet.max_row+1):
        stock_sheet.cell(row,4).comment=Comment('Source: '+stock['source']+'. Blank means unknown; zero means explicitly none owned.','DM-02')
    source_rows=[[b['board'],b['candidate'],b['sha256']] for b in summary['boards']]
    source_rows += [[r['part'],r['source'],r['sha256']] for r in summary['manufacturer_evidence']]
    source_rows += [['Owned stock','Verification/build/owned-inventory/stock.json',sha(HERE.parent/'owned-inventory/stock.json')]]
    add_sheet(wb,'Sources',['Scope','Path','SHA-256'],source_rows,[25,100,70])
    output=HERE/'DM-02-DIP-logic-candidate-BOM.xlsx';wb.save(output)
    check=load_workbook(output);cached=load_workbook(output,data_only=True)
    assert check['Candidate BOM'].max_row==len(bom)+1
    for row,want in zip(check['Candidate BOM'].iter_rows(min_row=2),bom):assert [c.value for c in row]==want
    assert not any(c.data_type in ('f','e') for s in check for row in s for c in row)
    assert not any(c.data_type=='e' for s in cached for row in s for c in row)
    assert not any('SOIC' in r[3] for r in bom)
    totals={r[0]:r[1] for r in bom}
    assert all(totals[c['part']]==c['quantity'] for c in choices.values())
    actual_stock={r[0]:r for r in check['Owned stock'].iter_rows(min_row=2,values_only=True)}
    assert actual_stock['CD74ACT175E'][2:4]==('No',0)
    assert actual_stock['74HCT157'][3]==1
    assert 'SN74HC377N' in actual_stock and '74HCT377' not in actual_stock
    write('workbook-validation.json',dict(passed=True,sha256=sha(output),bom_rows=len(bom),formula_count=0,formula_errors=[],
        replaced_packages=91,remaining_soic=0,remaining_plcc=summary['remaining_non_dip_memory'],
        source_stock_sha256=sha(HERE.parent/'owned-inventory/stock.json')))
    replacements=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [old,c['part'],c['quantity'],c['sourcing']])+'</tr>' for old,c in choices.items())
    role_counts=defaultdict(int)
    for r in review['positions']:role_counts[r['board']]+=1
    board_rows=''.join(f'<tr><td>{esc(k)}</td><td>{v}</td></tr>' for k,v in role_counts.items())
    (HERE/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · DIP logic candidate</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:24px auto;padding:0 16px;max-width:1120px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{width:100%;table-layout:fixed;border-collapse:collapse}}td,th{{vertical-align:top;text-align:left;border-bottom:1px solid #304156;padding:10px;overflow-wrap:anywhere}}.note{{padding:12px;background:#253245;color:#ffd082}}@media(max-width:650px){{table,tbody,tr,td{{display:block}}thead{{display:none}}td{{padding:8px 0}}td:first-child{{font-weight:bold}}}}</style>
<nav><a href="/">Dashboard</a> · <a href="../owned-inventory/">Owned inventory</a> · <a href="../bom-inventory/">Earlier reference BOM</a></nav>
<h1>DIP replacements for all 91 SOIC logic ICs</h1><p><a id="workbook" href="{output.name}">Download the revised DIP-logic candidate BOM</a> · <a href="candidate-BOM.csv">CSV</a></p>
<p id="scope" class="note">DL1 has zero SOIC logic packages across {len(summary['boards'])} staged sheets. Native pin/net checks passed; integrated timing and physical qualification are pending. Eight PLCC flash ICs still need the separate owned-M27C322 conversion before the complete design meets the DIP-only requirement.</p>
<h2>Selected replacements</h2><table id="replacements"><thead><tr><th>Earlier SOIC</th><th>Selected DIP</th><th>Count</th><th>Stock / sourcing</th></tr></thead><tbody>{replacements}</tbody></table>
<h2>The 48 flip-flops</h2><p>These are 175 quad flip-flops, not 157 multiplexers. CD74ACT175E preserves their positive-edge clock, active-low asynchronous clear, complementary outputs and pin numbering. TI lists the DIP-16 part as active. The package conversion retains 48 devices.</p>
<p>The reviewed ACT limits are 2.9–11.5 ns clock-to-Q, 3.3–13 ns clear-to-Q, 2 ns setup/hold and 1 ns reset recovery, at 4.5–5.5 V and −55 to 125 °C with a 50 pF load. ACT input thresholds are 2.0/0.8 V. Existing AC175 timing and analogue results do not establish ACT receiver behaviour.</p>
<p>All 48 positions have reset connected; C1:U1, SQ1:U3 and SQ1:U5 also use complementary outputs. Your HCT574 has no asynchronous clear or complementary outputs, so it cannot directly replace these devices. The netlist has {summary['potential_273_pairs']} pairs with the same clock/reset and no used complementary outputs, worth examining for eight-bit resettable 273-style registers. That requires rewiring and timing/load checks.</p>
<table id="roles"><thead><tr><th>Board</th><th>175 packages</th></tr></thead><tbody>{board_rows}</tbody></table>
<h2>Latest stock</h2><p id="stock-update">Zero CD74ACT175E owned: source 48 for this candidate. CD74HCT161E is an exact owned match, count unknown. Owned 74HCT154N provides a decoder option for four positions; manufacturer/logo and count remain pending. The owned registers are SN74HC377N. Their CMOS-output drivers make reuse plausible, with input/load/timing checks still needed. Owned SN74HCT00N and SN74HCT08N gates require slower timing models than the selected AHCT parts. See the <a href="../owned-inventory/logic-review.json">pin-derived stock review</a>.</p>
<h2>Remaining decisions</h2><p>Exact owned alternatives need integration checks before changing the selected decoder, register and gate identities. HCT191 counter reuse and HCT574 register redesign may reduce the final package count; the quantities here describe the checked package-conversion stage.</p>
<h2>Evidence</h2><p><a href="summary.json">Native checks and fault detections</a> · <a href="choices.json">Part selections and ACT limits</a> · <a href="register-review.json">All 48 register connections</a> · <a href="packages.json">Schematic-derived packages</a> · <a href="sources/cd74act175.pdf">TI ACT175 datasheet</a> · <a href="workbook-validation.json">Workbook checks</a> · <a href="manifest.json">Publication hashes</a></p></html>''')
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and not(p.parent==HERE and p.name in excluded)}
    write('manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),files=files))
    print('Published',len(bom),'BOM rows;',len(files),'artifacts; zero SOIC, eight remaining PLCC flash ICs')


if __name__=='__main__':main()

"""Publish a stock-comparison BOM from distinct, hash-checked design scopes."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import csv
import hashlib
import html
import json
import re
import shlex
import shutil
import subprocess
import sys

from openpyxl import Workbook,load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table,TableStyleInfo
from openpyxl.utils import get_column_letter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/bom-inventory/'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.legacy import read_sheet,inventory


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def read(name):return json.loads((HERE/name).read_text())
def esc(value):return html.escape(str(value))


def assembly(footprint):
    if 'THT-Socket' in footprint:return 'PLCC IC + through-hole socket'
    if footprint.startswith(('Package_SO:','Package_DFN_QFN:')):return 'SMD'
    if not footprint:return 'Unspecified in schematic'
    if footprint=='DIP32' or any(s in footprint for s in ('DIP-','_THT:','_THT_', 'PinHeader','PinSocket','Oscillator_DIP','TO-92')):return 'Through-hole'
    return 'Other / unresolved'


def category(ref):
    return {'U':'IC','Y':'Oscillator','C':'Capacitor','R':'Resistor','J':'Connector'}.get(re.sub(r'\d.*','',ref),'Other hardware')


def aggregate(rows):
    grouped=defaultdict(list)
    for r in rows:grouped[r['value'],r['footprint'],r['category']].append(r)
    return [dict(part=value,quantity=len(items),category=kind,footprint=fp,assembly=assembly(fp),
        references=', '.join(r['board']+':'+r['reference'] for r in items),
        source_files=sorted({r['source'] for r in items}))
        for (value,fp,kind),items in sorted(grouped.items())]


def csv_file(name,headers,rows):
    with (HERE/name).open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream);writer.writerow(headers);writer.writerows(rows)


def workbook(sheets):
    wb=Workbook();wb.remove(wb.active)
    for index,(name,headers,rows,widths) in enumerate(sheets):
        ws=wb.create_sheet(name);ws.append(headers)
        for row in rows:ws.append(row)
        ws.freeze_panes='C2';ws.sheet_view.showGridLines=False
        for col,width in enumerate(widths,1):ws.column_dimensions[get_column_letter(col)].width=width
        for row in ws:
            for cell in row:
                cell.font=Font(name='Arial',size=10,color='142333')
                cell.alignment=Alignment(vertical='top',wrap_text=True)
        for cell in ws[1]:
            cell.font=Font(name='Arial',size=10,bold=True,color='FFFFFF')
            cell.fill=PatternFill('solid',fgColor='17354A')
        ws.row_dimensions[1].height=32
        for r in range(2,ws.max_row+1):ws.row_dimensions[r].height=60 if name not in ('References','Sources') else 42
        table=Table(displayName=f'BOMTable{index+1}',ref=f'A1:{get_column_letter(ws.max_column)}{ws.max_row}')
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
        ws.add_table(table)
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0;ws.print_title_rows='1:1'
        ws.sheet_properties.outlinePr.summaryRight=False
        if name=='IC inventory':
            for row in ws.iter_rows(min_row=2,min_col=8,max_col=10):
                for cell in row:
                    cell.fill=PatternFill('solid',fgColor='FFF2CC');cell.font=Font(name='Arial',size=10,color='0000CC')
                    cell.comment=Comment('User input. Record actual markings and counted stock; blank means unknown, not zero. Different logic families need review.','DM-02')
            dv=DataValidation(type='whole',operator='greaterThanOrEqual',formula1=0,allow_blank=True)
            dv.showErrorMessage=True;dv.error='Enter a whole number of chips, zero or greater.'
            ws.add_data_validation(dv);dv.add(f'I2:I{ws.max_row}')
            for r in range(2,ws.max_row+1):
                ws.cell(r,3).comment=Comment('Quantity is a source-derived count within the scope in column A, not a purchase quantity. Do not sum scopes.','DM-02')
                if ws.cell(r,5).value=='SMD':
                    ws.cell(r,5).fill=PatternFill('solid',fgColor='F8D7DA')
                    ws.cell(r,5).font=Font(name='Arial',size=10,bold=True,color='9C1C28')
        if name=='Sources':
            for r in range(2,ws.max_row+1):
                ws.cell(r,3).hyperlink=ws.cell(r,3).value
                ws.cell(r,3).font=Font(name='Arial',size=10,color='0066AA',underline='single')
    wb.active=1
    path=HERE/'DM-02-working-BOM-and-inventory.xlsx';wb.save(path)
    check=load_workbook(path)
    assert not any(c.data_type=='f' for ws in check for row in ws for c in row),'This inventory workbook intentionally contains source counts, not calculations'
    assert check['IC inventory'].max_row==len(sheets[1][2])+1
    assert all(check['IC inventory'].cell(r,c).value is None for r in range(2,check['IC inventory'].max_row+1) for c in (8,9,10))
    assert not any(c.data_type=='e' for ws in check for row in ws for c in row)
    return len(check.sheetnames)


def main():
    changes=read('changes.json');notes=read('part-notes.json')
    inv_path=ROOT/'Verification/build/assembly-repaired/inventory.json';inv=json.loads(inv_path.read_text())
    inputs={str(inv_path.relative_to(ROOT)), 'Verification/dm02/legacy.py','Verification/package-plan.json'}
    inputs.update(inv['source_hashes'])
    inputs.update(str(p.relative_to(ROOT)) for p in (ROOT/'Verification').glob('*-parts.json'))
    for c in changes:inputs.update(c['sources'])
    current=[]
    for b in inv['boards']:
        path=ROOT/b['source'];assert sha(path)==inv['source_hashes'][b['source']],b['source']
        # Reparse physical references; compare to the previously audited inventory.
        source_sheet=read_sheet(path);actual=inventory(source_sheet)
        inputs.update(c['library_source'] for c in source_sheet['components'])
        expected={(r['reference'],r['value'],r['footprint']) for r in inv['packages'] if r['board']==b['board']}
        got={(r['ref'],r['value'],r['footprint']) for r in actual['packages']}
        assert got==expected,(b['board'],'inventory differs')
        for r in actual['packages']:
            current.append(dict(board=b['board'],reference=r['ref'],value=r['value'],footprint=r['footprint'],
                category=category(r['ref']),source=b['source'],units=r['units']))
    assert len(current)==738 and len({(r['board'],r['reference']) for r in current})==738
    baseline=[];raw=[];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for path in sorted((ROOT/'Circuits/KiCad').glob('*/*.sch')):
        rel=str(path.relative_to(ROOT));inputs.add(rel)
        sheet=read_sheet(path);original=inventory(sheet)
        assert not original['issues'],(rel,original['issues'])
        inputs.update(c['library_source'] for c in sheet['components'])
        for r in original['packages']:
            baseline.append(dict(board=path.stem,reference=r['ref'],value=r['value'],footprint=r['footprint'],
                category=category(r['ref']),source=rel,units=r['units']))
        text=subprocess.check_output(['git','show',f'{head}:{rel}'],cwd=ROOT,text=True)
        archived=HERE/'sources/original-head'/rel;archived.parent.mkdir(parents=True,exist_ok=True);archived.write_text(text)
        for block in re.findall(r'^\$Comp\n(.*?)^\$EndComp',text,re.M|re.S):
            lines=block.splitlines();label=shlex.split(next(l for l in lines if l.startswith('L ')))
            if not label[2].startswith(('U','Y')):continue
            fields={int(shlex.split(l)[1]):shlex.split(l)[2] for l in lines if l.startswith('F ')}
            raw.append(dict(source=rel,reference=label[2],symbol=label[1],value=fields.get(1,''),
                unit=int(next(l for l in lines if l.startswith('U ')).split()[1])))
    write('original-symbol-instances.json',dict(commit=head,scope='Raw symbol instances, NOT physical package quantities; U? and reused units are unresolved.',instances=raw))
    write('references.json',dict(current=current,reviewed_baseline=baseline))
    full=aggregate(current);old=aggregate(baseline)
    ics=[r for r in full if r['category'] in ('IC','Oscillator')]
    # The baseline sometimes specifies a DIP footprint for only some uses of
    # the same generic part. Give the user one stock-entry row per value.
    oldgroups=defaultdict(list)
    for r in baseline:
        if r['category'] in ('IC','Oscillator'):oldgroups[r['value']].append(r)
    oldics=[]
    for value,items in sorted(oldgroups.items()):
        footprints=sorted({r['footprint'] for r in items if r['footprint']})
        unspecified=any(not r['footprint'] for r in items)
        fp='; '.join(footprints+(['some/all footprints unspecified'] if unspecified else []))
        oldics.append(dict(part=value,quantity=len(items),footprint=fp,
            assembly='Unspecified / confirm package' if unspecified else assembly(fp),
            references=', '.join(r['board']+':'+r['reference'] for r in items)))
    assert {r['part'] for r in ics}==set(notes)
    for r in ics:r.update(notes[r['part']])
    smd=sum(r['quantity'] for r in ics if r['assembly']=='SMD')
    assert smd==91 and len([r for r in ics if r['assembly']=='SMD'])==6
    # These are documented inventory-matching paths, not automatic substitutions.
    tht=[
        ['CD74AC175M96',48,'None verified','Do not guess an E suffix or apply HCT175 timing as AC175 timing.','Verification/vendor/clock/cd74ac175.txt'],
        ['CD74HCT154M96',4,'CD74HCT154E / CD74HCT154EN','Historical family ordering table lists PDIP; current extracted addendum does not establish these order codes.','Verification/vendor/controller/cd74hct154.txt'],
        ['CD74HCT161M96',5,'CD74HCT161E','Archived addendum: NRND, Production, PDIP-16. Existing stock remains relevant.','Verification/vendor/pc/cd74hct161.txt'],
        ['CD74HCT377M96',2,'CD74HCT377E','Archived addendum: Active, Production, PDIP-20.','Verification/vendor/alu/cd74hct377.txt'],
        ['SN74AHCT00DR',16,'SN74AHCT00N','Archived addendum: Active, Production, PDIP-14.','Verification/vendor/controller/sn74ahct00.txt'],
        ['SN74AHCT08DR',16,'SN74AHCT08N','Archived addendum: NRND, Production, PDIP-14. Existing stock remains relevant.','Verification/vendor/pc/sn74ahct08.txt']]
    for row in tht:
        inputs.add(row[4]);text=(ROOT/row[4]).read_text()
        if row[2]!='None verified':assert all(p.strip() in text for p in row[2].split('/'))
    options=[
        ['ACH-4.000MHZ-EK',1,'Through-hole DIP-8','Alternative to the single ECS oscillator','Separate 4 MHz experiment; not added to normal FD1 quantities.','IC14'],
        ['TPS389050GQDSERQ1',1,'SMD WSON-6','Research candidate for reset frontend','Static screen only; no complete supervisor circuit selection.','IC15'],
        ['PLCC32 through-hole sockets',8,'Through-hole socket','Additional physical items if the eight PLCC flashes are used','Exact socket MPN/tail mapping remains unresolved. The main BOM counts chips, not these eight sockets.','IC01'],
        ['C315C104K5R5TA',3,'Through-hole radial','Replaces three generic CD1 100 nF capacitors only in P3 study','Not three extra capacitors. Lead forming / insertion tolerance remains open.','P3 study'],
        ['M27C322-100F1',1,'Through-hole FDIP-42','Earlier AL1 alternative to the eight-flash AL2 architecture','Legacy timing-study part. User may own M27C322; full speed marking is needed. Do not add both architectures.','IC01'],
        ['Optional DIP sockets',None,'Through-hole','Assembly choice','Quantity/type depends on the chosen IC inventory and whether sockets are desired.',''],
        ['Front-panel switches / reset conditioning',None,'Mostly through-hole preference','Incomplete interface hardware','Original controls exist in reviewed baseline; candidate frontend is unfinished.','IC14, IC15'],
        ['Power entry, bulk capacitors, mechanics, display electronics',None,'Unselected','Unfinished assembly items','Not represented by a complete procurement-ready BOM.','']]
    inputs.update(['Verification/build/cd1-decoupling/summary.json','Verification/build/clock-ach/interface.json'])
    manifests=[]
    for name in sorted(inputs):
        source=ROOT/name;dest=HERE/'sources/current'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest);manifests.append(dict(source=name,sha256=sha(dest),archived=str(dest.relative_to(HERE))))
    write('source-manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),git_head=head,sources=manifests))
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),current_scope='One FD1 system: 13 final module sheets plus BP1; AL2 occupies AL1 connector slot; DF1 sheet implements DF2.',
        physical_references=len(current),current_bom_groups=len(full),ic_packages=sum(r['quantity'] for r in ics if r['category']=='IC'),
        oscillators=sum(r['quantity'] for r in ics if r['category']=='Oscillator'),ic_and_oscillator_types=len(ics),
        smd_ic_packages=smd,smd_ic_types=6,plcc_ic_packages=8,
        dip_ic_packages=sum(r['quantity'] for r in ics if r['category']=='IC' and r['assembly']=='Through-hole'),
        reviewed_baseline_references=len(baseline),reviewed_baseline_ic_and_oscillator_packages=sum(r['quantity'] for r in oldics),
        changes=len(changes),source_hashes_verified=True,user_inventory_confirmed=False,procurement_ready=False,
        notes=['Do not sum current, reviewed-baseline and alternative scopes.',
            'Reviewed baseline covers seven incomplete original sheets with annotation/gate-allocation repairs; it is not a complete old machine BOM.',
            'Quantities count physical board/reference packages, not gates or HDL instances.',
            'Connector values are functional labels; exact manufacturer/gender/mating choices remain unselected.',
            'The 4 MHz target still requires a compatible oscillator/reset solution; the drawn ECS is 8 MHz.',
            'Through-hole is the user preference. Existing inventory is not yet confirmed; SMD rows are explicit reconciliation work.'])
    write('bom.json',dict(summary=summary,current=full,reviewed_baseline=old,changes=changes,options=options,through_hole_paths=tht))
    write('summary.json',summary)
    invheaders=['Scope','Part / schematic value','Quantity in scope','Package / footprint','Assembly','Change IDs','Previous part / role','Owned full markings','Owned quantity','Inventory notes','References']
    invrows=[['FD1 candidate',r['part'],r['quantity'],r['footprint'],r['assembly'],r['changes'],r['previous'],None,None,None,r['references']] for r in ics]
    invrows += [['Reviewed baseline',r['part'],r['quantity'],r['footprint'] or 'Unspecified',r['assembly'],'See change log','Original-role comparison; not additive to FD1',None,None,None,r['references']] for r in oldics]
    bomheaders=['Category','Part / value','Quantity','Assembly','Footprint','References','Status']
    bomrows=lambda data:[[r['category'],r['part'],r['quantity'],r['assembly'],r['footprint'] or 'Unspecified',r['references'],
        notes.get(r['part'],{}).get('note','Generic value/footprint; exact manufacturer and assembly selection unresolved.')] for r in data]
    csv_file('IC-inventory.csv',invheaders,invrows)
    csv_file('current-BOM.csv',bomheaders,bomrows(full))
    csv_file('reviewed-baseline-BOM.csv',bomheaders,bomrows(old))
    changeheaders=['ID','Area','Before','After','Change type','Status','Explanation','Source paths']
    changerows=[[c[k] for k in ('id','area','before','after','kind','status','detail')]+['; '.join(c['sources'])] for c in changes]
    csv_file('IC-replacements.csv',changeheaders,changerows)
    instructions=[
        ['Purpose','Working BOM and inventory comparison. This records what has been modelled, including substitutions that conflict with a predominantly through-hole build.'],
        ['Edit these cells','IC inventory: yellow columns H–J only (owned full markings, owned quantity, inventory notes). Other columns are source-derived facts. Blank stock fields mean unknown, not zero.'],
        ['Example only; not actual inventory','For a SN74HCT574N row: H = SN74HCT574N (TI); I = 6; J = DIP-20, drawer B2. This example is not included as stock data.'],
        ['Scopes','FD1 candidate, reviewed baseline and options are alternatives/comparisons. Do not sum their quantities.'],
        ['Current candidate',f'{summary["ic_packages"]} IC packages plus one oscillator across 13 module sheets and BP1. {smd} ICs are SMD, {summary["dip_ic_packages"]} are DIP, eight are PLCC.'],
        ['Through-hole mismatch','Six proposed SMD IC types remain explicit reconciliation work. See THT paths. No inventory is assumed present or absent.'],
        ['Pin compatibility is insufficient','HCT, HC, AHCT, AHC, AC, ACT and LS parts have different thresholds/timing. Record the full markings and speed suffixes.'],
        ['Current clock inconsistency','ECS-100AX-080 is the drawn 8 MHz oscillator; FD1 timing targets 4 MHz. The ACH 4 MHz experiment is a separate alternative, not an extra device to purchase.'],
        ['PLCC distinction','SST39SF040 chips are PLCC, not DIP. The main BOM counts eight chips; eight separate through-hole sockets are additional physical items if this architecture is retained.'],
        ['Reviewed baseline','Seven original sheets after annotation, identity and gate-allocation repairs. Controller/PC implementation was incomplete there; these baseline counts are not a complete original-machine BOM.'],
        ['Original repository','Raw HEAD schematics and symbol-instance data are archived. U? references/reused units and incorrect ALU value labels prevent treating raw instances as package quantities.'],
        ['Alternatives and missing items','See Options and gaps. Supervisor, sockets, bulk supply, mechanics and display are not a finished purchasing list. P3 capacitors replace existing CD1 capacitor positions.'],
        ['Quantity derivation','Each board/reference counts once; multiunit logic symbols count as one package. Full BOM keeps separate functional connector labels; exact connector manufacturer/gender is still unselected.'],
        ['Source traceability','References tab maps every counted physical component to its schematic. Sources tab links archived inputs and their SHA-256 hashes.'],
        ['No calculated shortages','Owned-part equivalence must be checked before subtracting inventory from proposed requirements. This workbook has no formulas.'],
        ['User preference','Predominantly through-hole; compare actual stock before choosing substitutions or committing the operating frequency.']]
    sheets=[
        ('Start',['Topic','Instructions'],instructions,[32,125]),
        ('IC inventory',invheaders,invrows,[24,28,14,42,30,22,52,34,16,45,65]),
        ('Current BOM',bomheaders,bomrows(full),[20,32,12,30,46,72,80]),
        ('IC replacements',changeheaders,changerows,[12,26,52,70,34,38,110,70]),
        ('Reviewed baseline',bomheaders,bomrows(old),[20,32,12,30,46,72,80]),
        ('THT paths',['Selected SMD part','FD1 qty','Documented DIP path','Archived evidence / condition','Source'],tht,[28,12,36,95,72]),
        ('Options and gaps',['Part / item','Quantity if used','Assembly','Relationship to current BOM','Condition','Change IDs'],options,[42,18,32,70,110,20]),
        ('References',['Scope','Board','Reference','Part / value','Category','Footprint','Symbol units','Source'],
            [[scope,r['board'],r['reference'],r['value'],r['category'],r['footprint'],','.join(map(str,r['units'])),r['source']]
             for scope,items in [('FD1',current),('Reviewed baseline',baseline)] for r in items],[24,28,14,30,22,48,16,80]),
        ('Sources',['Source path','SHA-256','Archived URL'],[[r['source'],r['sha256'],BASE+r['archived']] for r in manifests],[90,70,130])]
    sheet_count=workbook(sheets)
    # User-facing HTML: current IC list first, complete files one click away.
    currentrows=''.join(f'<tr data-assembly="{esc(r["assembly"])}"><td>{esc(r["part"])}</td><td>{r["quantity"]}</td><td class="{ "smd" if r["assembly"]=="SMD" else ""}">{esc(r["assembly"])}</td><td>{esc(r["previous"])}<p>{esc(r["note"])}</p><a href="#change-{r["changes"].split(",")[0]}">{esc(r["changes"])}</a><details><summary>References</summary>{esc(r["references"])}</details></td></tr>' for r in ics)
    oldrows=''.join(f'<tr><td>{esc(r["part"])}</td><td>{r["quantity"]}</td><td>{esc(r["assembly"])}</td><td>{esc(r["references"])}</td></tr>' for r in oldics)
    changelist=''.join(f'<article id="change-{c["id"]}"><h3>{c["id"]}: {esc(c["area"])}</h3><p><b>Before:</b> {esc(c["before"])}<br><b>Current proposal:</b> {esc(c["after"])}</p><p>{esc(c["detail"])}</p><small>{esc(c["kind"])} · {esc(c["status"])}</small></article>' for c in changes)
    thtrows=''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in r[:4])+'</tr>' for r in tht)
    optionrows=''.join('<tr>'+''.join(f'<td>{esc(v) if v is not None else "TBD"}</td>' for v in r[:5])+'</tr>' for r in options)
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · working BOM and inventory</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1150px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.downloads{{display:flex;flex-wrap:wrap;gap:12px}}.downloads a{{padding:10px 15px;background:#234863;border-radius:6px}}.notice{{color:#ffd082}}.smd{{color:#ff9eab;font-weight:bold}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}#current th:first-child{{width:23%}}#current th:nth-child(2){{width:7%}}#current th:nth-child(3){{width:20%}}article{{border-top:1px solid #304156;padding:10px 0}}input,select{{font:inherit;padding:9px;max-width:100%;box-sizing:border-box}}.filters{{display:flex;flex-wrap:wrap;gap:12px;margin:15px 0}}summary{{cursor:pointer;color:#8acfff}}small{{color:#b9c7d8}}@media(max-width:700px){{main{{padding:18px 10px}}section{{padding:12px}}th,td{{padding:5px;font-size:12px}}h1{{font-size:28px}}}}</style>
<main><nav><a href="/">Live verification dashboard</a> · <a href="../clock-ach/">4 MHz oscillator experiment</a> · <a href="../assembly-repaired/">Earlier assembly audit</a></nav>
<h1>Working BOM and inventory comparison</h1><p>The current candidate has <b>{summary['ic_packages']} IC packages and one oscillator</b>: {summary['dip_ic_packages']} DIP ICs, {smd} SMD ICs and eight PLCC flash ICs. The SMD selections are highlighted for reconciliation with your through-hole stock.</p>
<div class="downloads"><a href="DM-02-working-BOM-and-inventory.xlsx" download>Download Excel inventory workbook</a><a href="IC-inventory.csv" download>IC inventory CSV</a><a href="current-BOM.csv" download>Full current BOM CSV</a><a href="IC-replacements.csv" download>IC changes CSV</a></div>
<p>In the workbook, fill the yellow columns with the full chip markings, quantity owned and notes. Blank inventory cells mean unknown. There is a separate reviewed-baseline list so you can also check chips that the candidate replaced.</p>
<p class="notice">This records the design so far. Your stock is unconfirmed, through-hole is the preference, and the BOM still needs reconciliation before it becomes a purchasing list. The current, baseline and alternative quantities must not be added together.</p>
<section><h2>Current candidate ICs</h2><p>One FD1 system: 13 final module sheets plus BP1. AL2 is named AL1 at the connector interface; DF1 is the sheet name for DF2. Each physical board/reference is counted once. Historical standalone variants and PCB experiments are excluded from these totals.</p>
<div class="filters"><label>Find a part <input id="search" type="search" placeholder="Part, previous role or reference"></label><label>Assembly <select id="assembly"><option value="">All</option><option>SMD</option><option>Through-hole</option><option>PLCC IC + through-hole socket</option></select></label></div><p id="count">{len(ics)} part types</p>
<table id="current"><thead><tr><th>Part as modelled</th><th>Qty</th><th>Assembly</th><th>What changed / inventory note</th></tr></thead><tbody>{currentrows}</tbody></table>
<p>The complete schematic inventory contains {len(current)} component references: 288 ICs, one oscillator, 289 capacitors, three resistors and 157 connector positions. The connector count includes both module-side and backplane-side positions; exact mating parts and gender are unfinished. The workbook also includes every reference and footprint.</p></section>
<section><h2>Through-hole paths to check against your stock</h2><p>The archived manufacturer documents support the following leads. They have not been substituted into the current schematics. NRND means “not recommended for new designs”; it does not by itself disqualify an existing chip. Package pinout and timing still need checking.</p><table id="tht"><thead><tr><th>Selected SMD part</th><th>Qty</th><th>Documented DIP path</th><th>Evidence / condition</th></tr></thead><tbody>{thtrows}</tbody></table>
<p>The largest unresolved item is the 48 AC175 register packages. I have not established a through-hole replacement with the same limits. Lowering the operating frequency or adapting the register implementation may be appropriate once the actual inventory is known.</p></section>
<section><h2>IC substitutions and additions</h2><p>Some changes replace a chip; others redesign an entire function or add buffering/staging. The notes identify that distinction. Quantities mentioned in different change entries can overlap and are not a second BOM.</p>{changelist}</section>
<section><h2>Reviewed original-design ICs</h2><p>This covers the seven original KiCad sheets after annotation, identity and gate-allocation repairs: {summary['reviewed_baseline_ic_and_oscillator_packages']} IC/oscillator packages. The original controller/program-counter implementation was incomplete, so this is not a like-for-like whole-machine count. Raw repository labels and U? symbol instances are preserved in the source archive.</p>
<table id="baseline"><thead><tr><th>Reviewed schematic value</th><th>Qty</th><th>Package information</th><th>References</th></tr></thead><tbody>{oldrows}</tbody></table><p><a href="reviewed-baseline-BOM.csv">Full reviewed-baseline BOM</a> · <a href="original-symbol-instances.json">Original raw labels and symbol instances</a></p></section>
<section><h2>Alternatives and unfinished assembly items</h2><table id="options"><thead><tr><th>Item</th><th>Qty if used</th><th>Assembly</th><th>Relationship</th><th>Condition</th></tr></thead><tbody>{optionrows}</tbody></table>
<p>Exact passive manufacturers, socket mechanics, power entry, bulk capacitance, front-panel/reset hardware and display electronics remain incomplete. The separate ACH and supervisor experiments are not silently included as installed components.</p></section>
<section><h2>Sources and verification</h2><p>The current BOM was reparsed from its 14 source sheets and matched against the earlier 738-reference assembly audit. Quantities collapse multiunit gates into physical packages. The 72-input ACH study and prior publications remain unchanged.</p><nav><a href="bom.json">Structured BOM</a> · <a href="references.json">Every physical reference</a> · <a href="source-manifest.json">Source snapshot hashes</a> · <a href="summary.json">Counts and scope</a> · <a href="validation.json">Workbook and count checks</a> · <a href="manifest.json">Published hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main>
<script>const rows=[...document.querySelectorAll('#current tbody tr')];function filter(){{const q=document.querySelector('#search').value.toLowerCase(),a=document.querySelector('#assembly').value;let n=0;for(const r of rows){{r.hidden=!(r.textContent.toLowerCase().includes(q)&&(!a||r.dataset.assembly===a));if(!r.hidden)n++;}}document.querySelector('#count').textContent=n+' of '+rows.length+' part types';}}document.querySelector('#search').addEventListener('input',filter);document.querySelector('#assembly').addEventListener('change',filter);</script></html>'''
    (HERE/'index.html').write_text(page)
    # Verify the actual exported quantities, not just the input objects.
    wb=load_workbook(HERE/'DM-02-working-BOM-and-inventory.xlsx',data_only=True)
    actual_total=sum(row[2] for row in wb['Current BOM'].iter_rows(min_row=2,values_only=True))
    assert actual_total==738
    stock=list(wb['IC inventory'].iter_rows(min_row=2,values_only=True))
    assert sum(r[2] for r in stock if r[0]=='FD1 candidate')==289
    assert sum(r[2] for r in stock if r[0]=='FD1 candidate' and r[4]=='SMD')==91
    assert len([r for r in stock if r[0]=='FD1 candidate'])==19
    assert all(len(row)==len(invheaders) for row in invrows)
    assert sum(r['quantity'] for r in full)==len(current)
    assert sum(r['quantity'] for r in old)==len(baseline)
    for row in manifests:assert sha(ROOT/row['source'])==row['sha256'],'Source changed during BOM build'
    write('validation.json',dict(passed=True,current_references=738,current_ics_and_oscillator=289,current_ic_types=19,
        smd_ics=91,source_parity=True,workbook_sheets=sheet_count,inventory_rows=len(invrows),
        user_inventory_cells_blank=True,formula_cells=0,excel_error_cells=0,
        baseline_references=len(baseline),baseline_ic_rows=len(oldics),changes=len(changes)))
    print('BOM:',summary['ic_packages'],'ICs + oscillator;',smd,'SMD ICs;',len(full),'full BOM groups;',len(invrows),'inventory rows;',sheet_count,'workbook sheets')


if __name__=='__main__':main()

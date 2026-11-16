"""Publish LL1 inventory with a searchable per-driver matrix."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.common import digest,write_json
from dm02.reporting import freshness
from dm02 import cp1,link_loads_evidence
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-link-loads/'


def snapshot():
    assert not (HERE/'manifest.json').exists(),'Preserve publication; use --verify-only'
    report=json.loads((ROOT/'Verification/build/report.json').read_text())
    assert freshness(report)['fresh'] and report['link_loads']['revision']=='CP1-LL1'
    assert not any(c['status']=='error' for c in report['checks'])
    assert [m['passed'] for m in report['milestones']]==[3,3,8]
    cp1.verify_hashes(ROOT/'Verification/build',report['artifact_hashes'])
    lock,inventory=link_loads_evidence.load()
    mapping={'report.json':'Verification/build/report.json','load-notes.md':'Verification/Link-loads.md',
        'smoke.log':'Verification/build/cp1/smoke.log','tests.log':'Verification/build/tests.log',
        'equivalence.json':'Verification/build/cp1/equivalence.json','study.css':'Verification/build/cp1-readiness/study.css'}
    for name in list(lock['source_hashes'])+['Verification/link-loads-evidence.json','Verification/tests/test_link_loads.py',
        'Verification/tests/test_cp1.py','Verification/dm02/cp1.py','Verification/dashboard/app.js']:
        mapping['source-snapshot/'+name]=name
    hashes={}
    for dest,name in mapping.items():
        source=ROOT/name;target=HERE/dest;target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(source);shutil.copyfile(source,target)
        assert digest(source)==digest(target)==before;hashes[name]=before
    text='''# Whole-link electrical load inventory

**CP1-LL1 counts every CA1 physical pin:** 7,324 pins, 2,018 fitted contact pins, 864 mating pairs and 1,708 potential-driver scenarios. All 19 HCT245 transceivers have DIR tied high. The inventory includes 39 pull resistors and TX1's 1 kΩ terminal series resistor.

| Path | IC-only subtotal | Finding |
| --- | --- | --- |
| MAR0–13 | 44 pF each | 49 pF with the old 5 pF planning allowance |
| MAR14–15 | 48 pF each | 53 pF with that allowance exceeds the 50 pF screen |
| DATA0–3 / DATA4–7 | 100 / 90 pF | Exceeds the HCT245 50 pF disable fixture; 150 pF data/enable fixture is separate |
| SRAM RAM0–7 | 20 pF | Exceeds the 5 pF release fixture; read fixture is 30 pF |
| Both ACH oscillators | 10 pF | 5 pF remains before socket/routing/probe loads |

These are conditional table maxima and allocations. **Complete physical load totals remain unknown.** The matrix does not establish actual failure or physical timing acceptance. CP1-R2 remains accepted, with milestone gates 3/5, 3/5 and 8/9.

- [Search all 1,708 driver scenarios](drivers.html)
- [Complete pin/net/contact inventory](final/inventory.json)
- [Method, conditions and findings](load-notes.md)
- [Five detected mutations](final/mutations.json)
- [Manufacturer source provenance](sources/manifest.json)
- [Bounded replay report](report.json)
- [Harness log](tests.log)

## Manufacturer reviews

The capacitance columns retain their source conditions. HCT245 A/B ports use an unguaranteed 10 pF allocation. Memory capacitance limits apply at 25 °C; AHC/AHCT input rows generally apply at 5 V. Other output pins use the stated allocation or conditional table value. No unknown socket/contact/trace/cable/probe term is silently set to zero.

| Candidate part | Input pF | Status | Source |
| --- | --- | --- | --- |
'''
    for name,p in inventory['parts'].items():
        text+=f'| {name} | {p["input_pf"] if p["input_pf"] is not None else "—"} | {p["input_status"]} | [manufacturer excerpt]({p["source"]}) |\n'
    text+='''
## Reproduction and preserved attempts

The evidence lock regenerates the complete inventory from CA1's exported pins and declared mating pairs. It compares 1,089 earlier R2 rows, 179 BR1 rows and 150 TX1 rows. Five mutations reject omitted receivers, contacts and resistors, an unjustified data-port maximum, and aliased CPU-card domains. Eight focused tests also cover duplicate counting, SRAM bidirectional pins, MAR loading and oscillator headroom.

Earlier source-collection attempts and both inventory iterations remain archived. The final version uses the exact ACT175 source, adds the complete TX1 comparison and separates W27C512's 30 pF high-speed fixture from its historical 50 pF default. Restore earlier studies through `Backup/README.md` before bounded replay.
'''
    (HERE/'index.md').write_text(text)
    (HERE/'loads.css').write_text('table { display:block; overflow-x:auto; max-width:100%; } td { overflow-wrap:anywhere; } input { width:100%; padding:.8rem; box-sizing:border-box; } #matrix { font-size:.8rem; } #error { color:#b22; }\n')
    subprocess.run(['pandoc',str(HERE/'index.md'),'--standalone','--metadata','title=DM-02 whole-link load inventory',
        '--css','study.css','--css','loads.css','-o',str(HERE/'index.html')],check=True)
    (HERE/'drivers.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>DM-02 LL1 driver matrix</title><link rel="stylesheet" href="study.css"><link rel="stylesheet" href="loads.css"></head><body>
<main><p><a href="index.html">LL1 study</a> · <a href="final/inventory.json">Full pin-level JSON</a></p><h1>Per-driver load matrix</h1>
<p>IC-only subtotals contain conditional maxima and allocations. All complete physical totals remain unknown. Each scenario assumes its named driver is active and other potential drivers are inactive. Contact counts include both physical sides.</p>
<label for="search">Filter by native net, physical driver or original module/reference</label><input id="search" type="search" placeholder="For example U8006.7, DATA0 or TX1"><p id="count">Loading…</p><p id="error"></p>
<table id="matrix"><thead><tr><th>Driver / original</th><th>Part</th><th>Native net</th><th>IC-only pF</th><th>Contact pins</th><th>Fixture comparisons</th></tr></thead><tbody></tbody></table></main><script src="drivers.js"></script></body></html>''')
    (HERE/'drivers.js').write_text('''"use strict";
fetch("final/inventory.json").then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(data=>{
 const rows=[];const body=document.querySelector("tbody");
 for(const net of data.nets)for(const s of net.scenarios){
  const pin=data.pins[s.driver],row=document.createElement("tr");
  const fields=[s.driver+" / "+pin.board+" "+pin.source_reference+"."+pin.pin,pin.part,net.native_names.join(" · "),String(s.ic_only_pf),String(net.contacts.length),s.screens.map(f=>f.arc+": "+f.load_pf+" pF; "+(f.ic_only_exceeds?"IC subtotal EXCEEDS":f.legacy_5pf_exceeds?"+5 pF EXCEEDS":"unknown parasitics pending")).join("; ")];
  for(const field of fields){const td=document.createElement("td");td.textContent=field;row.append(td)}
  body.append(row);rows.push({row,text:fields.join(" ").toLowerCase()});
 }
 function filter(){const query=document.querySelector("#search").value.toLowerCase();let count=0;for(const r of rows){r.row.hidden=!r.text.includes(query);if(!r.row.hidden)count++}document.querySelector("#count").textContent=count+" / "+rows.length+" driver scenarios"}
 document.querySelector("#search").addEventListener("input",filter);filter();
}).catch(e=>{document.querySelector("#error").textContent="Inventory load failed: "+e.message});
''')
    write_json(HERE/'snapshot.json',dict(passed=True,source_hashes=hashes,
        harness=next(c['summary'] for c in report['checks'] if c['id']=='harness'),
        physical_qualification=False,milestones_passed=[3,3,8]))
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','matrix.png'}
    files={str(p.relative_to(HERE)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and
        (p.parent!=HERE or p.name not in excluded)}
    write_json(HERE/'manifest.json',dict(files=files))


def verify():
    files=json.loads((HERE/'manifest.json').read_text())['files']
    def check(item):
        name,record=item;assert digest(HERE/name)==record['sha256'],name
        with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
            actual=hashlib.sha256(response.read()).hexdigest()
        assert actual==record['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,files.items()))
    write_json(HERE/'remote-validation.json',dict(passed=True,checked_hashes=len(checked),base_url=BASE))
    print('Verified',len(checked),'published hashes:',BASE)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if not a.verify_only:snapshot()
    verify()

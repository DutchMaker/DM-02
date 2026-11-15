"""Publish nominal DIP alternatives while retaining the original working BOM."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import html
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
def esc(v):return html.escape(str(v))


def main():
    summary,audit=read('summary.json'),read('audit.json');assert summary['passed'] and audit['passed']
    for b in summary['boards']:
        assert sha(ROOT/b['source'])==b['source_sha256']
        assert sha(HERE/b['candidate'])==b['candidate_sha256']
    for r in audit['original_inputs']:assert sha(HERE/r['file'])==r['sha256']
    for r in summary['footprints'].values():assert sha(HERE/r['archived'])==r['sha256']
    counts=Counter((r['before'],r['after']) for r in summary['changes'])
    parts=''.join(f'<tr><td>{esc(old)}</td><td>{esc(new)}</td><td>{count}</td></tr>' for (old,new),count in sorted(counts.items()))
    boards=''.join(f'<tr><td>{b["board"]}</td><td>{b["changes"]}</td><td>{b["native"]["physical_pins"]}</td><td><a href="{b["candidate"]}">Legacy sheet</a> · <a href="native/{b["board"]}/{b["native"]["sheet"]}.kicad_sch">Native KiCad</a> · <a href="native/{b["board"]}/{b["native"]["sheet"]}.xml">Netlist</a></td></tr>' for b in summary['boards'])
    faults=''.join(f'<li>{esc(r["fault"])}: rejected by {esc(r["diagnostic"])}</li>' for r in audit['faults'])
    source_links=''.join(f'<li><a href="sources/{Path(r["source"]).name}">{r["part"]}: archived manufacturer table</a></li>' for r in summary['sources'])
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · DIP package screen</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1050px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #304156;overflow-wrap:anywhere}}@media(max-width:700px){{section{{padding:12px}}td,th{{padding:5px;font-size:12px}}}}</style>
<main><nav><a href="../bom-inventory/">Working BOM and inventory workbook</a> · <a href="/">Live dashboard</a></nav><h1>Through-hole package alternatives</h1>
<p class="pass">Four documented DIP part variants cover 39 proposed SMD packages across nine sheets. Nominal pad-number coverage and native KiCad net equivalence pass.</p>
<p class="notice">These are isolated package candidates. The published working BOM still records the parts originally modelled, so it remains a consistent inventory-comparison snapshot. User stock, package-specific timing applicability and physical assembly fit remain open.</p>
<section><h2>Parts screened</h2><table id="parts"><thead><tr><th>Current SMD selection</th><th>Documented DIP variant</th><th>Packages</th></tr></thead><tbody>{parts}</tbody></table>
<p>The archived package addenda list CD74HCT377E and SN74AHCT00N as Active; CD74HCT161E and SN74AHCT08N as NRND. These are archived status statements, not a stock check. NRND does not itself rule out an existing chip in your inventory.</p>
<p>The package edits preserve the logic family and function. Each affected reference has a matching DIP pin set, and the installed footprints use through-hole pads. This establishes nominal pad numbering, not lead diameter, insertion tolerance, socket body clearance or assembled electrical performance.</p><ul>{source_links}</ul></section>
<section><h2>Independent export checks</h2><p>The parser confirms all pre-edit pin groups are preserved. KiCad imports the original symbol libraries and independently exports the nine edited sheets; its native results agree. A second check verifies {audit['parts_verified']} exported component values/footprints and {audit['net_groups_verified']} net groups, including unchanged components. The 39 changed packages contain {audit['changed_package_pads']} pads.</p>
<table id="boards"><thead><tr><th>Module</th><th>Changed packages</th><th>Native pins compared</th><th>Candidate files</th></tr></thead><tbody>{boards}</tbody></table>
<p>Three saved XML mutations exercise the exported-evidence checker:</p><ul id="faults">{faults}</ul>
<nav><a href="summary.json">Package-screen results</a> · <a href="audit.json">Identity audit and faults</a> · <a href="check.py">Candidate generator/checker</a> · <a href="audit.py">Export auditor</a></nav></section>
<section><h2>Remaining through-hole decisions</h2><p>If all four variants are adopted, the candidate's SMD IC count would fall from 91 to 52: 48 AC175 registers and four HCT154 decoders. The eight PLCC flash ICs are a separate package issue; a through-hole socket does not make the IC a DIP part.</p>
<p>The archived HCT154 family table contains historical DIP part codes, but their current status and exact owned markings need checking. A through-hole AC175 replacement with the required limits has not been qualified. The operating frequency and register architecture can be revisited once the actual stock is known.</p>
<p>Reproduce with <code>python3 Verification/build/tht-package-screen/check.py</code>, then <code>audit.py</code>, <code>publish.py</code> and <code>verify_publication.py</code> in the same directory. Python, KiCad CLI and its installed footprint libraries are required. All normal-source hashes are checked before publication.</p>
<nav><a href="manifest.json">Published file hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*')) if p.is_file()
        and '__pycache__' not in p.parts and p.suffix!='.pyc' and not(p.parent==HERE and p.name in excluded)}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n')
    print('Published',len(files),'DIP-screen artifacts')


if __name__=='__main__':main()

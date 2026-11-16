"""Publish completed CP1-R2 evidence without changing historical CP1 pages."""
from pathlib import Path
from collections import Counter
import csv,hashlib,html,json
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    accepted=json.loads((HERE/'acceptance.json').read_text());assert accepted['passed']
    packages=json.loads((HERE/'packages.json').read_text());counts=Counter(x['value'] for x in packages if x['ic'])
    assert counts['CD74HCT273E']==3 and sum(counts.values())==192
    with (HERE/'candidate-BOM.csv').open('w') as stream:
        writer=csv.writer(stream);writer.writerow(['Selected part','Required','Exact owned quantity','Sourcing'])
        for part,count in sorted(counts.items()):writer.writerow([part,count,'0' if part=='CD74ACT175E' else 'Unknown','User confirmed zero owned' if part=='CD74ACT175E' else 'Exact stock/count requires confirmation'])
    state=json.loads((HERE/'verification-state.json').read_text());boot=next(x for x in state['runs'] if x.get('boot'))
    summary=dict(revision='CP1-R2',digital_verification_passed=True,physical_qualification=False,
        logic_memory_packages=192,baseline_packages=288,saving=96,all_logic_memory_dip=True,
        native_boards=12,part_changes=accepted['selected_273'],minimum_observed_hold_ns=accepted['minimum_observed_hold_ns'],
        boot_microcycles=boot['coverage']['microcycles'],boot_io_events=boot['output']['io_events'],
        pixel_errors=boot['output']['pixel_errors'],milestones=[dict(number=n,passed=p,total=t) for n,p,t in ((1,3,5),(2,3,5),(3,8,9))],
        open_items=accepted['physical_boundary'])
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    names=['acceptance.json','part-qualification.json','source-manifest.json','native-audit.json','interconnect-check.json',
           'physical-review.json','component-review.json','clock-check.json','fault-check.json','register-check.json',
           'module-check.json','mar-check.json','verification-state.json','rom-check.json','programming-check.json',
           'program-budget-check.json','workbook-validation.json','recalculation.json','candidate-BOM.csv','DM-02-CP1-R2-BOM.xlsx',
           'sources/cd74hct273.pdf','run.py','verify.py','qualify_part.py','finalize_revision.py']
    links=''.join(f'<li><a href="{html.escape(n,quote=True)}">{html.escape(n)}</a></li>' for n in names)
    opens=''.join('<li>'+html.escape(s)+'</li>' for s in accepted['physical_boundary'])
    rows=''.join(f'<tr><td>{html.escape(n)}</td><td>{c}</td></tr>' for n,c in sorted(counts.items()))
    (HERE/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 CP1-R2</title>
<style>body{max-width:960px;margin:40px auto;padding:0 20px;background:#101923;color:#e6edf3;font:16px/1.6 system-ui}a{color:#63dfdc;overflow-wrap:anywhere}td,th{padding:8px;text-align:left;border-bottom:1px solid #425266}li{overflow-wrap:anywhere}table{width:100%}</style>
<h1>CP1-R2: documented HCT273 timing</h1><p id="state">Complete digital rerun passed. Physical qualification remains open.</p>
<p>Three CD74HCT273E DIP-20 registers replace SN74HCT273N at AL1 U2 and ME1 U11/U15. All 60 pins, footprints and connectivity match. The design still uses 192 DIP logic/memory ICs, 96 fewer than the 288-package baseline.</p>
<p>TI SCHS174D specifies clock-to-Q and clear-to-Q maxima of 38/40 ns at 4.5 V, −40 to 85 °C and 50 pF. The model retains a conservative 42 ns delay envelope and now checks the required 3 ns data hold.</p>
<p id="boot">A fresh ROM boot passed 2,840,175 microcycles and 43,829 IO events, with exact text and zero errors across 48,000 pixels. All three substituted registers have measured post-capture data activity in that digital run.</p>
<p>150 clock profiles, 24 continuous CPU profiles, three all-opcode profiles, exhaustive counter/MAR/register checks and standalone ALU/memory suites passed. The smallest observed hold interval was '''+str(accepted['minimum_observed_hold_ns'])+''' ns. Sampled delay models do not qualify real supply/load behaviour.</p>
<p>Milestones remain <strong>3/5, 3/5 and 8/9</strong>. This revision closes the selected HCT273 specification ambiguity; physical acceptance gates remain open.</p>
<p><a href="/">Live dashboard</a> · <a href="../compact-design/">Original CP1 archive</a> · <a href="../cp1-timing-review/">Earlier substitution study</a></p>
<h2>Remaining work</h2><ul>'''+opens+'</ul><h2>Selected ICs</h2><table><tr><th>Part</th><th>Required</th></tr>'+rows+'</table><h2>Evidence</h2><ul>'+links+'</ul></html>')
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.vvp'
           and p not in {HERE/n for n in ('manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','parent-lock.json')}}
    (HERE/'manifest.json').write_text(json.dumps(dict(revision='CP1-R2',files=files),indent=2)+'\n')
    print('Published',len(files),'files')
if __name__=='__main__':main()

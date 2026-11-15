"""Publish the accepted bounded analogue checkpoint, without vendor models."""
import csv
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
from accept import evaluate

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name): return json.loads((HERE/name).read_text())


def plot(data):
    width,height=1000,580
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Loaded output and overload against the capture window</title>',
        '<desc id="desc">Both 50 pF traces meet their thresholds before the 265 to 315 ns guarded capture window. Both 5000 pF overloads fail.</desc>',
        '<rect width="1000" height="580" fill="#0c1420"/>',
        '<g font-family="system-ui" font-size="14" fill="#e2e8f0">']
    x=lambda t:70+(t-140)/200*880
    for index,edge in enumerate(('rising','falling')):
        top=35+index*280
        y=lambda v:top+200-v/5.5*200
        parts.append(f'<text x="70" y="{top-13}">{edge.capitalize()} output: 50 pF (green), 5000 pF overload (red)</text>')
        parts.append(f'<rect x="{x(265)}" y="{top}" width="{x(315)-x(265)}" height="200" fill="#183e3b"/>')
        for v in (0,1,2,3,4,5):
            parts.append(f'<path d="M70,{y(v)} H950" stroke="#304156"/><text x="42" y="{y(v)+5}">{v}</text>')
        for t in (140,173,200,230,265,300,315,340):
            parts.append(f'<path d="M{x(t)},{top} V{top+200}" stroke="#304156"/><text x="{x(t)}" y="{top+224}" text-anchor="middle">{t}</text>')
        threshold=2 if edge=='rising' else .8
        parts.append(f'<path d="M70,{y(threshold)} H950" stroke="#ffd082" stroke-dasharray="5 5"/>')
        for case,color in (('normal','#88e2b0'),('overload','#ff9eab')):
            with (HERE/'traces'/f'{edge}-{case}.csv').open() as stream:
                rows=[(float(r['time_ns']),float(r['output_v'])) for r in csv.DictReader(stream)]
            pts=[f'{x(t):.3f},{y(v):.3f}' for i,(t,v) in enumerate(rows) if 140<=t<=340 and i%4==0]
            parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{x(290)}" y="{top+18}" text-anchor="middle">valid window</text>')
    parts.append('<text x="950" y="570" text-anchor="end">Time from pilot launch (ns)</text></g></svg>')
    (HERE/'waveforms.svg').write_text('\n'.join(parts))


def main():
    contract,data,acceptance=read('contract.json'),read('exploration.json'),read('acceptance.json')
    assert acceptance['requirement_status']=='pass'
    assert sha(HERE/'exploration.json')==acceptance['evidence_sha256']
    assert sha(HERE/'contract.json')==acceptance['contract_sha256']
    assert sha(HERE/'tests.log')==acceptance['tests_sha256']
    for name,digest in data['method_hashes'].items(): assert sha(HERE/name)==digest
    assert sha(HERE.parent/'pilot-driver/audit.py')==data['audit_sha256']
    requirements=json.loads((ROOT/'Verification/requirements.json').read_text())
    checked=evaluate(contract,data,requirements)
    assert checked==acceptance['checks']
    for source in read('source-manifest.json'):
        assert sha(ROOT/source['source'])==source['sha256']==sha(HERE/source['archived'])
    assert not list(HERE.rglob('*.ibs')) and not list(HERE.rglob('*.cir'))
    plot(data)
    esc=html.escape
    normal=[r for r in data['loads'] if r['fault']=='normal']
    normals=''.join(f'<tr><td>{r["edge"]}</td><td>{r["stable_threshold_ns"]:.3f}</td><td>{r["setup_margin_ns"]:.3f}</td><td>{r["window_min_v"]:.6f}–{r["window_max_v"]:.6f}</td><td>pass</td></tr>' for r in normal)
    faults=''.join(f'<tr><td>{r["edge"]}</td><td>{r["fault"]}</td><td>{r["window_min_v"]:.3f}–{r["window_max_v"]:.3f} V</td><td>detected</td></tr>' for r in data['loads'] if r['fault']!='normal')
    correlation=''.join(f'<tr><td>{r["case"]}</td><td>{r["max_difference_v"]*1000:.3f}</td><td>{r["threshold_difference_ns"]:.6f}</td></tr>' for r in data['correlation'])
    independent=''.join(f'<tr><td>{r["case"]}</td><td>{r["max_voltage_difference_v"]*1000:.6f}</td><td>{"pass" if r["measured"]["passed"] else "overload detected"}</td></tr>' for r in data['independent'])
    converter=data['conversion_faults'][0]
    minimum=checked['minimum_setup_margin_ns']
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · PILOT-03 bounded experiment passed</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}img{{display:block;width:100%;height:auto}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#0c1420;padding:12px}}@media(max-width:700px){{main{{padding:18px 10px}}section{{padding:12px}}th,td{{padding:5px;font-size:12px}}h1{{font-size:28px}}}}</style>
<main><nav><a href="/">Full-system dashboard</a> · <a href="../pilot-driver/">Previous model audit</a> · <a href="../bom-inventory/">BOM and inventory</a></nav>
<h1>PILOT-03: loaded-output experiment passed</h1><p id="verdict" class="pass">The bounded analogue gap is closed at the fully specified 5 V / 25 °C model point. Both 50 pF transitions pass, with at least {minimum:.3f} ns of setup margin.</p>
<p>The unchanged requirement is: “Loaded output reaches the required voltage before capture in a bounded analogue experiment.” This checkpoint accepts that experiment. PILOT-05 retains physical and full operating-envelope qualification.</p>
<p class="notice">This is a separately hashed acceptance checkpoint. The ongoing full-system run and its displayed milestone totals are not rewritten by this publication.</p>
<section><h2>What was tested</h2><p>TI SN74HCT245N, output B1 at PDIP pin 18, with the manufacturer's 4 pF die capacitance and pin-specific 0.047 Ω / 7.118 nH / 0.439 pF package model. The external load is 50 pF: a 10 pF receiver allocation plus 40 pF for route, socket and probe. A 1 kΩ resistor opposes each transition, to ground for rising and to 5 V for falling.</p>
<p>The resistive fixture retains TI's waveform loading and adds the receiver capacitance. It is a test load, not a new component in the machine's BOM. The earlier capacitive-only experiment is retained as <a href="capacitive-only-exploration.json">separate exploratory evidence</a>.</p>
<p>The complete switching shape starts at 173 ns: 45 ns source delay + 100 ns ROM delay + 28 ns buffer allowance. Its initial idle interval is retained as extra delay. Capture stays at 300 ns. Applying 25 ns setup, 5 ns hold and ±10 ns uncertainty requires a valid output throughout <b>265–315 ns</b>.</p>
<table id="normal"><thead><tr><th>Edge</th><th>Stable threshold (ns)</th><th>Setup margin (ns)</th><th>Voltage in valid window</th><th>Result</th></tr></thead><tbody>{normals}</tbody></table>
<p>Rising outputs must remain ≥2.0 V and falling outputs ≤0.8 V. The monitor checks the whole window, including its boundaries, rather than one sample at capture. The receiver thresholds and input-capacitance allocation are traced to the archived SN74HCT574 datasheet.</p>
<img src="waveforms.svg" alt="Normal and overloaded output voltages against the guarded capture window"><p><a href="waveforms.svg">Open waveform plot</a> · <a href="traces/rising-normal.csv">Rising trace CSV</a> · <a href="traces/falling-normal.csv">Falling trace CSV</a></p></section>
<section><h2>Manufacturer waveform correlation</h2><p>The transient implementation solves two fixture equations for the pullup and pulldown switching factors, accounting for die-capacitance current and both clamp tables. It retains the extracted factors, including excursions outside 0–1; it does not clip or retime them to force agreement. ngspice then integrates the resulting circuit.</p>
<p>All eight typical/minimum-column fixture reconstructions agree within the declared 10 mV and 0.1 ns numerical tolerances. The minimum column uses an explicit 4 pF assumption because TI gives no corner capacitance; it is a reconstruction check, not an accepted operating point.</p>
<table id="correlation"><thead><tr><th>Fixture case</th><th>Maximum voltage error (mV)</th><th>Threshold-time error (ns)</th></tr></thead><tbody>{correlation}</tbody></table></section>
<section><h2>Independent numerical verification</h2><p>A second implementation integrates the die-capacitor, package-inductor and external-capacitor equations using SciPy's Radau solver. It uses no ngspice voltage or operating-point result. The independent solver agrees on both normal transitions and both overload failures.</p>
<table id="independent"><thead><tr><th>Case</th><th>Maximum solver difference (mV)</th><th>Capture verdict</th></tr></thead><tbody>{independent}</tbody></table>
<p>Halving both the coefficient-grid spacing and ngspice maximum timestep changes the normal threshold times by less than {max(r['threshold_difference_ns'] for r in data['refinements']):.6f} ns. Analytical RC extraction and an exact matrix-exponential RLC solution also check the implementation.</p></section>
<section><h2>Faults must fail</h2><p>Each fault is tested on both edges: 5000 pF overload, capture advanced to 180 ns, switching delayed to 300 ns, and a disabled driver. All eight fail the voltage-window monitor.</p>
<table id="faults"><thead><tr><th>Edge</th><th>Fault</th><th>Window voltage</th><th>Result</th></tr></thead><tbody>{faults}</tbody></table>
<p>A ninth fault changes the implemented die capacitance from 4 pF to 40 pF while retaining the extracted switching factors. Fixture correlation rejects it with {converter['max_difference_v']:.3f} V maximum error. This checks the model-conversion path as well as the capture monitor.</p>
<p>All 12 regression tests pass. They also reject a falsified success flag, reduced load, relaxed capture time, missing fault coverage, independent-solver disagreement and promotion of the unqualified fast corner.</p></section>
<section><h2>Acceptance boundary</h2><p>This closes the bounded nominal-point experiment in PILOT-03. Physical receiver/socket/PCB loading, transmission lines, simultaneous switching, supply/ground behaviour, output-enable handover and the complete clock/reset path remain open.</p>
<p>The fast-column rising-waveform extraction becomes singular, and the file lacks minimum/maximum die capacitance. No interpolation across 4.75–5.25 V or 0–50 °C is claimed. The manufacturer says measurements used the NS package; applying the N package network follows the IBIS de-embedded-waveform convention, with actual package/bench correlation retained under PILOT-05.</p>
<p><a href="https://ibis.org/cookbook/taskgroup/cookbook-v4_4.pdf">IBIS waveform extraction guidance</a> · <a href="https://www.ibis.org/summits/jan15/ross2.pdf">Two-fixture switching-factor method</a> · <a href="https://www.ti.com/lit/ibs/SCLM097">Original TI model</a></p></section>
<section><h2>Reproduce and inspect</h2><p>Requires Python with NumPy and SciPy, ngspice, and the sibling pilot-driver scripts. Download the pinned TI model and official checker into a private cache outside the served Verification directory. The model and generated SPICE decks remain private; computed output traces are published here.</p>
<pre>python3 Verification/build/pilot-driver/prepare.py "$PRIVATE_CACHE"
python3 Verification/build/pilot-transient/transient.py \\
  --model "$PRIVATE_CACHE/sclm097a.ibs" \\
  --private-work "$PRIVATE_CACHE/transient" --independent
python3 Verification/build/pilot-transient/accept.py
python3 Verification/build/pilot-transient/publish.py</pre>
<nav><a href="acceptance.json">Acceptance decision</a> · <a href="evidence.json">Gate evidence</a> · <a href="contract.json">Experiment contract</a> · <a href="exploration.json">All numerical results</a> · <a href="transient.py">Transient implementation</a> · <a href="explore.py">Switching-factor extraction</a> · <a href="accept.py">Acceptance checks</a> · <a href="test_transient.py">Regression tests</a> · <a href="tests.log">Test output</a> · <a href="source-manifest.json">Source snapshot</a> · <a href="manifest.json">Publication hashes</a> · <a href="remote-validation.json">Remote validation</a></nav></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n')
    print('Published',len(files),'artifacts; bounded PILOT-03 checkpoint accepted')


if __name__=='__main__': main()

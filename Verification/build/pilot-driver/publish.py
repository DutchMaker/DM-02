"""Publish the driver qualification evidence and its explicit milestone limit."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads((HERE/'summary.json').read_text())
    assert data['audit_completed'] and not data['milestone_gate_passed']
    assert data['normalized_checker']['passed']
    assert len(data['independent_dc_checks']) == 12 and all(r['passed'] for r in data['independent_dc_checks'])
    assert len(data['endpoints']) == 24 and len(data['waveform_thresholds']) == 12
    assert data['package']['pin_roles_checked'] and data['package']['data_pins'] == 16
    assert len(data['faults']) == 2 and all(r['detected'] for r in data['faults'])
    assert not list(HERE.rglob('*.ibs')) and not list(HERE.rglob('*.cir')), 'Private model material in publication tree'
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_*.py', '-v'],
                           capture_output=True, text=True, timeout=60)
    (HERE/'tests.log').write_text(tests.stdout+tests.stderr)
    assert tests.returncode == 0
    inputs = []
    for relative in ('Verification/models.json', 'Verification/requirements.json', 'Verification/dm02/analog.py'):
        source = ROOT/relative; dest = HERE/'sources'/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        inputs.append(dict(source=relative, sha256=sha(source), archived=str(dest.relative_to(HERE))))
    (HERE/'source-manifest.json').write_text(json.dumps(inputs, indent=2)+'\n')
    esc = html.escape
    corners = ''.join(f'<tr><td>{r["name"]}</td><td>{r["voltage_v"]:g} V</td><td>{r["temperature_c"]:g} °C</td><td>{r["c_comp_pf"] if r["c_comp_pf"] is not None else "NA"}</td></tr>' for r in data['corners'])
    dc = ''.join(f'<tr><td>{r["case"]}</td><td>{r["ngspice_v"]:.6f}</td><td>{r["bisection_v"]:.6f}</td><td>{abs(r["difference_v"])*1e6:.3f}</td></tr>' for r in data['independent_dc_checks'])
    waves = ''.join(f'<tr><td>{r["edge"]}</td><td>{r["corner"]}</td><td>{r["fixture_v"]:g}</td><td>{r["stable_threshold_ns"]:.3f}</td><td>{r["voltage_at_waveform_25ns"]:.3f}</td><td>{"yes" if r["valid_at_waveform_25ns"] else "no"}</td></tr>' for r in data['waveform_thresholds'])
    limits = ''.join('<li>'+esc(s)+'</li>' for s in data['limitations'])
    faults = ''.join(f'<li>{esc(r["fault"])}: detected by {esc(r["detector"])}. <a href="{r["fault"]}.log">Checker log</a>.</li>' for r in data['faults'])
    discrepancy = data['worst_endpoint_difference_v']*1000
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · pilot driver model audit</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.notice{{color:#ffd082}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#0c1420;padding:12px}}@media(max-width:700px){{main{{padding:18px 10px}}section{{padding:12px}}th,td{{padding:5px;font-size:12px}}h1{{font-size:28px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../bom-inventory/">BOM and inventory</a> · <a href="../tht-package-screen/">DIP package alternatives</a></nav>
<h1>SN74HCT245N pilot driver audit</h1><p class="notice" id="verdict">PILOT-03 remains open. The exact driver's manufacturer model now has reproducible syntax, package-pin and DC consistency checks. Loaded transient correlation is still required.</p>
<section><h2>Exact part and source</h2><p>The pilot names SN74HCT245N, a PDIP-20 transceiver. TI's SCLM097 Rev. A download contains the HCT245_N package and HCT245_IO model. The audit checks all 20 pin roles, including the 16 A/B data pins. The file is revision 1.2, dated 10 November 2004; its notes say the measurements used the NS package.</p>
<p><a href="https://www.ti.com/lit/ibs/SCLM097">TI model download</a> · <a href="https://www.ti.com/product/SN74HCT245">TI product page</a> · <a href="https://www.ibis.org/ibischk7/ibischk7.htm">Official IBISCHK 7.2.1 release</a></p>
<table id="corners"><thead><tr><th>Model column</th><th>Supply</th><th>Temperature</th><th>Die capacitance (pF)</th></tr></thead><tbody>{corners}</tbody></table>
<p>These are paired model columns. The min/max labels do not promise arbitrary combinations of supply, temperature and package parasitics. PDIP data-pin package values span {data['package']['data_pin_l_nh_range'][0]:.3f}–{data['package']['data_pin_l_nh_range'][1]:.3f} nH; physical socket and board parasitics are additional.</p></section>
<section><h2>Official checker results</h2><p>The original download reports two errors: its download filename differs from the internal File Name, and it ends with an invalid 0xff byte. A working copy named sn74hct245.ibs with that one trailing byte removed passes IBISCHK 7.2.1. All numerical model data are preserved.</p>
<p>The checker returns exit code zero even when it reports a failed file. The audit therefore parses its verdict and error count. A negative-capacitance fault also revealed that “File Passed” can accompany a warning; the local positive-capacitance contract rejects that case.</p>
<nav><a href="ibischk-original.log">Original-file check</a> · <a href="ibischk-normalized.log">Normalized-file check</a></nav><ul id="faults">{faults}</ul></section>
<section><h2>Independent DC check</h2><p>A piecewise-linear table reader solves output-node current balance by bisection. Separate ngspice behavioural-current circuits solve the same 12 fixture/state/corner cases. Every result agrees within 2 µV. The numerical routines also pass analytical resistor-divider and ringing-crossing checks.</p>
<table id="dc"><thead><tr><th>Case</th><th>ngspice (V)</th><th>Bisection (V)</th><th>Difference (µV)</th></tr></thead><tbody>{dc}</tbody></table>
<p>All 24 recorded waveform endpoints were compared with DC equilibria under their stated resistor loads. The largest difference is {discrepancy:.3f} mV. This is a diagnostic measurement; it is not presented as an IBISCHK error or used as a new milestone tolerance.</p></section>
<section><h2>What the supplied waveforms establish</h2><p>All four waveforms specify 1 kΩ resistive fixtures and zero fixture capacitance. The separate Cref=50 pF parameter describes a timing reference and must not be mistaken for a 50 pF waveform load. The table below measures the final crossing into ≥2.0 V for a rising edge or ≤0.8 V for a falling edge.</p>
<table id="waves"><thead><tr><th>Edge</th><th>Corner</th><th>Fixture (V)</th><th>Stable threshold (ns)</th><th>Voltage at 25 ns</th><th>Valid at 25 ns?</th></tr></thead><tbody>{waves}</tbody></table>
<p>The times refer to the file's waveform origin. They are not guaranteed input-to-output delays, and the 25 ns column is a diagnostic of the supplied fixture data. It does not establish the pilot's 300 ns capture margin.</p></section>
<section><h2>Remaining acceptance work</h2><ul>{limits}</ul>
<p>To close PILOT-03, the transient implementation needs fixture correlation, an explicit receiver/trace/socket load, capture-threshold checks and load/timing fault cases. PILOT-05 separately retains physical operating-envelope qualification. The current arbitrary-resistance RC sweep remains limited evidence.</p></section>
<section><h2>Reproduce</h2><p>Requires Python 3.10+, ngspice and curl on an Apple-silicon Mac. The pinned checker executable is verified against the official release digest. Choose a private cache outside the served Verification directory; the TI model's distribution terms require obtaining it from TI.</p>
<pre>python3 Verification/build/pilot-driver/prepare.py "$PRIVATE_CACHE"
python3 Verification/build/pilot-driver/audit.py \\
  --model "$PRIVATE_CACHE/sclm097a.ibs" \\
  --checker "$PRIVATE_CACHE/ibischk7_64" \\
  --private-work "$PRIVATE_CACHE/hct245-audit"
python3 Verification/build/pilot-driver/publish.py</pre>
<nav><a href="summary.json">Full audit results</a> · <a href="audit.py">Audit and circuit generator</a> · <a href="prepare.py">Pinned downloads</a> · <a href="test_audit.py">Analytical checks</a> · <a href="tests.log">Test results</a> · <a href="source-manifest.json">Pilot source snapshot</a> · <a href="manifest.json">Publication hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded = {'manifest.json', 'remote-validation.json', 'browser-check.json', 'desktop.png', 'mobile.png'}
    files = {str(p.relative_to(HERE)): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(), files=files), indent=2)+'\n')
    print('Published', len(files), 'pilot-driver audit artifacts; loaded-output milestone remains open')


if __name__ == '__main__':
    main()

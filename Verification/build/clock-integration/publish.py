"""Publish the tested ACH integration and its explicit physical limits."""
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
CANDIDATE=HERE/'candidate'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def main():
    summary=read(HERE/'summary.json');sources=read(HERE/'source-manifest.json')
    assert summary['passed'] and summary['tests']>=158 and not summary['normal_sources_modified']
    for relative,digest in sources['candidate'].items():assert sha(CANDIDATE/relative)==digest,relative
    verification=CANDIDATE/'Verification';build=verification/'build'
    timing=summary['clock_timing'];base='candidate/Verification/build/'
    links=''.join(f'<li><a href="candidate/{html.escape(p,quote=True)}">{html.escape(p)}</a></li>' for p in sources['changed'])
    failures=[r for r in summary['intervals'][0]['paths'] if not r['passed']]
    rows=''.join(f'<tr><td>{html.escape(r["path"])}</td><td>{r["margin_ns"]:.3f} ns</td></tr>' for r in failures)
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · 4 MHz clock integration</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1050px;margin:auto;padding:24px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}section{{padding:18px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}h1{{line-height:1.2}}table{{border-collapse:collapse;width:100%;table-layout:fixed}}td,th{{text-align:left;padding:8px;border-bottom:1px solid #304156;overflow-wrap:anywhere}}th:last-child{{width:25%}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../clock-ach/">Original isolated ACH study</a> · <a href="../bom-inventory/">Published BOM workbook</a></nav><h1>4 MHz clock integration validated in staging</h1>
<p class="pass" id="verdict">150/150 clock profiles and {summary['tests']} regression tests pass. The staged C1 and FD1 use the same ACH-4.000MHZ-EK contract.</p>
<p class="notice">This staged result closes the candidate-selection mismatch. Physical clock qualification remains open. Normal source promotion and a complete run of the promoted tree are pending.</p>
<section><h2>One selected oscillator contract</h2><p>C1/Y1 changes from ECS-100AX-080 with a DIP-14 footprint to the through-hole ACH-4.000MHZ-EK with a DIP-8 footprint. Pin 1 is isolated NC, 4 is ground, 5 is output and 8 is 5V. All {summary['normalized_clock_net_groups']} clock net groups agree after this intentional pin remap; native KiCad verifies the selected drawing.</p>
<p>Every counted-clock testbench consumes the selected 250 ns oscillator period. FD1 verifies its target against the selected part and records the identity in simulation provenance. Tests reject the old footprint/pin map, excess oscillator load, a changed selection and a doubled actual stimulus rate.</p>
<p>The working inventory workbook is preserved as published. This page records the proposed one-part substitution; owned inventory and procurement remain unconfirmed.</p></section>
<section><h2>Conditional timing and connected execution</h2><p>At 4 MHz, the phase interval is at least {timing['phase_min_ns']:.3f} ns, leaving {timing['pilot_margin_ns']:.3f} ns over the unchanged pilot requirement. The smallest internal margin is {min(r['margin_ns'] for r in timing['paths']):.3f} ns.</p>
<p>FD1 passes all eight continuous profiles, three all-opcode profiles, exact hello-world output, 324 connector links, nine wiring faults and 28 receiver guards. All 46 interval paths pass conditionally at 4 MHz. The counterfactual 8 MHz study fails these paths:</p>
<table id="rejections"><thead><tr><th>8 MHz path</th><th>Margin</th></tr></thead><tbody>{rows}</tbody></table>
<p>The extra HALT-path failure follows from the wider assumed receiver-duty range. The analysis retains the selected 4 MHz part identity while marking 8 MHz as a counterfactual.</p>
<nav><a href="{base}clock/candidate.json">Clock results</a> · <a href="{base}clock/native/comparison.json">Native clock parity</a> · <a href="{base}distribution/summary.json">Connected FD1 execution</a> · <a href="{base}distribution/timing.json">All interval paths</a> · <a href="tests.log">Regression log</a></nav></section>
<section><h2>Physical limits</h2><p>The ACH standard load is 15 pF, fully allocated to a 10 pF AHCT input and 5 pF routing/socket/probe allowance. Actual loading is unqualified. The manufacturer specifies 45–55% duty at half supply; the 37–63% receiver-duty range used here is an explicit sensitivity assumption. Edge measurement levels, monotonicity, cycle jitter, startup/reset and full insertion tolerance remain open.</p>
<p>The archived manufacturer-origin sheet is dated 2016-11-15 and came through a mirror. Current lifecycle, latest revision and stock are unconfirmed. This result does not approve fabrication.</p></section>
<section><h2>Changed sources</h2><ul>{links}</ul></section><nav><a href="summary.json">Summary and proposed BOM delta</a> · <a href="source-manifest.json">Source hashes</a> · <a href="manifest.json">Publication hashes</a> · <a href="remote-validation.json">Remote verification</a></nav></main></html>'''
    (HERE/'index.html').write_text(page)
    paths=[HERE/p for p in ('prepare.py','validate.py','publish.py','promote.py','verify.py','browser_check.cjs','tests.log','summary.json','source-manifest.json','baseline-sources.json','index.html')]
    paths.extend(CANDIDATE/p for p in sources['changed'])
    for folder in ('clock','distribution'):
        paths.extend(p for p in (build/folder).rglob('*') if p.is_file() and p.suffix not in ('.vvp','.pyc'))
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths)) if p.is_file()}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n')
    print('Published',len(files),'clock-integration artifacts')


if __name__=='__main__':main()

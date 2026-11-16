from pathlib import Path
import hashlib
import html
import json
import re

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results.json').read_text())
    assert result['completed'] and all(x['detected'] for x in result['unit_checks'])
    sampled='All eight sampled profiles passed the added hold check.' if result['all_sampled_profiles_passed'] else 'The sampled profiles exposed a data-hold failure; this part is not a verified drop-in replacement.'
    observations=[re.search(r'events=(\d+) minimum_ns=([\d.]+)',line) for x in result['runs'] for line in x['observed_hold_lines']]
    minimum=min(float(m[2]) for m in observations if m and int(m[1])>0)
    rows=''.join('<tr><td>'+html.escape(x['profile'])+'</td><td>'+('pass' if x['passed'] else 'fail')+'</td><td><a href="'+html.escape(x['log'],quote=True)+'">Simulation log</a><pre>'+html.escape('\n'.join(x['observed_hold_lines']))+'</pre></td></tr>' for x in result['runs'])
    text='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 HCT273 timing review</title>
<style>body{max-width:960px;margin:40px auto;padding:0 20px;background:#101923;color:#e6edf3;font:16px/1.6 system-ui}a{color:#63dfdc}td,th{padding:8px;text-align:left;border-bottom:1px solid #425266}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%;table-layout:fixed}</style>
<h1>HCT273 timing review</h1><p id="state">CD74HCT273E evaluated; active CP1 remains unchanged.</p>
<p>TI SCHS174D explicitly specifies clock-to-Q at 38 ns maximum and clear-to-Q at 40 ns maximum, at 4.5 V, −40 to 85 °C and 50 pF. The PDIP-20 ordering entry is Active / Production. These maxima fit inside CP1's 42 ns delay allocation.</p>
<p>The alternative requires 3 ns data hold. CP1's SN74HCT273 model assumes 0 ns, so matching the maximum propagation delay alone cannot qualify the substitution. The study adds a 3 ns monitor while retaining CP1's conservative setup, pulse, recovery and propagation parameters. Unit stimuli check a 2 ns violation and legal 3/4 ns boundaries.</p>
<p>'''+sampled+'''</p><table><thead><tr><th>Profile</th><th>Result</th><th>Observed hold checks</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<p>The CPU profiles exercise the accumulator register; they do not capture IO. Two standalone memory profiles cover both IO registers. The smallest observed hold interval is '''+str(minimum)+''' ns, versus the alternative part's 3 ns requirement. Rows with zero events provide no hold coverage.</p>
<p>This bounded study does not qualify minimum silicon delays, physical loads, all corner profiles or full boot. Any substitution needs revised schematic/BOM identity and accepted timing evidence, including a physical load limit of 50 pF for these bounds.</p>
<p><a href="source.json">Manufacturer bounds</a> · <a href="cd74hct273.pdf">TI datasheet</a> · <a href="results.json">Study results</a> · <a href="review.py">Reproduction script</a> · <a href="../cp1-promotion/">CP1 promotion</a></p></html>'''
    (HERE/'index.html').write_text(text)
    files={str(p.relative_to(HERE)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in HERE.rglob('*') if p.is_file() and p.suffix!='.vvp' and p.name not in ('manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png')}
    (HERE/'manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print(sampled)


if __name__=='__main__':main()

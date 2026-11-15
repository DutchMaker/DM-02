"""Publish the isolated ACH experiment and its complete local evidence hashes."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import html
import json

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())


def main():
    summary,interface,faults=map(read,('summary.json','interface.json','hdl-faults.json'))
    assert all(d['passed'] for d in (summary,interface,faults))
    assert summary['passing_simulations']==summary['simulations']==100
    assert all(r['passed'] for r in read('simulations.json'))
    assert summary['native']['source_hash']==sha(HERE/'sandbox/Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch')
    for row in read('source-manifest.json'):
        assert sha(HERE/'sources'/row['source'])==row['sha256']
        assert sha(HERE.parents[2]/row['source'])==row['sha256'],'Normal source changed'
    assert sha(HERE/'footprint/Oscillator_DIP-8.kicad_mod')==interface['footprint']['sha256']
    timing=read('timing.json');rows=''
    for a,b in zip(timing['half_supply_reference_only']['paths'],timing['assumed_receiver_duty_sensitivity']['paths']):
        rows+=f'<tr><td>{html.escape(a["path"])}</td><td>{a["margin_ns"]:.3f}</td><td>{b["margin_ns"]:.3f}</td></tr>'
    diagnostics=''.join(f'<tr><td>{html.escape(r["name"])}</td><td>{"Pass" if r["expected_pass"] else "Rejected"}</td><td>{html.escape(r["diagnostic"])}</td></tr>' for r in faults['results'])
    links={
        'summary.json':'Summary','interface.json':'Electrical and nominal footprint screen',
        'timing.json':'Conditional timing arithmetic','simulations.json':'100 simulation results',
        'hdl-faults.json':'Executable fault results','native/comparison.json':'Native KiCad comparison',
        'native/Counted-Clock.kicad_sch':'Native schematic','native/Counted-Clock.xml':'Native netlist',
        'sandbox/Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch':'Legacy ACH candidate',
        'sandbox/Circuits/KiCad/Libraries/DM02-ACH.lib':'ACH symbol library',
        'footprint/Oscillator_DIP-8.kicad_mod':'Archived nominal DIP-8 footprint',
        'source-manifest.json':'72 original input hashes','adaptations.json':'Five source adaptations',
        'sources/Verification/build/component-followup/abracon-ach-2016.pdf':'Abracon ACH family sheet',
        'sources/Verification/build/component-followup/abracon-ach-source.json':'Manufacturer retrieval record',
        'sources/Verification/vendor/clock/sn74ahct04.txt':'Archived AHCT04 receiver limits',
        'prepare.py':'Prepare isolated snapshot','check.py':'Native and simulation runner',
        'faults.py':'Executable fault runner','interface_review.py':'Interface and footprint screen',
        'manifest.json':'All publication hashes','remote-validation.json':'Remote hash verification'}
    artifacts=''.join(f'<li><a href="{p}">{label}</a></li>' for p,label in links.items())
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · isolated 4 MHz ACH clock</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}main{{max-width:1100px;margin:auto;padding:28px 18px}}a{{color:#8acfff;overflow-wrap:anywhere}}h1{{line-height:1.2}}section{{padding:20px;background:#152132;border:1px solid #304156;border-radius:10px;margin:20px 0}}.pass{{color:#88e2b0}}.notice{{color:#ffd082}}img{{display:block;width:100%;height:auto;background:white}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #304156;overflow-wrap:anywhere}}code,pre{{white-space:pre-wrap;overflow-wrap:anywhere}}@media(max-width:700px){{section{{padding:13px}}td,th{{padding:5px;font-size:12px}}}}</style>
<main><nav><a href="/">Live dashboard</a> · <a href="../component-followup/">Earlier oscillator research</a> · <a href="../reset-followup/">Supervisor screen</a></nav>
<h1>Isolated 4 MHz ACH clock</h1><p class="pass">100/100 digital profiles pass with the ACH pin map. Native KiCad agrees on 66 net groups and 204 physical pins across 27 components. Four contract faults and three executable HDL faults are rejected.</p>
<p class="notice">This candidate tests the counted-clock core at a 4 MHz oscillator / 500 kHz microcycle rate. Receiver-threshold duty, loaded slew, jitter, startup/reset behaviour and physical assembly remain unqualified. Milestone acceptance is unchanged.</p>
<section><h2>Explicit oscillator substitution</h2><table id="pins"><thead><tr><th>Function</th><th>Existing ECS DIP-14</th><th>ACH DIP-8 candidate</th></tr></thead><tbody><tr><td>NC</td><td>1</td><td>1</td></tr><tr><td>Case / GND</td><td>7</td><td>4</td></tr><tr><td>Output</td><td>8</td><td>5</td></tr><tr><td>VDD</td><td>14</td><td>8</td></tr></tbody></table>
<p>ACH-4.000MHZ-EK selects 4 MHz, −20..70 °C and ±30 ppm. It has the standard 15 pF output load and an unused pin 1. Tri-state option A and 50 pF option 50 are absent from this ordering code.</p>
<p>The experiment contains its own symbol, DIP-8 footprint declaration, part contract, pin-derived oscillator drive and frequency-aware testbench. The ordinary library resolver runs inside a repository-shaped snapshot of 72 archived inputs. All connectivity matches C1 after the intentional oscillator-terminal remap.</p>
<a href="schematic-svg/Counted-Clock.svg"><img src="schematic-svg/Counted-Clock.svg" alt="Native KiCad rendering of the isolated 4 MHz ACH counted-clock candidate"></a>
<p>The stock oscillator footprint has four 0.8 mm holes on a 7.62 × 7.62 mm grid. The ACH drawing gives ±0.2 mm pitch tolerance and 0.46 mm nominal leads, with no maximum lead diameter. The nominal grid matches; full insertion tolerance and socket fit remain open.</p></section>
<section><h2>Oscillator-to-receiver conditions</h2><p>Y1.5 drives only U3.1, an SN74AHCT04N input allocated 10 pF. The 15 pF oscillator rating leaves 5 pF for every other contribution, including track, pad, socket and probe capacitance. The present 5 pF routing allocation consumes all of that remainder.</p>
<p>At 4.5–5.5 V supply, the archived output-level limits give 2.05 V static high margin and 0.25 V static low margin against the AHCT input thresholds. These static margins do not establish loaded timing.</p>
<p>The ACH sheet specifies 45–55% duty at half supply and 10 ns maximum rise/fall time. It omits the rise/fall measurement levels and a cycle-jitter maximum. Monotonic crossings, the receiver's 20 ns/V transition condition and duty at its actual thresholds still need evidence.</p>
<p>The 37–63% digital-duty sweep is an assumed stress range, expanded by eight percentage points from 45–55%. At nominal 250 ns period this is 20 ns per side. It is a sensitivity test; it is not a datasheet-derived duty guarantee.</p></section>
<section><h2>Conditional timing and executable checks</h2><p>Ten zero/maximum/mixed gate-delay profiles run at five ideal digital duty cycles (37, 45, 50, 55 and 63%) and both ±30 ppm endpoints. Each checks counted sequencing, 8:1 division, continuous running, handshake cycles, button steps, stop boundaries, reset abort/restart and pilot ROM transfers.</p>
<p>The testbench uses a 250 ns nominal oscillator period, period-relative phase checks and settling windows. It retains the 1 µs external reset-pulse test. Gate timing limits and the allocated routing/jitter terms remain those of the archived C1 contract.</p>
<table id="timing"><thead><tr><th>Core path</th><th>45/55 reference margin (ns)</th><th>37/63 assumed-duty margin (ns)</th></tr></thead><tbody>{rows}</tbody></table>
<p>The smallest assumed-duty margin is {summary['min_sensitivity_margin_ns']:.3f} ns. This result is conditional on the ideal receiver stimulus and retained load/slew assumptions; it does not qualify the complete FD1 machine with this physical oscillator.</p>
<table id="faults"><thead><tr><th>Executable case</th><th>Outcome</th><th>Observed diagnostic</th></tr></thead><tbody>{diagnostics}</tbody></table>
<p>The four additional contract mutations select output pin 8, add 0.1 pF beyond the standard-load budget, restore the DIP-14 footprint or swap the supply/output net labels. Each is rejected.</p></section>
<section><h2>Reset boundary</h2><p>ACH startup is specified at 10 ms maximum in the archived family sheet. The existing external-fixture contract holds reset for 25 ms after a valid supply, leaving 15 ms of arithmetic surplus. The supervisor circuit still needs a bounded delay and defined behaviour on interrupted ramps and shallow brownouts.</p>
<p>Digital simulations exercise ideal reset edges and C1's staged release. The earlier TPS389050GQDSERQ1 screen remains static-only: its 26.23 mV release headroom does not supply the missing maximum assertion delay. Receiver inhibition, SRAM/IO write interruption and metastability qualification remain open.</p></section>
<section><h2>Evidence and reproduction</h2><ul id="artifacts">{artifacts}</ul>
<pre>python3 Verification/build/clock-ach/prepare.py
python3 Verification/build/clock-ach/check.py
python3 Verification/build/clock-ach/faults.py
python3 Verification/build/clock-ach/interface_review.py
python3 Verification/build/clock-ach/publish.py
python3 Verification/build/clock-ach/verify_publication.py</pre>
<p>The reproduction tools require Python 3, Icarus Verilog and KiCad CLI. The footprint screen reads the installed KiCad footprint and retains its hash. Run preparation and checks together after changing inputs. The manufacturer sheet is revision 2016-11-15; current manufacturer revision/lifecycle, sourcing and physical tests remain open.</p></section></main></html>'''
    (HERE/'index.html').write_text(page)
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png','schematic.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.kicad_prl')
        and not(p.parent==HERE and p.name in excluded)}
    (HERE/'manifest.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n')
    print('Published',len(files),'files;',sum(r['bytes'] for r in files.values()),'bytes')


if __name__=='__main__':main()

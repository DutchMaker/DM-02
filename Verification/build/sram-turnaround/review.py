"""Static, direction-specific SRAM bus and command-release review; no simulation."""
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.memory_hardware import Circuit
from dm02.legacy import read_sheet,function_number
from dm02.reporting import sources


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def gate_paths(c,target,origin,seen=()):
    """Trace actual combinational pin nets; unknown branches add no path."""
    if target==origin:return [dict(delay_ns=0,gates=[])]
    assert target not in seen,'Combinational cycle'
    found=[]
    for part in c.sheet['components']:
        kind=function_number(part['lib_id'].split(':')[-1])
        if kind not in ('04','08','00','32'):continue
        outs=[p for p in part['pins'] if p['kind']=='O']
        ins=[p for p in part['pins'] if p['kind']=='I']
        if not outs or not ins:continue
        assert len(outs)==1
        if c.nodes[part['ref'],outs[0]['number']]!=target:continue
        for pin in ins:
            for path in gate_paths(c,c.nodes[part['ref'],pin['number']],origin,seen+(target,)):
                edge=dict(ref=part['ref'],input_pin=pin['number'],output_pin=outs[0]['number'],
                    mpn=part['value'],maximum_ns=c.parts['devices'][part['value']]['max_delay_ns'])
                found.append(dict(delay_ns=path['delay_ns']+edge['maximum_ns'],gates=path['gates']+[edge]))
    return found


def analyze(c):
    pins={(part['ref'],p['number']):(part,p) for part in c.sheet['components'] for p in part['pins']}
    rows=[]
    assert c.nodes['U2','24']==c.labels['READ_n']
    assert c.nodes['U4','1']==c.nodes['U4','19']==c.labels['WRITE_n']
    assert c.nodes['U2','22']==c.labels['GND'] and c.nodes['U2','30']==c.labels['5V']
    for bit in range(8):
        net=c.nets[c.labels[f'RAM{bit}']]
        drivers=[];receivers=[]
        for node in net['nodes']:
            part,p=pins[tuple(node)];device=c.parts['devices'][part['value']]
            row=dict(ref=part['ref'],pin=p['number'],mpn=part['value'],kind=p['kind'])
            if p['kind'] in ('O','T','B'):drivers.append(row)
            elif p['kind']=='I':receivers.append(dict(row,input_cap_pf=device['input_cap_pf']))
            else:raise ValueError('Unexpected SRAM bus pin '+str(node))
        assert {r['ref'] for r in drivers}=={'U2','U4'} and len(receivers)==1
        receiver=sum(r['input_cap_pf'] for r in receivers);trace=c.parts['constraints']['local_trace_cap_pf']
        rows.append(dict(bit=bit,drivers=drivers,receivers=receivers,
            read_external_known_allocation_pf=receiver+trace,read_inactive_writer_output_cap_max_pf=None,
            write_external_allocation_at_25c_pf=receiver+trace+c.parts['devices']['AS6C1008-55PCN']['io_cap_pf'],
            full_temperature_bound_qualified=False))
    paths={}
    for target in ('READ_n','WRITE_n'):
        paths[target]={origin:gate_paths(c,c.labels[target],c.labels[origin]) for origin in ('MEM_out_n','MEM_load_n')}
        assert all(paths[target].values())
    read_logic=max(p['delay_ns'] for ps in paths['READ_n'].values() for p in ps)
    write_logic=max(p['delay_ns'] for ps in paths['WRITE_n'].values() for p in ps)
    ram=c.parts['devices']['AS6C1008-55PCN'];buf=c.parts['devices']['SN74AHCT244N']
    release={'read_to_write':read_logic+ram['disable_max_ns'],'write_to_read':write_logic+buf['disable_max_ns']}
    uncertainty=c.parts['constraints']['routing_uncertainty_ns']
    return dict(buses=rows,paths=paths,read_disable_logic_max_ns=read_logic,write_disable_logic_max_ns=write_logic,
        conditional_release_max_ns=release,relative_uncertainty_allocation_ns=uncertainty,
        conditional_blank_requirement_ns={k:v+uncertainty for k,v in release.items()},
        minimum_new_driver_enable_assumed_ns=0,
        command_blank_verified=False,turnaround_qualified=False,
        scope='Conditional sufficient release intervals from the ME1 command pins, assuming the existing device timing bounds apply. Both commands must first be inactive. Zero earliest enable is conservative. Actual command blanking, hazards, reset abort, physical loads/slew and full-temperature capacitance remain unqualified.')


def main():
    before=sources();HERE.mkdir(parents=True,exist_ok=True)
    paths=['Circuits/KiCad/Memory/candidates/Memory-IO.sch','Circuits/KiCad/Distribution/candidates/Data-ME1.sch']
    results={name:analyze(Circuit(read_sheet(ROOT/path))) for name,path in zip(('ME1','FD1_ME1'),paths)}
    assert results['ME1']==results['FD1_ME1'],'Distribution changed internal SRAM handover'
    # Explicit pin faults must not be admitted by the static interface review.
    from copy import deepcopy
    faults=[]
    for ref,pin,target in [('U2','24','GND'),('U4','1','GND'),('U2','22','5V')]:
        c=Circuit();c.nodes=deepcopy(c.nodes);c.nodes[ref,pin]=c.labels[target]
        try:analyze(c)
        except AssertionError:faults.append(dict(ref=ref,pin=pin,target=target,detected=True))
        else:raise AssertionError('Undetected control-pin mutation')
    source_paths=paths+['Verification/memory-parts.json','Verification/pc-parts.json','Verification/controller-parts.json',
        'Verification/alu-parts.json','Verification/dm02/memory_hardware.py','Verification/dm02/alu_hardware.py',
        'Verification/designs/memory_candidate.py','Verification/designs/distribution_candidate.py',
        'Verification/vendor/memory/as6c1008.txt','Verification/vendor/memory/manifest.json',
        'Verification/vendor/clock/sn74ahct244.txt','Verification/vendor/clock/manifest.json']
    for relative in source_paths:
        target=HERE/'sources'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
    for group,filename in [('memory','as6c1008.txt'),('clock','sn74ahct244.txt')]:
        manifest=json.loads((ROOT/f'Verification/vendor/{group}/manifest.json').read_text())
        entry=next(r for r in manifest['files'] if r['file']==filename)
        assert sha(ROOT/f'Verification/vendor/{group}/{filename}')==entry['sha256']
    assert sources()==before,'Normal inputs changed during review'
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),review_completed=True,
        status='limited',normal_sources_modified=False,simulation_performed=False,
        source_hashes={p:before[p] for p in source_paths},normal_source_hashes=before,results=results,pin_mutations=faults,
        datasheet_conditions=dict(sram_read_load_pf=50,sram_read_ttl_loads=1,
            sram_tristate_load_pf=5,sram_tristate_threshold_mv_from_steady_state=500,
            sram_io_cap_max_pf=8,sram_capacitance_temperature_c=25,
            sram_tristate_characterized_not_production_tested=True,
            source_pages=[5,6,7]),
        findings=['The 23 pF allocation describes write drive: 10 pF mux input + 5 pF routing + 8 pF SRAM DQ capacitance at 25 C.',
            'During reads, the external allocation is 15 pF plus an unbounded inactive AHCT244 output capacitance; the SRAM own DQ capacitance is not counted again as an external receiver.',
            'The 20 ns SRAM disable limit is characterized at 5 pF and a 500 mV departure from the steady output, not a full logic-threshold transition.',
            'The same-condition tOHZ<tOLZ ordering applies to the SRAM itself; it does not establish non-overlap with a separate AHCT244 driver.',
            'A slower oscillator does not by itself prove a blank interval at the ME1 command pins. The conditional interval arithmetic is not a qualification result.'])
    write(HERE/'review.json',summary)
    r=results['ME1'];findings=''.join('<li>'+html.escape(s)+'</li>' for s in summary['findings'])
    (HERE/'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DM-02 · SRAM handover review</title><link rel="icon" href="data:,">
<style>:root{{color-scheme:dark}}body{{margin:24px auto;padding:0 16px;max-width:1000px;background:#0c1420;color:#e2e8f0;font:16px/1.6 system-ui}}a{{color:#8acfff;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%;table-layout:fixed}}td,th{{border-bottom:1px solid #304156;padding:8px;text-align:left}}.limit{{color:#ffd082}}</style>
<nav><a href="/">Live dashboard</a> · <a href="../clock-integration/">Staged 4 MHz clock</a></nav><h1>SRAM private-bus handover</h1>
<p class="limit" id="verdict">Static review complete; electrical turnaround remains unqualified. All eight SRAM data nets retain two possible drivers.</p>
<p>Normal ME1 and FD1/ME1 have identical internal SRAM bus connections and command-release paths. Three control-pin mutations are rejected. This review runs no simulation and changes no normal sources.</p>
<h2>Direction-specific load allocation</h2><ul>{findings}</ul>
<h2>Conditional command blanking</h2><p>The calculation starts when MEM_out_n and MEM_load_n are both commanded inactive at the ME1 connector. It uses maximum disable-path delays and zero minimum enable delay for the new driver. The 10 ns relative-uncertainty allowance is additional. Device load and edge conditions must hold before these figures can be used.</p>
<table id="intervals"><tr><th>Direction</th><th>Release bound</th><th>Blank with allowance</th></tr><tr><td>Read to write</td><td>{r['conditional_release_max_ns']['read_to_write']:.1f} ns</td><td>{r['conditional_blank_requirement_ns']['read_to_write']:.1f} ns</td></tr><tr><td>Write to read</td><td>{r['conditional_release_max_ns']['write_to_read']:.1f} ns</td><td>{r['conditional_blank_requirement_ns']['write_to_read']:.1f} ns</td></tr></table>
<p>Next verification must establish the command blank interval through CW1/SQ1 and the ME1 input pins, characterize or bound inactive-output capacitance and loaded release, and cover reset interruption. These conditional numbers do not close MOD-08 or authorize a PCB.</p>
<p><a href="review.json">Pin paths, allocations and scope</a> · <a href="sources/Verification/vendor/memory/as6c1008.txt">SRAM source, pages 5–7</a> · <a href="sources/Verification/vendor/clock/sn74ahct244.txt">AHCT244 source</a> · <a href="manifest.json">Publication hashes</a> · <a href="remote-validation.json">Remote verification</a></p></html>''')
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.rglob('*')) if p.is_file() and not(p.parent==HERE and p.name in excluded) and '__pycache__' not in p.parts}
    write(HERE/'manifest.json',dict(files=files))
    print(json.dumps(dict(buses=len(r['buses']),conditional_blank_ns=r['conditional_blank_requirement_ns'],pin_faults=len(faults),publication_files=len(files),qualified=False)))


if __name__=='__main__':main()

"""Resume after the budget correction, accepting only matching completed models."""
from pathlib import Path
import importlib.util,json,time,hashlib
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,digest,write_json
from dm02.compact_hardware import Circuit,support_hdl
def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def main():
    results=[];verified=[];start=time.time()
    folders=[f'c{c}-cases0' for c in range(12)]+[f'c{c}-cases0-d{d}-ppm{ppm}' for c in (1,4,7) for d in (.37,.63) for ppm in (-30,30)]+[f'c{c}-cases1' for c in (0,1,7)]+['c1-hello_world']
    for name in folders:
        folder=BUILD/'compact'/name;x=json.loads((folder/'result.json').read_text());assert x['passed']
        for model,h in x['model_hashes'].items():
            assert digest(folder/model)==h,(name,model,'saved model changed')
            expected=r.bench() if model=='tb.sv' else (VROOT/'hdl/controller_devices.sv').read_text()+support_hdl() if model=='support.sv' else Circuit(Path(model).stem).hdl(x['corner'])
            assert sha(expected)==h,(name,model,'current model differs')
        for board,h in x['schematic_hashes'].items():assert digest(r.CANDIDATE/f'Circuits/KiCad/Compact/candidates/{board}.sch')==h
        log=(HERE/x['log']).read_text();assert 'DONE ' in log and 'FATAL' not in log and 'TIMEOUT' not in log
        verified.append(name);results.append(x)
    # Dedicated device suites must also match the current checked model text.
    for name in [f'counter-c{c}-full1-fault0' for c in (0,1,4)]+['counter-c1-full0-fault1']:
        folder=BUILD/'compact'/name;x=json.loads((folder/'result.json').read_text());assert x['passed']
        for model,h in x['model_hashes'].items():assert digest(folder/model)==h
        assert sha(support_hdl())==x['model_hashes']['support.sv']
        assert sha((VROOT/'hdl/compact_counter_tb.sv').read_text())==x['model_hashes']['tb.sv']
        c=Circuit('SP1')
        if x['fault']:c.nodes['U3','5']=c.labels['GND']
        assert sha(c.hdl(x['corner']))==x['model_hashes']['stack.sv']
        assert sha(Circuit('C1').hdl(x['corner']))==x['model_hashes']['clock.sv']
        verified.append(name);results.append(x)
    for x in json.loads((HERE/'register-check.json').read_text())['runs']:
        folder=(HERE/x['log']).parent
        for model,h in x['model_hashes'].items():assert digest(folder/model)==h
        assert sha((VROOT/'hdl/alu_devices.sv').read_text()+(VROOT/'hdl/controller_devices.sv').read_text()+support_hdl())==x['model_hashes']['support.sv']
        assert sha(Circuit('BF1').hdl(x['corner']))==x['model_hashes']['fabric.sv']
    for corner in range(10):
        folder=BUILD/'compact'/f'clock-c{corner}'
        assert digest(folder/'clock.sv')==sha('`define DM02_OSC_PERIOD_NS 250\n'+Circuit('C1').hdl(corner))
        assert digest(folder/'tb.sv')==sha((VROOT/'hdl/clock_candidate_tb.sv').read_text().replace('phase,active,ready,state);','phase,active,ready,state,,);'))
    for name in ('rom-check.json','clock-check.json','register-check.json','fault-check.json','native-audit.json','physical-review.json','interconnect-check.json','workbook-validation.json'):
        d=json.loads((HERE/name).read_text());assert d.get('passed',d.get('native_passed')),name
    receipt=dict(passed=True,profiles=verified,checks_sha256={p.name:digest(p) for p in HERE.glob('*check.json')},
        reason='Wall/simulated-time execution budgets changed; SRAM fixture cropped to the unchanged decoded 64 KiB. Prior passing models/schematics remain hash-matched. The four-second-watchdog boot is preserved as a failed run, not accepted.')
    write_json(HERE/'resume-check.json',receipt)
    write_json(HERE/'verification-state.json',dict(state='running',started_at=start,resumed=verified))
    try:
        x=r.profile(1,boot=True);results.append(x);assert x['passed']
    except Exception as e:
        write_json(HERE/'verification-state.json',dict(state='failed',started_at=start,finished_at=time.time(),error=repr(e),runs=results));raise
    write_json(HERE/'verification-state.json',dict(state='complete',passed=True,started_at=start,finished_at=time.time(),runs=results,resumed=verified))
    print('CP1 serial regression complete',flush=True)
if __name__=='__main__':main()

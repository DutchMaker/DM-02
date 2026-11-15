"""Bounded, synthetic critical path; explicit monitors, not simulator specify checks."""
import json
import re
from .common import BUILD, VROOT, command, evidence, write_json


def run():
    p = json.loads((VROOT/'requirements.json').read_text())['pilot']
    folder = BUILD/'pilot'
    folder.mkdir(parents=True, exist_ok=True)
    required = sum(p[k] for k in ('source_tco_ns','rom_access_ns','buffer_delay_ns','setup_ns','clock_uncertainty_ns'))
    budget = dict(required_ns=required, terms=p,
                  documented_margin_ns=p['documented_phase_ns']-required,
                  candidate_margin_ns=p['candidate_phase_ns']-required,
                  hold_qualification='unresolved: no guaranteed path minimum delays',
                  physical_clock='unqualified: existing 1nF load requires a device/clock model and measurement')
    write_json(folder/'budget.json', budget)
    definitions = '\n'.join(f'`define {k.upper()} {v}' for k,v in p.items())
    (folder/'parameters.vh').write_text(definitions+'\n')
    code, log = command(['iverilog','-g2012','-I',folder,'-o',folder/'pilot.vvp',VROOT/'hdl/pilot.sv'])
    (folder/'compile.log').write_text(log)
    if code:
        raise RuntimeError(log)
    cases = [('candidate',0,p['candidate_phase_ns'],set()),
             ('documented-120ns',0,p['documented_phase_ns'],{'SETUP','DATA'}),
             ('setup-fault',1,p['candidate_phase_ns'],{'SETUP'}),
             ('hold-fault',2,p['candidate_phase_ns'],{'HOLD'}),
             ('pulse-fault',3,p['candidate_phase_ns'],{'PULSE'}),
             ('reset-fault',4,p['candidate_phase_ns'],{'RESET'}),
             ('contention-fault',5,p['candidate_phase_ns'],{'CONTENTION'}),
             ('wiring-fault',6,p['candidate_phase_ns'],{'DATA'})]
    results=[]
    for name,mode,phase,expected in cases:
        code, log = command(['vvp',folder/'pilot.vvp',f'+MODE={mode}',f'+PHASE={phase}',f'+VCD={name}.vcd'],cwd=folder)
        (folder/(name+'.log')).write_text(log)
        actual=set(re.findall(r'VIOLATION (\w+)',log))
        done=re.search(r'DONE captures=(\d+)',log)
        captures=int(done[1]) if done else 0
        ok=code==0 and captures==8 and actual==expected
        results.append(dict(name=name,status='pass' if ok else 'fail',expected=sorted(expected),
                            observed=sorted(actual),captures=captures,
                            meaning='model path passes' if not expected else 'expected violation detected' if ok else 'checker mismatch',
                            log=f'pilot/{name}.log',waveform=f'pilot/{name}.vcd'))
    write_json(folder/'cases.json',results)
    return [evidence('pilot','Timed digital pilot','pass' if results[0]['status']=='pass' else 'fail',
                     'Eight address-sensitive transfers at the candidate phase separation.',cases=results,
                     artifacts=['pilot/cases.json','pilot/candidate.vcd','pilot/candidate.log'],
                     limitation='Synthetic source-register/ROM/buffer/destination path; not a complete schematic-derived CPU.'),
            evidence('mutations','Fault-detection qualification','pass' if all(x['status']=='pass' for x in results[1:]) else 'fail',
                     'Exact expected monitor sets checked for setup, hold, pulse, reset, contention and wiring faults.',artifacts=['pilot/cases.json']),
            evidence('timing','Phase timing budget','fail' if budget['documented_margin_ns']<0 else 'limited',
                     f"Documented phase margin {budget['documented_margin_ns']} ns; candidate margin +{budget['candidate_margin_ns']} ns.",
                     budget=budget,artifacts=['pilot/budget.json'],
                     limitation='Candidate separation is a stimulus, not a change to or qualification of the physical clock.')]

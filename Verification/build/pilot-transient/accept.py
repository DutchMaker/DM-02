"""Evaluate the unchanged PILOT-03 requirement against a bounded experiment.

This accepts the analogue method at the fully specified nominal model point.
It does not accept PILOT-05, the physical operating-envelope requirement.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(contract,data,requirements):
    """Require all numerical checks; do not trust a simulator's pass flag."""
    def require(condition,reason):
        if not condition: raise ValueError(reason)
    pilot=requirements['pilot']
    expected={'source_tco_ns':pilot['source_tco_ns'],'rom_access_ns':pilot['rom_access_ns'],
        'buffer_delay_ns':pilot['buffer_delay_ns'],'capture_ns':pilot['candidate_phase_ns'],
        'setup_ns':pilot['setup_ns'],'hold_ns':pilot['hold_ns'],'uncertainty_ns':pilot['clock_uncertainty_ns'],
        'high_threshold_v':2.0,'low_threshold_v':0.8,'supply_v':5.0,'temperature_c':25.0,
        'die_capacitance_pf':4.0,'total_external_load_pf':50.0,'opposing_fixture_resistance_ohm':1000.0}
    for key,value in expected.items(): require(contract[key]==value,'Contract mismatch: '+key)
    start=pilot['candidate_phase_ns']-pilot['setup_ns']-pilot['clock_uncertainty_ns']
    end=pilot['candidate_phase_ns']+pilot['hold_ns']+pilot['clock_uncertainty_ns']
    require(contract['valid_window_start_ns']==start and contract['valid_window_end_ns']==end,'Capture window changed')
    require(contract['shape_launch_ns']==sum(pilot[k] for k in ('source_tco_ns','rom_access_ns','buffer_delay_ns')),'Launch budget changed')
    require(contract['receiver_input_allocation_pf']+contract['route_socket_probe_allocation_pf']==50,'Load accounting')
    require(contract['qualified_corner']=='typ','Unqualified corner promoted')
    correlation=data['correlation']
    expected_correlation={f'correlation-{col}-{edge}-{v}' for col,supply in ((1,5.0),(2,4.5))
        for edge in ('rising','falling') for v in (0.0,supply)}
    require({r['case'] for r in correlation}==expected_correlation and len(correlation)==8,'Fixture coverage')
    for r in correlation:
        require(r['max_difference_v']<=contract['fixture_max_voltage_error_v'],'Fixture voltage correlation')
        require(r['threshold_difference_ns']<=contract['fixture_threshold_error_ns'],'Fixture timing correlation')
    loads=data['loads']
    faults=('normal','overload','premature-capture','late-launch','disabled')
    require({r['case'] for r in loads}=={edge+'-'+fault for edge in ('rising','falling') for fault in faults}
        and len(loads)==10,'Load/fault coverage')
    for row in loads:
        require(row['case']==row['edge']+'-'+row['fault'],'Case identity')
        measured=row['window_min_v']>=2.0 if row['edge']=='rising' else row['window_max_v']<=.8
        require(row['passed']==measured,'Claimed voltage verdict disagrees with measurements')
        require(measured==(row['fault']=='normal'),'Positive case failed or fault escaped')
        expected_cap=contract['faults']['overload_pf'] if row['fault']=='overload' else 50
        require(row['capacitance_pf']==expected_cap,'Load changed')
        require(row['fixture_r_ohm']==1000 and row['fixture_v']==(0 if row['edge']=='rising' else 5),'Resistive fixture changed')
        capture=contract['faults']['premature_capture_ns'] if row['fault']=='premature-capture' else contract['capture_ns']
        require(row['window_start_ns']==capture-contract['setup_ns']-contract['uncertainty_ns'] and
            row['window_end_ns']==capture+contract['hold_ns']+contract['uncertainty_ns'],'Measured wrong window')
        if row['fault']=='normal':
            require(row['stable_threshold_ns']<=start and row['setup_margin_ns']>0,'Late stable threshold')
            require(abs(row['setup_margin_ns']-(start-row['stable_threshold_ns']))<1e-8,'Margin arithmetic')
    independent=data['independent']
    require({r['case'] for r in independent}=={'rising-normal','falling-normal','rising-overload','falling-overload'} and len(independent)==4,'Independent solver coverage')
    for row in independent:
        original=next(r for r in loads if r['case']==row['case'])
        require(row['max_voltage_difference_v']<=contract['independent_solver_max_voltage_error_v'],'Independent solver disagreement')
        require(row['measured']['passed']==original['passed'],'Independent capture verdict disagrees')
    require({r['case'] for r in data['refinements']}=={'rising-normal','falling-normal'} and len(data['refinements'])==2,'Refinement coverage')
    require(all(r['measured']['passed'] and r['threshold_difference_ns']<=contract['refinement_threshold_difference_ns']
        for r in data['refinements']),'Numerical refinement unstable')
    conversion=data['conversion_faults']
    require(len(conversion)==1 and conversion[0]['fault']=='die-capacitance-times-ten','Missing conversion fault')
    require(conversion[0]['max_difference_v']>contract['fixture_max_voltage_error_v'],'Conversion fault escaped correlation')
    require(any(r['corner']=='max' and r['edge']=='rising' for r in data['rejected_corners']),'Fast-corner limitation lost')
    return dict(passed=True,positive_cases=2,physical_fault_cases=8,conversion_fault_cases=1,
        fixture_correlations=8,independent_cases=4,refinements=2,
        minimum_setup_margin_ns=min(r['setup_margin_ns'] for r in loads if r['fault']=='normal'))


def main():
    contract=json.loads((HERE/'contract.json').read_text())
    data=json.loads((HERE/'exploration.json').read_text())
    requirements=json.loads((ROOT/'Verification/requirements.json').read_text())
    models=json.loads((ROOT/'Verification/models.json').read_text())
    for name,value in data['method_hashes'].items():
        assert digest(HERE/name)==value,'Experiment method changed since execution: '+name
    assert digest(HERE.parent/'pilot-driver/audit.py')==data['audit_sha256']
    driver=json.loads((HERE.parent/'pilot-driver/summary.json').read_text())
    assert driver['model_sha256']==data['model_sha256'] and driver['normalized_checker']['passed']
    assert next(m for m in models['models'] if m['id']=='hct245')['candidate_mpn']==contract['part']
    assert next(m for m in models['models'] if m['id']=='hct574')['candidate_mpn']=='SN74HCT574N'
    receiver=(ROOT/'Verification/vendor/controller/sn74hct574.txt').read_text()
    assert re.search(r'VIH\s+High-level input voltage.*\s2\s+',receiver)
    assert re.search(r'VIL\s+Low-level input voltage.*0\.8',receiver)
    assert re.search(r'Ci\s+4\.5 V to 5\.5 V\s+3\s+10',receiver)
    checked=evaluate(contract,data,requirements)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'],
        capture_output=True,text=True,timeout=120)
    (HERE/'tests.log').write_text(tests.stdout+tests.stderr)
    assert tests.returncode==0,tests.stdout+tests.stderr
    sources=[]
    for relative in ('Verification/requirements.json','Verification/models.json',
                     'Verification/vendor/controller/sn74hct574.txt','Verification/build/pilot-driver/audit.py',
                     'Verification/build/pilot-driver/summary.json'):
        source=ROOT/relative;dest=HERE/'sources'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest)
        sources.append(dict(source=relative,sha256=digest(source),archived=str(dest.relative_to(HERE))))
    (HERE/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
    requirement=next(r for r in requirements['requirements'] if r['id']=='PILOT-03')
    assert requirement['text']=='Loaded output reaches the required voltage before capture in a bounded analogue experiment'
    acceptance=dict(created_at=datetime.now(timezone.utc).isoformat(),requirement=requirement,
        requirement_status='pass',scope=contract['scope'],checks=checked,
        acceptance_reason='The unchanged requirement asks for a bounded analogue experiment. The fully specified nominal model point passes the unchanged pilot capture window, independent integration and injected faults. Full physical/envelope qualification belongs to the distinct PILOT-05 requirement and is not accepted here.',
        physical_clock_qualified=False,full_operating_envelope_qualified=False,
        normal_full_run_report_modified=False,
        evidence_sha256=digest(HERE/'exploration.json'),contract_sha256=digest(HERE/'contract.json'),
        tests_sha256=digest(HERE/'tests.log'))
    (HERE/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
    evidence=dict(id='analog',title='Bounded manufacturer-model loaded-output experiment',status='pass',
        summary=f"PILOT-03: both 50 pF / 1 kohm transitions pass at 5 V / 25 C; {checked['minimum_setup_margin_ns']:.3f} ns minimum margin. Eight load/timing/drive faults and one conversion fault detected.",
        requirement_status='pass',scope=contract['scope'],limitation='PILOT-05 and full physical/PVT qualification remain open.',
        artifacts=['pilot-transient/acceptance.json','pilot-transient/contract.json','pilot-transient/exploration.json','pilot-transient/tests.log'])
    (HERE/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(checked))


if __name__=='__main__': main()

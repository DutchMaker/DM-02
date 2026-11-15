"""Evaluate the unchanged PILOT-03 requirement against a bounded experiment.

This accepts the analogue method at the fully specified nominal model point.
It does not accept PILOT-05, the physical operating-envelope requirement.
"""
import math


def evaluate(contract,data,requirements):
    """Require all numerical checks; do not trust a simulator's pass flag."""
    def require(condition,reason):
        if not condition: raise ValueError(reason)
    pilot=requirements['pilot']
    expected={'source_tco_ns':pilot['source_tco_ns'],'rom_access_ns':pilot['rom_access_ns'],
        'buffer_delay_ns':pilot['buffer_delay_ns'],'capture_ns':pilot['candidate_phase_ns'],
        'setup_ns':pilot['setup_ns'],'hold_ns':pilot['hold_ns'],'uncertainty_ns':pilot['clock_uncertainty_ns'],
        'high_threshold_v':2.0,'low_threshold_v':0.8,'supply_v':5.0,'temperature_c':25.0,
        'die_capacitance_pf':4.0,'total_external_load_pf':50.0,'opposing_fixture_resistance_ohm':1000.0,
        'fixture_max_voltage_error_v':.01,'fixture_threshold_error_ns':.1,
        'independent_solver_max_voltage_error_v':.01,'refinement_threshold_difference_ns':.1}
    for key,value in expected.items(): require(contract[key]==value,'Contract mismatch: '+key)
    start=pilot['candidate_phase_ns']-pilot['setup_ns']-pilot['clock_uncertainty_ns']
    end=pilot['candidate_phase_ns']+pilot['hold_ns']+pilot['clock_uncertainty_ns']
    require(contract['valid_window_start_ns']==start and contract['valid_window_end_ns']==end,'Capture window changed')
    require(contract['shape_launch_ns']==sum(pilot[k] for k in ('source_tco_ns','rom_access_ns','buffer_delay_ns')),'Launch budget changed')
    require(contract['receiver_input_allocation_pf']+contract['route_socket_probe_allocation_pf']==50,'Load accounting')
    require(contract['qualified_corner']=='typ','Unqualified corner promoted')
    require(contract['faults']==dict(overload_pf=5000.,premature_capture_ns=180.,late_shape_launch_ns=300.,disabled_driver=True),'Fault stimulus changed')
    def finite(value):
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    def numeric_tree(value):
        if isinstance(value,dict): return all(numeric_tree(v) for v in value.values())
        if isinstance(value,list): return all(numeric_tree(v) for v in value)
        return not isinstance(value,(int,float)) or math.isfinite(value)
    require(numeric_tree(data),'Nonfinite numerical evidence')
    correlation=data['correlation']
    expected_correlation={f'correlation-{col}-{edge}-{v}' for col,supply in ((1,5.0),(2,4.5))
        for edge in ('rising','falling') for v in (0.0,supply)}
    require({r['case'] for r in correlation}==expected_correlation and len(correlation)==8,'Fixture coverage')
    for r in correlation:
        require(0<=r['max_difference_v']<=contract['fixture_max_voltage_error_v'],'Fixture voltage correlation')
        require(0<=r['threshold_difference_ns']<=contract['fixture_threshold_error_ns'],'Fixture timing correlation')
    loads=data['loads']
    faults=('normal','overload','premature-capture','late-launch','disabled')
    require({r['case'] for r in loads}=={edge+'-'+fault for edge in ('rising','falling') for fault in faults}
        and len(loads)==10,'Load/fault coverage')
    for row in loads:
        require(row['case']==row['edge']+'-'+row['fault'],'Case identity')
        require(finite(row['window_min_v']) and finite(row['window_max_v']) and row['window_min_v']<=row['window_max_v'],'Invalid voltage interval')
        launch=contract['faults']['late_shape_launch_ns'] if row['fault']=='late-launch' else contract['shape_launch_ns']
        require(row.get('shape_launch_ns')==launch and row.get('driver_enabled')==(row['fault']!='disabled'),'Stimulus identity')
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
        require(0<=row['max_voltage_difference_v']<=contract['independent_solver_max_voltage_error_v'],'Independent solver disagreement')
        require(row['measured']['passed']==original['passed'],'Independent capture verdict disagrees')
    require({r['case'] for r in data['refinements']}=={'rising-normal','falling-normal'} and len(data['refinements'])==2,'Refinement coverage')
    require(all(r['measured']['passed'] and 0<=r['threshold_difference_ns']<=contract['refinement_threshold_difference_ns']
        for r in data['refinements']),'Numerical refinement unstable')
    conversion=data['conversion_faults']
    require(len(conversion)==1 and conversion[0]['fault']=='die-capacitance-times-ten','Missing conversion fault')
    require(conversion[0]['max_difference_v']>contract['fixture_max_voltage_error_v'],'Conversion fault escaped correlation')
    require(any(r['corner']=='max' and r['edge']=='rising' for r in data['rejected_corners']),'Fast-corner limitation lost')
    return dict(passed=True,positive_cases=2,physical_fault_cases=8,conversion_fault_cases=1,
        fixture_correlations=8,independent_cases=4,refinements=2,
        minimum_setup_margin_ns=min(r['setup_margin_ns'] for r in loads if r['fault']=='normal'))

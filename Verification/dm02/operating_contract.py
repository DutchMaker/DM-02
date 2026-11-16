"""Live engineering requirements, separate from CP1's frozen simulation inputs."""
from copy import deepcopy
from itertools import product
import json
import math
from .common import ROOT, VROOT, digest

PATH = VROOT/'operating-contract.json'
REQUIRED_EVIDENCE = {
    'Verification/requirements.json', 'Verification/targets/cp1/lock.json',
    'Verification/build/cp1-readiness/study-validation.json',
    'Verification/build/cp1-readiness/timing-screen.json',
    'Verification/build/cp1-readiness/sweep-capture/f5-c1-d0.37-cases1-ppm30/result.json',
}


def validate(contract):
    if contract['schema_version'] != 1 or contract['physical_qualification'] is not False:
        raise ValueError('Operating contract is a target, not physical qualification')
    clock = contract['clock']
    for key in ('oscillator_nominal_hz', 'oscillator_periods_per_microcycle', 'microcycle_nominal_hz'):
        value = clock[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid clock quantity: '+key)
    if clock['oscillator_periods_per_microcycle'] != 8:
        raise ValueError('CP1 requires eight oscillator periods per microcycle')
    if clock['oscillator_nominal_hz'] / 8 != clock['microcycle_nominal_hz']:
        raise ValueError('Oscillator and microcycle rates disagree')
    ppm = clock['oscillator_tolerance_ppm']
    if isinstance(ppm, bool) or not isinstance(ppm, (int, float)) or not math.isfinite(ppm) or not 0 <= ppm < 1e6:
        raise ValueError('Invalid oscillator tolerance')
    if clock['preferred_rate_is_mandatory'] is not False:
        raise ValueError('Owner-approved preferred rate is not mandatory')
    if clock['phase_separation_periods'] != 3 or clock['phase_pulse_periods'] != 4:
        raise ValueError('Phase geometry differs from the CP1 counted clock')
    if not REQUIRED_EVIDENCE.issubset(contract['evidence']):
        raise ValueError('Operating contract requires its baseline and decision evidence')
    for field, keys, expected in (('supply', ('min_v', 'max_v'), (4.75, 5.25)),
                                  ('ambient', ('min_c', 'max_c'), (0, 50))):
        if tuple(contract[field][k] for k in keys) != expected:
            raise ValueError('Owner voltage/temperature envelope changed: '+field)
    reset = contract['startup_reset']
    for value in (reset['minimum_guard_after_valid_supply_ms'], reset['minimum_reset_request_ns'],
                  clock['oscillator_startup_max_ms'], contract['modes']['maximum_stop_microcycles'],
                  contract['timing_acceptance']['minimum_setup_reserve_ns']):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid operating-contract timing limit')
    if reset['minimum_guard_after_valid_supply_ms'] < clock['oscillator_startup_max_ms']:
        raise ValueError('Reset guard is shorter than oscillator startup')
    if reset['minimum_reset_request_ns'] < 1000:
        raise ValueError('Reset request is shorter than the CP1 boundary contract')
    modes = contract['modes']
    if modes['idle_phase2'] != 0 or modes['idle_phase3'] != 0:
        raise ValueError('Stopped phases must inhibit writes')
    if set(modes['allowed']) != {'continuous','halt-resume','single-step','reset-abort'}:
        raise ValueError('Unexpected clock mode contract')
    matrix = contract['qualification_matrix']
    for key, values in (('supply_points_v', [4.75, 5.0, 5.25]), ('ambient_points_c', [0, 25, 50])):
        if matrix[key] != values:
            raise ValueError('Qualification matrix does not cover the selected envelope: '+key)
    if matrix['digital_ppm'] != [-ppm, 0, ppm]:
        raise ValueError('Digital sensitivity matrix differs from oscillator tolerance')
    allocations = contract['timing_acceptance']['conditional_allocations']
    if matrix['digital_corners'] != list(range(10)) or matrix['digital_duties'] != [allocations['receiver_duty_min'], .5, allocations['receiver_duty_max']]:
        raise ValueError('Digital sensitivity coverage is incomplete')
    if not 0 < allocations['receiver_duty_min'] <= .5 <= allocations['receiver_duty_max'] < 1:
        raise ValueError('Invalid receiver-duty sensitivity range')
    if {t['id'] for t in matrix['physical_tests']} != {'supply-startup','clock-modes','data-timing','bus-release','sram-turnaround','functional-repeat'}:
        raise ValueError('Physical qualification groups are incomplete')
    if len({t['id'] for t in matrix['physical_tests']}) != len(matrix['physical_tests']):
        raise ValueError('Duplicate qualification test ID')
    return contract


def load(path=PATH, root=ROOT):
    contract = validate(json.loads(path.read_text()))
    for name, expected in contract['evidence'].items():
        source = (root/name).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file() or digest(source) != expected:
            raise ValueError('Missing or changed operating-contract evidence: '+name)
    lock = json.loads((root/'Verification/targets/cp1/lock.json').read_text())
    if contract['design_revision'] != lock['revision']:
        raise ValueError('Operating contract refers to another design revision')
    clock_path = 'Verification/clock-parts.json'
    origin = root/'Verification/targets/cp1/overlay' if clock_path in lock['overlay'] else root
    source = origin/clock_path
    if digest(source) != lock['sources'][clock_path]:
        raise ValueError('Clock source differs from the accepted baseline')
    oscillator = json.loads(source.read_text())['oscillator']
    for field, key in (('oscillator_mpn','mpn'), ('oscillator_nominal_hz','frequency_hz'),
                       ('oscillator_tolerance_ppm','stability_ppm'), ('oscillator_startup_max_ms','startup_max_ms')):
        if contract['clock'][field] != oscillator[key]:
            raise ValueError('Selected clock differs from accepted evidence: '+field)
    study = json.loads((root/'Verification/build/cp1-readiness/study-validation.json').read_text())
    if not study['passed'] or study['physical_qualification']:
        raise ValueError('Readiness study must be validated digital evidence')
    recommendation = study['recommendation']
    if (recommendation['oscillator_hz'],recommendation['microcycle_hz']) != (
            contract['clock']['oscillator_nominal_hz'],contract['clock']['microcycle_nominal_hz']):
        raise ValueError('Selected rate differs from the clock recommendation')
    return contract


def effective_requirements(baseline, contract):
    """Only the live operating envelope changes; preserve the pilot and gate map."""
    validate(contract)
    requirements = deepcopy(baseline)
    requirements['revision'] = contract['revision']
    requirements['status'] = contract['status']
    requirements['historical_baseline'] = dict(revision=baseline['revision'],
        operating_envelope=deepcopy(baseline['operating_envelope']),
        source='Verification/requirements.json', scope='Frozen reference/pilot and CP1-R2 simulation input')
    requirements['operating_envelope'] = dict(clock_hz=contract['clock']['microcycle_nominal_hz'],
        clock_unit='microcycles per second', oscillator_hz=contract['clock']['oscillator_nominal_hz'],
        supply_min_v=contract['supply']['min_v'], supply_max_v=contract['supply']['max_v'],
        ambient_min_c=contract['ambient']['min_c'], ambient_max_c=contract['ambient']['max_c'])
    requirements['operating_contract'] = 'Verification/operating-contract.json'
    requirements['pilot_scope'] = 'Historical verification-method stimulus; not the CP1-OC1 machine clock. New machine budgets use operating_contract.'
    return requirements


def matrix(contract):
    validate(contract)
    clock = contract['clock']; spec = contract['qualification_matrix']
    frequency = clock['oscillator_nominal_hz']; ppm = clock['oscillator_tolerance_ppm']
    period_min = 1e9 / (frequency * (1 + ppm/1e6))
    allocations = contract['timing_acceptance']['conditional_allocations']
    common = dict(contract_revision=contract['revision'], design_revision=contract['design_revision'],
                  oscillator_nominal_hz=frequency, microcycle_nominal_hz=clock['microcycle_nominal_hz'])
    return dict(**common, physical_qualification=False, status='specified coverage; execution not implied',
        derived_limits=dict(oscillator_min_hz=frequency*(1-ppm/1e6), oscillator_max_hz=frequency*(1+ppm/1e6),
            microcycle_min_hz=clock['microcycle_nominal_hz']*(1-ppm/1e6),
            microcycle_max_hz=clock['microcycle_nominal_hz']*(1+ppm/1e6),
            oscillator_period_min_ns=period_min,
            conditional_phase_separation_min_ns=clock['phase_separation_periods']*period_min-allocations['phase_output_spread_ns'],
            conditional_phase_pulse_min_ns=clock['phase_pulse_periods']*period_min-allocations['phase_output_spread_ns'],
            maximum_stop_ns=contract['modes']['maximum_stop_microcycles']*1e9/clock['microcycle_nominal_hz'],
            minimum_setup_reserve_ns=contract['timing_acceptance']['minimum_setup_reserve_ns']),
        physical=[dict(**common,test=t['id'],issue=t['issue'],supply_v=v,ambient_c=c,
                       stimulus=t['stimulus'],acceptance=t['pass'],status='not-run')
                  for t,v,c in product(spec['physical_tests'],spec['supply_points_v'],spec['ambient_points_c'])],
        digital=[dict(**common,corner=c,duty=d,ppm=p,status='coverage-request-only')
                 for c,d,p in product(spec['digital_corners'],spec['digital_duties'],spec['digital_ppm'])],
        measurement_record=spec['measurement_record'])

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from dm02 import cp1, operating_contract as oc
from dm02.common import digest
from dm02.reporting import milestones


class OperatingContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(oc.PATH.read_text())
        self.baseline = json.loads((oc.VROOT/'requirements.json').read_text())

    def test_selected_clock_is_supported_by_pinned_sources(self):
        loaded = oc.load()
        self.assertEqual(loaded['revision'], 'CP1-OC1')
        self.assertEqual(loaded['clock']['microcycle_nominal_hz'], 500000)
        self.assertFalse(loaded['physical_qualification'])

    def test_new_envelope_does_not_rewrite_historical_pilot_or_gate_map(self):
        original = deepcopy(self.baseline)
        active = oc.effective_requirements(self.baseline, self.contract)
        self.assertEqual(self.baseline, original)
        self.assertEqual(active['operating_envelope']['clock_hz'], 500000)
        self.assertEqual(active['historical_baseline']['operating_envelope']['clock_hz'], 1000000)
        for field in ('pilot', 'requirements', 'milestones', 'architecture'):
            self.assertEqual(active[field], original[field])
        lock = json.loads((cp1.TARGET/'lock.json').read_text())
        checks = cp1.checks_from_evidence(lock)
        self.assertEqual([m['passed'] for m in milestones(active, checks)], [3,3,8])
        for check in checks:
            if check['id'] in ('timing','physical-clock','module-timing','pcb','bench'):
                self.assertNotEqual(check['status'], 'pass')

    def test_matrix_has_all_physical_corners_without_claiming_measurements(self):
        matrix = oc.matrix(self.contract)
        self.assertEqual(len(matrix['physical']), 54)
        self.assertEqual(len(matrix['digital']), 90)
        self.assertEqual({(r['supply_v'], r['ambient_c']) for r in matrix['physical']},
                         {(v,t) for v in (4.75,5.0,5.25) for t in (0,25,50)})
        self.assertEqual({r['status'] for r in matrix['physical']}, {'not-run'})
        self.assertEqual({r['status'] for r in matrix['digital']}, {'coverage-request-only'})
        self.assertTrue(all(r['microcycle_nominal_hz']==500000 and r['contract_revision']=='CP1-OC1'
                            for r in matrix['physical']+matrix['digital']))
        limits = matrix['derived_limits']
        self.assertAlmostEqual(limits['microcycle_max_hz'], 500015)
        self.assertAlmostEqual(limits['microcycle_min_hz'], 499985)
        self.assertAlmostEqual(limits['conditional_phase_separation_min_ns'], 717.477500675, places=6)
        self.assertEqual(limits['maximum_stop_ns'], 8000)

    def test_unsafe_or_incomplete_contract_mutations_are_rejected(self):
        mutations = [
            lambda c: c.update(physical_qualification=True),
            lambda c: c['clock'].update(microcycle_nominal_hz=1000000),
            lambda c: c['clock'].update(oscillator_tolerance_ppm=float('nan')),
            lambda c: c['clock'].update(oscillator_periods_per_microcycle=4),
            lambda c: c['clock'].update(phase_separation_periods=4),
            lambda c: c['clock'].update(preferred_rate_is_mandatory=True),
            lambda c: c['supply'].update(min_v=4.5),
            lambda c: c['startup_reset'].update(minimum_guard_after_valid_supply_ms=5),
            lambda c: c['startup_reset'].update(minimum_guard_after_valid_supply_ms=float('nan')),
            lambda c: c['startup_reset'].update(minimum_reset_request_ns=100),
            lambda c: c['modes'].update(idle_phase3=1),
            lambda c: c['timing_acceptance'].update(minimum_setup_reserve_ns=0),
            lambda c: c['qualification_matrix'].update(supply_points_v=[5.0]),
            lambda c: c['qualification_matrix'].update(digital_corners=[1]),
            lambda c: c['qualification_matrix']['physical_tests'].pop(),
            lambda c: c['evidence'].clear(),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(mutation=i):
                changed = deepcopy(self.contract); mutate(changed)
                with self.assertRaises(ValueError): oc.validate(changed)

    def test_missing_or_changed_decision_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in self.contract['evidence']:
                target = root/name; target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(oc.ROOT/name,target)
            clock = Path('Verification/targets/cp1/overlay/Verification/clock-parts.json')
            (root/clock).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(oc.ROOT/clock,root/clock)
            path = root/'contract.json'; path.write_text(json.dumps(self.contract))
            self.assertEqual(oc.load(path,root)['revision'],'CP1-OC1')
            evidence = root/'Verification/build/cp1-readiness/study-validation.json'
            original = evidence.read_bytes(); evidence.write_bytes(original+b' ')
            with self.assertRaisesRegex(ValueError,'changed operating-contract evidence'):
                oc.load(path,root)
            evidence.unlink()
            with self.assertRaisesRegex(ValueError,'Missing or changed'):
                oc.load(path,root)

    def test_consistent_but_unverified_faster_rate_is_rejected(self):
        changed = deepcopy(self.contract)
        changed['clock'].update(oscillator_nominal_hz=8000000,microcycle_nominal_hz=1000000)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'contract.json'; path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'differs from accepted evidence'):
                oc.load(path)

    def test_frozen_baseline_and_lock_still_have_their_original_hashes(self):
        for name in ('Verification/requirements.json','Verification/targets/cp1/lock.json'):
            self.assertEqual(digest(oc.ROOT/name),self.contract['evidence'][name])


if __name__=='__main__':
    unittest.main()

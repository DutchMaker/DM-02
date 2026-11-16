from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from dm02 import release_requirements as rr,release_sim as sim,release_evidence as evidence
from dm02.release_measurements import plan


class ReleaseRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph=rr.Graph();cls.audit=cls.graph.audit()

    def test_native_driver_ownership_and_command_paths(self):
        data=[r for r in self.audit['buses'] if r['bus']=='DATA']
        ram=[r for r in self.audit['buses'] if r['bus']=='RAM']
        self.assertEqual(len(data),8);self.assertEqual(len(ram),8)
        self.assertTrue(all(len(r['driver_pins'])==1 for r in data))
        self.assertTrue(all(len(r['driver_pins'])==2 for r in ram))
        self.assertEqual(self.audit['truth_cases'],8192)
        self.assertEqual(self.audit['steady_state_dual_drive_cases'],0)
        self.assertEqual(self.audit['conditional_blank_ns'],dict(read_to_write=36.5,write_to_read=48,source3_release=76.5))
        self.assertTrue(self.audit['paths']['ram_we_n']['a14'])
        self.assertTrue(self.audit['paths']['mar_low_oe_n'])

    def test_direction_control_and_extra_driver_faults_rejected(self):
        faults=rr.mutations(self.graph.inventory)
        self.assertEqual(len(faults),4);self.assertTrue(all(r['detected'] for r in faults.values()))

    def test_same_data_contention_and_early_capture_fail_dynamically(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('same-data-overlap','early-read-capture'):
                result=sim.short(Path(tmp)/name,self.graph,sim.CASES[name])
                self.assertTrue(result['expectation_met']);self.assertNotEqual(result['exit_code'],0)

    def test_measurement_plan_cannot_masquerade_as_qualification(self):
        p=plan(self.audit)
        self.assertFalse(p['physical_qualification']);self.assertTrue(p['review_required'])
        self.assertEqual(len(p['driver_cases']),48)
        self.assertEqual(p['supply_points_v'],[4.75,5.0,5.25]);self.assertEqual(p['ambient_points_c'],[0,25,50])
        self.assertTrue(all(r['actual_total_load_pf'] is None and r['actual_max_release_ns'] is None for r in p['driver_cases']))

    def test_repeated_reads_do_not_inflate_opposing_turnovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.csv'
            p.write_text('time_ns,ram_oe_n,ram_we_n,writer_oe_n\n0,1,1,1\n10,1,1,0\n20,1,1,1\n30,0,1,1\n40,1,1,1\n50,0,1,1\n')
            r=evidence.opposing_turnovers(p)
            self.assertEqual(r['write_to_read'],dict(count=1,minimum_requested_gap_ns=10))

    def test_complete_evidence_replay(self):
        _,r=evidence.load()
        self.assertFalse(r['physical_qualification']);self.assertEqual(r['short_faults'],5)
        for name in ('boot-guarded-max','boot-zero','boot-mixed2','boot-mixed3'):
            self.assertEqual(r['boots'][name]['opposing_turnovers']['read_to_write']['count'],167)

    def test_missing_events_rejected_before_replay(self):
        lock=json.loads(evidence.LOCK.read_text())
        del lock['artifacts']['cp1-release/iteration-2/boot-zero/release-events.csv']
        with self.assertRaisesRegex(ValueError,'Missing RR1 artifact'):evidence.verify(lock)

    def test_all_original_boot_inputs_are_declared(self):
        lock=json.loads(evidence.LOCK.read_text())
        for name in evidence.BOOT_CASES:
            run=json.loads((rr.STUDY/evidence.ACCEPTED/name/'result.json').read_text())
            self.assertTrue(set(run['input_hashes'])<=lock['artifacts'].keys())


if __name__=='__main__':unittest.main()

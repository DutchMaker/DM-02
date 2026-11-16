from copy import deepcopy
import json
import unittest
from dm02 import oscillator_interface as oi,oscillator_waveforms as waves,oscillator_evidence as evidence


class OscillatorInterfaceTests(unittest.TestCase):
    def test_native_first_receivers_and_complete_frontend_loads(self):
        result=oi.audit();cpu,text=result['frontends']
        self.assertEqual([f['raw']['attached_pin_count'] for f in result['frontends']],[2,2])
        self.assertEqual(cpu['raw']['planning_total_pf'],14)
        self.assertEqual(cpu['timing_fixture_edge_ns'],3);self.assertEqual(text['timing_fixture_edge_ns'],6)
        stage=next(r for r in cpu['conditioned'] if r['driver']=='U1010.18')
        self.assertEqual(stage['ic_only_pf'],40);self.assertEqual(stage['planning_margin_pf'],2)

    def test_family_option_probe_and_topology_faults_rejected(self):
        results=oi.faults();self.assertEqual(len(results),6)
        self.assertTrue(all(r['detected'] for r in results.values()))

    def test_half_supply_symmetry_cannot_be_reused_at_ttl_threshold(self):
        r=waves.analyze(waves.waveform(duty=.45,edge=10),5)
        self.assertAlmostEqual(r['half_supply_duty']['min'],.45)
        self.assertGreater(r['timing_1v5_high_ns']['min'],250*.45)
        self.assertFalse(r['numerical_edge_comparison']['CPU_3ns'])
        self.assertFalse(r['numerical_edge_comparison']['TEXT_6ns'])
        self.assertFalse(r['physical_qualification'])

    def test_missing_cycle_and_extra_edge_detected(self):
        for fault in ('extra-edge','missing-cycle'):
            r=waves.analyze(waves.waveform(fault=fault),5)
            self.assertFalse(r['nominal_period_screen'])

    def test_brownout_restarts_guard_and_unknown_clock_blocks_release(self):
        self.assertTrue(waves.startup(25_000_000,0,10_000_000,True))
        self.assertFalse(waves.startup(25_000_000,15_000_000,20_000_000,True))
        self.assertFalse(waves.startup(25_000_000,0,10_000_000,False))
        self.assertFalse(waves.startup(25_000_000,0,None,True))

    def test_nonmonotone_sample_time_rejected(self):
        with self.assertRaisesRegex(ValueError,'time must increase'):
            waves.analyze([(0,0),(10,5),(10,0),(20,5)],5)

    def test_full_source_and_reproducible_evidence(self):
        _,r=evidence.load();self.assertEqual(len(r['waveforms']['cases']),81)
        self.assertFalse(r['hardware_changed']);self.assertFalse(r['physical_qualification'])
        self.assertTrue(all(p['actual_raw_capacitance_pf'] is None for p in r['measurement_plan']['links']))

    def test_missing_visual_waveform_source_rejected(self):
        lock=json.loads(evidence.LOCK.read_text())
        del lock['artifacts']['cp1-oscillator/sources/sn74ahct04-waveform.pdf']
        with self.assertRaisesRegex(ValueError,'Missing OS1 artifact'):evidence.verify(lock)


if __name__=='__main__':unittest.main()

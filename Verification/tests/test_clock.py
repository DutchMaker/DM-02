from copy import deepcopy
import tempfile
from pathlib import Path
import unittest
from dm02.clock import Clock, budget, simulate
from dm02.electrical import audit


class CountedClock(unittest.TestCase):
    def setUp(self):
        self.circuit=Clock()
        self.temp=tempfile.TemporaryDirectory(prefix='dm02-clock-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def pin_label(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        component=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in component['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1)
        at[0]['name']=label
        return Clock(sheet)

    def test_core_at_maximum_delay_and_fast_clock(self):
        ok,log=simulate(self.circuit,self.folder,1,0.4,100)
        self.assertTrue(ok,log)
        self.assertIn('steps=24 stops=32 resets=8',log)
        self.assertEqual(audit(self.circuit.sheet)['findings'],[])

    def test_stage_on_same_edge_is_rejected(self):
        ok,log=simulate(self.pin_label('U2','9','CLK_P'),self.folder,1)
        self.assertFalse(ok,log)

    def test_stop_cannot_cut_short_a_cycle(self):
        ok,log=simulate(self.pin_label('U5','1','REQUEST_SYNC'),self.folder)
        self.assertFalse(ok,log)
        self.assertIn('runt phase pulse',log)

    def test_swapped_phase_output_is_rejected(self):
        ok,log=simulate(self.pin_label('U9','4','Q2_n'),self.folder)
        self.assertFalse(ok,log)
        self.assertRegex(log,'launch/capture phase interval|phase polarity/pin mapping')

    def test_wrong_polarity_feedback_is_rejected(self):
        ok,log=simulate(self.pin_label('U5','2','Q3'),self.folder)
        self.assertFalse(ok,log)

    def test_step_pending_must_clear_after_acceptance(self):
        ok,log=simulate(self.pin_label('U7','13','RESET_N_n'),self.folder)
        self.assertFalse(ok,log)
        self.assertIn('failed to stop',log)

    def test_reset_release_on_same_edge_is_rejected(self):
        ok,log=simulate(self.pin_label('U6','11','CLK_P'),self.folder)
        self.assertFalse(ok,log)
        self.assertIn('clock hold',log)

    def test_load_change_invalidates_timing_bound(self):
        self.assertTrue(budget(self.circuit)['passing'])
        # A 1 pF increase crosses the characterized 15 pF gate-output bin.
        self.circuit.parts['constraints']['local_trace_cap_pf']=6
        self.assertFalse(budget(self.circuit)['passing'])

    def test_overloaded_phase_driver_is_not_characterized(self):
        self.assertTrue(all(row['characterized'] for row in self.circuit.load()))
        self.circuit.parts['constraints']['phase_connector_load_pf']=1000
        self.assertFalse(all(row['characterized'] for row in self.circuit.load()))

    def test_jitter_and_startup_constraints_are_not_optional(self):
        self.circuit.parts['constraints']['clock_routing_and_jitter_ns']=10
        self.assertFalse(budget(self.circuit)['passing'])
        self.circuit.parts['constraints']['clock_routing_and_jitter_ns']=2
        self.circuit.parts['constraints']['power_on_reset_after_valid_supply_ms']=10
        self.assertFalse(budget(self.circuit)['passing'])


if __name__=='__main__': unittest.main()

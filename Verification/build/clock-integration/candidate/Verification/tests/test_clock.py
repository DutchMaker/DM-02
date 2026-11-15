from copy import deepcopy
import tempfile
from pathlib import Path
import unittest
from dm02.common import VROOT, command
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
        # One extra pF exceeds the selected oscillator's 15 pF load rating.
        self.circuit.parts['constraints']['local_trace_cap_pf']=6
        self.assertFalse(budget(self.circuit)['passing'])

    def test_overloaded_phase_driver_is_not_characterized(self):
        self.assertTrue(all(row['characterized'] for row in self.circuit.load()))
        self.circuit.parts['constraints']['phase_connector_load_pf']=1000
        self.assertFalse(all(row['characterized'] for row in self.circuit.load()))

    def test_selected_oscillator_pin_package_and_load_contract(self):
        result=self.circuit.oscillator_contract()
        self.assertTrue(result['passed']);self.assertEqual(result['allocated_load_pf'],15)
        self.assertFalse(result['physical_load_qualified'])
        for ref,pin,label in (('Y1','5','5V'),('Y1','8','OSC_TTL'),('Y1','4','5V')):
            with self.subTest(pin=pin),self.assertRaisesRegex(ValueError,'oscillator pin'):
                self.pin_label(ref,pin,label)
        sheet=deepcopy(self.circuit.sheet)
        next(c for c in sheet['components'] if c['ref']=='Y1')['footprint']='Oscillator:Oscillator_DIP-14'
        with self.assertRaisesRegex(ValueError,'footprint'):Clock(sheet)
        self.circuit.parts['oscillator']['output_pin']='8'
        with self.assertRaisesRegex(ValueError,'pin map'):self.circuit.hdl()

    def test_selected_frequency_is_distinct_from_counterfactual_analysis(self):
        timing=budget(self.circuit)
        self.assertTrue(timing['selected_frequency'])
        self.assertEqual(timing['analysis_frequency_hz'],4000000)
        fast=budget(self.circuit,frequency_hz=8000000)
        self.assertFalse(fast['selected_frequency'])
        self.assertEqual(fast['oscillator']['frequency_hz'],4000000)
        self.circuit.parts['oscillator']['frequency_hz']=8000000
        with self.assertRaisesRegex(ValueError,'must be 4 MHz'):self.circuit.hdl()

    def test_clock_monitor_rejects_doubled_actual_stimulus_rate(self):
        self.assertTrue(simulate(self.circuit,self.folder,1)[0])
        text=(VROOT/'hdl/clock_candidate_tb.sv').read_text()
        old='forever begin #(period*(1-duty)); osc=1; #(period*duty); osc=0; end'
        self.assertEqual(text.count(old),1)
        source=self.folder/'bad-rate.sv'
        source.write_text(text.replace(old,'forever begin #(period*(1-duty)/2); osc=1; #(period*duty/2); osc=0; end'))
        code,log=command(['iverilog','-g2012','-s','clock_candidate_tb','-o','bad.vvp','clock.sv',source],cwd=self.folder)
        self.assertEqual(code,0,log)
        code,log=command(['vvp','bad.vvp'],cwd=self.folder)
        self.assertNotEqual(code,0);self.assertIn('FATAL:',log)

    def test_jitter_and_startup_constraints_are_not_optional(self):
        self.circuit.parts['constraints']['clock_routing_and_jitter_ns']=80
        self.assertFalse(budget(self.circuit)['passing'])
        self.circuit.parts['constraints']['clock_routing_and_jitter_ns']=2
        self.circuit.parts['constraints']['power_on_reset_after_valid_supply_ms']=9
        self.assertFalse(budget(self.circuit)['passing'])


if __name__=='__main__': unittest.main()

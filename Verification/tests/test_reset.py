from copy import deepcopy
import unittest
from dm02.reset import Reset


class ResetCircuit(unittest.TestCase):
    def setUp(self): self.circuit=Reset()

    def test_reset_sources_and_indicator(self):
        self.assertEqual(self.circuit.topology(),[])
        for por in (0,1):
            for button in (0,1):
                expected=int(por and button)
                self.assertEqual(self.circuit.evaluate(por,button),
                                 dict(reset_released=expected,led_drive=expected))

    def test_original_switch_short_is_detected(self):
        sheet=deepcopy(self.circuit.sheet)
        sheet['labels'].append(dict(name='~POR',x=6650,y=2250,implicit=False))
        mutant=Reset(sheet)
        self.assertIn('Manual switch shorts an active IC output',mutant.topology())
        with self.assertRaisesRegex(ValueError,'Conflicting reset boundary drivers'):
            mutant.evaluate(1,0)

    def test_led_on_supervisor_is_detected(self):
        sheet=deepcopy(self.circuit.sheet)
        label=next(l for l in sheet['labels'] if l['name']=='RESET_OK_LED' and l['x']==6650)
        label['name']='~POR'
        self.assertTrue(Reset(sheet).topology())

    def test_reset_polarity_fault_is_detected(self):
        sheet=deepcopy(self.circuit.sheet)
        label=next(l for l in sheet['labels'] if l['name']=='RESET_ACTIVE' and l['x']==13950)
        label['name']='~POR'
        mutant=Reset(sheet)
        self.assertNotEqual(mutant.evaluate(1,1)['reset_released'],1)

    def test_original_led_load_is_detected(self):
        sheet=deepcopy(self.circuit.sheet)
        next(c for c in sheet['components'] if c['ref']=='R9')['value']='330'
        self.assertIn('LED series resistor value',Reset(sheet).topology())


if __name__=='__main__': unittest.main()

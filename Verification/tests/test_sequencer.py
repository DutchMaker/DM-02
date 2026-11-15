from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.sequencer import Circuit,fixtures,simulate,budget
from dm02.electrical import audit
from designs.sequencer_candidate import drawing,DEST


class Sequencer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-sequencer-')
        cls.folder=Path(cls.temp.name);cls.coverage=fixtures(cls.folder/'fixtures');cls.circuit=Circuit()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def pin_label(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        c=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in c['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1);at[0]['name']=label
        return Circuit(sheet)

    def gate_input(self,output,old,new):
        circuit=self.circuit
        c=next(c for c in circuit.sheet['components'] if any(p['kind']=='O' and
                 circuit.nodes[c['ref'],p['number']]==circuit.labels[output] for p in c['pins']))
        p=next(p for p in c['pins'] if p['kind']=='I' and circuit.nodes[c['ref'],p['number']]==circuit.labels[old])
        return self.pin_label(c['ref'],p['number'],new)

    def test_fetched_program_at_maximum_delays(self):
        r=simulate(self.circuit,self.folder/'good',1,self.folder/'fixtures')
        self.assertTrue(r['passed'],r['log']);self.assertIn('stepped=12',r['log'])
        self.assertEqual(self.coverage['conditional_branches'],128)
        self.assertEqual(self.coverage['max_tstate'],13)
        self.assertEqual(audit(self.circuit.sheet)['findings'],[])
        self.assertTrue(all(r['within_allocated_test_load'] for r in self.circuit.loads()))
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.circuit)))
        self.assertEqual(DEST.read_text(),drawing())

    def test_sequencing_and_halt_wiring_faults_are_detected(self):
        cases=[('late end sampling',self.pin_label('U1','9','ADVANCE')),
               ('counter load bypass',self.pin_label('U4','9','5V')),
               ('mode publication',self.pin_label('U3','5','STATE_F1')),
               ('IR data lane',self.pin_label('U6','3','GND')),
               ('upper tstate output',self.pin_label('J3','6','GND')),
               ('startup validity bypass',self.gate_input('NEXT_F1','VALID','5V')),
               ('end retention input',self.gate_input('CW_END_n','CW_END','GND')),
               ('fetch increment missing',self.gate_input('PC_INC','FETCH1_n','5V')),
               ('HALT feedback missing',self.gate_input('HALT_NEXT','HALTED_n','5V')),
               ('HALT request bypass',self.gate_input('REQUEST','HALTED_n','5V'))]
        for index,(name,circuit) in enumerate(cases):
            with self.subTest(name=name):
                r=simulate(circuit,self.folder/f'fault{index}',0,self.folder/'fixtures')
                self.assertFalse(r['passed'],r['log'])
                self.assertIn('FATAL:',r['log'])
                self.assertNotIn('SQ watchdog',r['log'])

    def test_interface_constraints_do_not_silently_pass(self):
        c=Circuit();c.parts['constraints']['pc_increment_connector_load_pf']=60
        rows=[r for r in c.loads() if 'PC_INC' in r['labels']]
        self.assertEqual(len(rows),1);self.assertFalse(rows[0]['within_allocated_test_load'])
        c.parts['constraints']['ir_data_setup_ns']=20;c.parts['constraints']['ir_data_hold_ns']=5
        failing=[r['path'] for r in budget(c) if r['margin_ns']<0]
        self.assertIn('IR data setup interface through NAND mux',failing)
        self.assertIn('IR data hold interface with zero contamination',failing)


if __name__=='__main__':unittest.main()

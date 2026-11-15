from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.register_hardware import Circuit,simulate,bus_load,budget
from dm02.alu_hardware import Circuit as Alu,simulate as fetched,fixtures
from dm02.instruction_fixtures import generate
from designs.register_candidate import drawing,DEST


class GeneralRegisters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-rg1-');cls.folder=Path(cls.temp.name);cls.circuit=Circuit()
        fixtures(cls.folder/'fixtures');generate(cls.folder/'fixtures',quick=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def mutation(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        c=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in c['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1);at[0]['name']=label;return Circuit(sheet)

    def test_storage_transfer_and_real_fetched_registers(self):
        self.assertEqual(DEST.read_text(),drawing())
        r=simulate(self.circuit,self.folder/'standalone',1);self.assertTrue(r['passed'],r['log'])
        self.assertIn('captures=2052 transfers=4096 resets=4',r['log'])
        r=fetched(Alu(),self.folder/'fetched',1,self.folder/'fixtures',True,cases=True,registers=self.circuit)
        self.assertTrue(r['passed'],r['log'])
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.circuit)))

    def test_pin_faults_are_detected(self):
        faults=[('input bit','U1','2','DATA1'),('B enable','U5','1','C_LOAD'),
                ('C clock','U8','9','GND'),('H hold','U15','2','GND'),('L high input','U21','13','INPUT6'),
                ('output select','U7','1','C_OE_n'),('missing reset','U3','1','5V'),
                ('reset output inhibition','U26','2','5V')]
        for i,(name,ref,pin,label) in enumerate(faults):
            with self.subTest(name=name):
                r=simulate(self.mutation(ref,pin,label),self.folder/f'fault{i}',0)
                self.assertFalse(r['passed'],r['log']);self.assertIn('FATAL:',r['log']);self.assertNotIn('watchdog',r['log'])

    def test_combined_bus_load_uses_receiver_pins_once(self):
        result=bus_load()
        self.assertEqual([r['input_cap_budget_pf'] for r in result['rows']],[70]*4+[60]*4)
        self.assertTrue(all(r['inputs_alone_exceed_table'] for r in result['rows']))
        for row in result['rows']:
            self.assertEqual(len(row['drivers']),9)
            endpoints={(p['candidate'],p['ref'],p['pin']) for p in row['receivers']}
            self.assertEqual(len(endpoints),len(row['receivers']))
            own=[p for p in row['receivers'] if p['candidate']=='RG1']
            self.assertEqual(len(own),1);self.assertEqual(own[0]['ref'],'U1')
        loads=self.circuit.loads()
        self.assertTrue(all(r['characterized'] for r in loads if not r['shared_data_bus']))
        self.assertEqual({r['cap_pf'] for r in loads if r['shared_data_bus']},{65})


if __name__=='__main__':unittest.main()

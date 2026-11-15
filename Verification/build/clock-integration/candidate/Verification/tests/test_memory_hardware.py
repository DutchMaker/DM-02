from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.memory_hardware import Circuit,simulate,budget,address_load,SOURCE
from dm02.address_hardware import AddressPath
from dm02.alu_hardware import Circuit as Alu,simulate as fetched,fixtures
from dm02.register_hardware import Circuit as Registers
from dm02.instruction_fixtures import generate
from dm02.electrical import audit
from designs.memory_candidate import drawing


class MemoryHardware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-memory-');cls.folder=Path(cls.temp.name);cls.circuit=Circuit()
        fixtures(cls.folder/'fixtures');generate(cls.folder/'fixtures',quick=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def mutate(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        part=next(x for x in sheet['components'] if x['ref']==ref and any(p['number']==pin for p in x['pins']))
        p=next(p for p in part['pins'] if p['number']==pin)
        labels=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(labels),1);labels[0]['name']=label
        return Circuit(sheet)

    def test_protection_routing_io_and_fetched_execution(self):
        self.assertEqual(SOURCE.read_text(),drawing());self.assertEqual(audit(self.circuit.sheet)['findings'],[])
        for corner in (0,1,2):
            r=simulate(self.circuit,self.folder/f'standalone{corner}',corner,quick=True);self.assertTrue(r['passed'],r['log'])
        r=fetched(Alu(),self.folder/'fetched',1,self.folder/'fixtures',True,cases=True,registers=Registers(),address_path=AddressPath(),memory=self.circuit)
        self.assertTrue(r['passed'],r['log'])

    def test_wiring_faults_are_detected(self):
        faults=[('U1','10','ADDRESS1'),('U2','12','ADDRESS1'),('U2','13','RAM1'),
                ('U2','29','WRITE_n'),('U2','24','GND'),('U4','2','INPUT1'),
                ('U5','1','GND'),('U6','1','GND'),('U11','4','IO_DATA_D1'),
                ('U15','4','IO_ADDR_D1'),('U19','1','5V'),('J4','3','PH0')]
        for i,(ref,pin,label) in enumerate(faults):
            with self.subTest(ref=ref,pin=pin):
                r=simulate(self.mutate(ref,pin,label),self.folder/f'fault{i}',0,quick=True)
                self.assertFalse(r['passed'],r['log']);self.assertIn('FATAL:',r['log']);self.assertNotIn('watchdog',r['log'])

    def test_sram_timing_monitors(self):
        # Deliberately impossible requirements for the selected 4 MHz stimulus.
        for field,value,message in [('write_pulse_ns',1000,'write pulse'),('write_data_setup_ns',1200,'data setup'),
                                    ('address_write_setup_ns',2000,'address/select setup'),('write_cycle_ns',6000,'write cycle')]:
            with self.subTest(field=field):
                c=Circuit();c.parts['devices']['AS6C1008-55PCN'][field]=value
                r=simulate(c,self.folder/field,1,quick=True)
                self.assertFalse(r['passed']);self.assertIn('ME1 SRAM '+message,r['log'])

    def test_conditional_budgets_retain_turnaround_gap(self):
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.circuit)))
        self.assertTrue(all(r['within_allocation'] for r in address_load(self.circuit,AddressPath().mar)['rows']))
        loads=self.circuit.loads()
        self.assertTrue(all(r['cap_pf']<=r['limit_pf'] for r in loads if not r['shared_data_bus']))
        ram=[r for r in loads if any(s.startswith('RAM') and s[3:].isdigit() for s in r['labels'])]
        self.assertEqual(len(ram),8)
        self.assertTrue(all(r['cap_pf']==23 and not r['characterized'] for r in ram))


if __name__=='__main__':unittest.main()

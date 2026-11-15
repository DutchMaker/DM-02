from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.address_hardware import Circuit,AddressPath,simulate,budget,SOURCES
from dm02.alu_hardware import Circuit as Alu,simulate as fetched,fixtures
from dm02.register_hardware import Circuit as Registers,bus_load
from dm02.instruction_fixtures import generate
from dm02.electrical import audit
from designs.address_candidate import drawing


class AddressHardware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-address-');cls.folder=Path(cls.temp.name);cls.path=AddressPath()
        fixtures(cls.folder/'fixtures');generate(cls.folder/'fixtures',quick=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def mutate(self,kind,ref,pin,label):
        c=getattr(self.path,kind);sheet=deepcopy(c.sheet)
        part=next(x for x in sheet['components'] if x['ref']==ref and any(p['number']==pin for p in x['pins']))
        p=next(p for p in part['pins'] if p['number']==pin)
        labels=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(labels),1);labels[0]['name']=label
        return AddressPath(**{kind:Circuit(kind,sheet)})

    def test_snapshot_transfer_and_fetched_stack(self):
        for c in (self.path.stack,self.path.mar):
            self.assertEqual(SOURCES[c.kind].read_text(),drawing(c.kind));self.assertEqual(audit(c.sheet)['findings'],[])
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.path)))
        r=simulate(self.path,self.folder/'standalone',1,quick=True);self.assertTrue(r['passed'],r['log'])
        for cases in (False,True):
            r=fetched(Alu(),self.folder/f'fetched{cases}',1,self.folder/'fixtures',True,cases=cases,registers=Registers(),address_path=self.path)
            self.assertTrue(r['passed'],r['log'])

    def test_wiring_and_feedback_faults_are_detected(self):
        faults=[('stack','U12','7','GND'),('stack','U18','7','GND'),('stack','U13','1','LOAD_HIGH'),
                ('stack','U3','1','5V'),('stack','U4','9','LOW_CLOCK'),('stack','U26','2','5V'),
                ('mar','U11','9','LOW_CLOCK'),('mar','U12','4','SP4'),('mar','U22','1','GND'),
                ('mar','U20','1','GND'),('mar','U32','7','GND'),('mar','U2','2','DATA1')]
        for i,(kind,ref,pin,label) in enumerate(faults):
            with self.subTest(kind=kind,ref=ref,pin=pin):
                r=simulate(self.mutate(kind,ref,pin,label),self.folder/f'fault{i}',0,quick=True)
                self.assertFalse(r['passed'],r['log']);self.assertIn('FATAL:',r['log']);self.assertNotIn('watchdog',r['log'])

    def test_loads_and_dedicated_address_receivers(self):
        for c in (self.path.stack,self.path.mar):
            self.assertTrue(all(r['characterized'] for r in c.loads() if not r['shared_data_bus']))
        for connector in ('J4','J5'):
            for bit in range(16):
                net=self.path.mar.nets[self.path.mar.nodes[connector,str(bit+3)]]
                receivers=[n for n in net['nodes'] if n[0].startswith('U')]
                self.assertEqual(len(receivers),1)
        from dm02.pc_hardware import Circuit as Pc
        from dm02.sequencer import Circuit as Seq
        rows=bus_load([('AL1',Alu()),('PC1',Pc()),('SQ1',Seq()),('RG1',Registers()),('SP1',self.path.stack),('MA1',self.path.mar)])['rows']
        self.assertEqual([r['input_cap_budget_pf'] for r in rows],[90]*4+[80]*4)
        self.assertTrue(all(len(r['drivers'])==13 for r in rows))


if __name__=='__main__':unittest.main()

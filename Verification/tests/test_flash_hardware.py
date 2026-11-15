from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.flash_hardware import Circuit,images,simulate,SOURCE,MPN
from dm02.alu_flash import Circuit as FlashAlu,budget as alu_budget,SOURCE as ALU_SOURCE
from dm02.alu_hardware import fixtures,simulate as fetched
from dm02.register_hardware import Circuit as Registers
from dm02.address_hardware import AddressPath
from dm02.memory_hardware import Circuit as Memory
from dm02.instruction_fixtures import generate
from dm02.electrical import audit
from designs.flash_candidate import drawing
from designs.alu_candidate import drawing as alu_drawing


class FlashHardware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-flash-');cls.folder=Path(cls.temp.name)
        cls.images=images(cls.folder/'images');fixtures(cls.folder/'fixtures');generate(cls.folder/'fixtures',quick=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def mutate(self,circuit,ref,pin,label):
        sheet=deepcopy(circuit.sheet)
        part=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        point=next(p for p in part['pins'] if p['number']==pin)
        labels=[l for l in sheet['labels'] if (l['x'],l['y'])==(point['x'],point['y'])]
        self.assertEqual(len(labels),1);labels[0]['name']=label;return type(circuit)(sheet)

    def test_array_images_routes_and_startup(self):
        c=Circuit();self.assertEqual(SOURCE.read_text(),drawing());self.assertEqual(audit(c.sheet)['findings'],[])
        self.assertTrue(all(r['characterized'] for r in c.loads()))
        self.assertEqual(self.images['words_verified'],2097152);self.assertEqual(len(self.images['images']),8)
        self.assertEqual({r['bytes'] for r in self.images['images']},{524288})
        raw=(self.folder/'images/alu-original.bin').read_bytes()
        for address in (0,1,0x7ffff,0x80000,0xfffff,0x100000,0x17ffff,0x180000,0x1fffff):
            bank=address>>19;offset=address&0x7ffff
            for lane,name in enumerate(('low','high')):
                self.assertEqual((self.folder/f'images/bank{bank}-{name}.bin').read_bytes()[offset],raw[2*address+lane])
        for corner in (0,1,2):
            r=simulate(c,self.folder/f'array{corner}',self.folder/'images',corner);self.assertTrue(r['passed'],r['log'])
        with self.assertRaises(ValueError):images(self.folder/'bad-images',b'\0\0')
        c.parts['devices'][MPN]['startup_ns']=0
        r=simulate(c,self.folder/'startup-bypass',self.folder/'images',1)
        self.assertFalse(r['passed']);self.assertIn('FR1 startup qualification bypassed',r['log'])

    def test_flash_pin_mutations(self):
        c=Circuit()
        for ref,pin,label,diagnostic in [('U1','12','FR_GROUP0_A1','FR1 read'),('U1','13','FR_BANK0_1','FR1 read'),
                ('U15','2','A20','FR1 read'),('U15','6','GND','FR1 read'),('U1','31','GND','FR1 write protection')]:
            with self.subTest(ref=ref,pin=pin):
                r=simulate(self.mutate(c,ref,pin,label),self.folder/f'fault-{ref}-{pin}',self.folder/'images')
                self.assertFalse(r['passed']);self.assertIn(diagnostic,r['log'])

    def test_flash_alu_and_startup_contract(self):
        c=FlashAlu();self.assertEqual(ALU_SOURCE.read_text(),alu_drawing(flash=True))
        self.assertEqual(audit(c.sheet)['findings'],[]);self.assertNotIn('M27C322-100F1',c.parts['devices'])
        self.assertTrue(all(r['characterized'] for r in c.loads() if not r['shared_data_bus']))
        self.assertTrue(all(r['margin_ns']>=0 for r in alu_budget(c)))
        for corner in (1,2):
            r=fetched(c,self.folder/f'alu{corner}',corner,self.folder/'fixtures',quick=True);self.assertTrue(r['passed'],r['log'])
        r=fetched(c,self.folder/'opcodes',1,self.folder/'fixtures',True,cases=True,
                  registers=Registers(),address_path=AddressPath(),memory=Memory())
        self.assertTrue(r['passed'],r['log'])
        r=fetched(c,self.folder/'early-reset',1,self.folder/'fixtures',quick=True,power_on_wait_ns=0)
        self.assertFalse(r['passed']);self.assertIn('AL2 flash startup reset contract',r['log'])
        c=self.mutate(c,'U11','3','ROM_D8')
        r=fetched(c,self.folder/'snapshot-bypass',0,self.folder/'fixtures',quick=True)
        self.assertFalse(r['passed']);self.assertIn('FATAL:',r['log']);self.assertNotIn('watchdog',r['log'])


if __name__=='__main__':unittest.main()

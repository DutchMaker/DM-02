from copy import deepcopy
import json
import unittest
from dm02.common import ROOT, VROOT
from dm02.legacy import read_sheet, library
from dm02.memory import Decoder, expected
from dm02.packages import allocate
from dm02.electrical import audit


class MemoryCircuit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet=read_sheet(ROOT/'Circuits/KiCad/Memory/Memory.sch')
        cls.decoder=Decoder(cls.sheet)

    def test_region_boundaries_and_external_bus_independence(self):
        for address in (0,0x3fff,0x4000,0x7fff,0x8000,0xfeff,0xff00,0xffff):
            for external in (0,0x4000,0xffff):
                for read,write in [(False,False),(True,False),(False,True)]:
                    for phase in (0,1):
                        self.assertEqual(self.decoder.evaluate(address,external,read,write,phase),expected(address,read,write,phase))

    def test_mar_load_gates(self):
        for controls in range(32):
            lo,hi,pc,stk,phase=((controls>>i)&1 for i in range(5))
            result=self.decoder.evaluate(0x1234,0xabcd,phase3=phase,load_low=lo,load_high=hi,pc_transfer=pc,stk_transfer=stk)
            self.assertEqual(result['low_load'],bool((lo or pc or stk) and not phase))
            self.assertEqual(result['high_load'],bool((hi or pc or stk) and not phase))

    def mutant_label(self,x,y,name):
        s=deepcopy(self.sheet)
        labels=[l for l in s['labels'] if (l['x'],l['y'])==(x,y)]
        self.assertEqual(len(labels),1); labels[0]['name']=name
        return Decoder(s)

    def test_original_address_decode_bug_is_detected(self):
        d=self.mutant_label(7050,7300,'A15')
        self.assertNotEqual(d.evaluate(0x8000,0,True),expected(0x8000,True,False,0))

    def test_original_direction_bug_is_detected(self):
        d=self.mutant_label(10000,1800,'~MEM_out')
        self.assertFalse(d.evaluate(0x4000,0,True)['memory_to_cpu'])

    def test_original_unprotected_ram_write_is_detected(self):
        d=self.mutant_label(8450,5000,'GND')
        self.assertTrue(d.evaluate(0xff00,0,write=True,phase2=1)['ram_writing'])

    def test_original_io_bus_driver_bug_is_detected(self):
        d=self.mutant_label(10000,1900,'MEM_idle')
        self.assertTrue(d.evaluate(0xff00,0,True)['memory_to_cpu'])

    def test_address_and_data_pin_swap_detection(self):
        for names in [('A0','A1'),('D0','D1')]:
            s=deepcopy(self.sheet); ram=next(c for c in s['components'] if c['stamp']=='5F5AEABC')
            a,b=[next(p for p in ram['pins'] if p['name']==n) for n in names]
            for axis in ('x','y'): a[axis],b[axis]=b[axis],a[axis]
            self.assertTrue(Decoder(s).routes()['errors'])

    def test_sram_supply_must_reach_connector_rail(self):
        s=deepcopy(self.sheet)
        s['labels']=[l for l in s['labels'] if not (l['name']=='5V' and (l['x'],l['y'])==(7750,3500))]
        self.assertTrue(any(r['kind']=='unconnected-supply' and r.get('pin')=='32' for r in audit(s)['findings']))

    def test_memory_supplies_and_spares_are_complete(self):
        self.assertEqual(audit(self.sheet)['findings'],[])
        for stamp in ('69171001','69171105'):
            s=deepcopy(self.sheet)
            c=next(c for c in s['components'] if c['stamp']==stamp)
            p=next(p for p in c['pins'] if p['kind'] in ('W','I'))
            s['labels']=[l for l in s['labels'] if (l['x'],l['y'])!=(p['x'],p['y'])]
            self.assertTrue(audit(s)['findings'])

    def test_supply_short_is_detected(self):
        s=deepcopy(self.sheet)
        s['labels'].append(dict(name='GND',x=13000,y=1100,implicit=False))
        self.assertTrue(any(r['kind']=='shorted-supply-rails' for r in audit(s)['findings']))

    def test_program_adapter_rom_protection_and_io_isolation(self):
        from dm02.programs import Machine
        m=Machine(bytes([0xc3,0,0]),self.decoder)
        m.put(0,0x55); self.assertEqual(m.get(0),0xc3)
        self.assertEqual(m.ignored_rom_writes,1)
        for address in (0x4000,0x7fff,0x8000,0xfeff):
            m.put(address,0x96); self.assertEqual(m.get(address),0x96)
        m.put(0xff00,ord('A'))
        self.assertEqual(bytes(m.text),b'A'); self.assertNotIn(0xff00,m.memory)

    def test_hc_receiver_regression_is_detected(self):
        s=read_sheet(ROOT/'Circuits/KiCad/Registers-StackPointer/Registers-StackPointer.sch')
        self.assertFalse(any(r['kind']=='ttl-to-hc' for r in audit(s)['findings']))
        next(c for c in s['components'] if c['ref']=='U10')['value']='74HC245'
        self.assertTrue(any(r['kind']=='ttl-to-hc' for r in audit(s)['findings']))


class PackageAllocation(unittest.TestCase):
    def setUp(self):
        self.sheet=read_sheet(ROOT/'Circuits/KiCad/Memory/Memory.sch')
        self.plan=json.loads((VROOT/'package-plan.json').read_text())['sheets']['Memory']

    def test_pack_unannotated_unit_one_gates_without_moving_nets(self):
        # Reconstruct anonymous unit-1 gates at the original endpoints, then
        # allocate the real units. Connectivity comparison uses stamp/endpoints.
        s=deepcopy(self.sheet)
        for i,c in enumerate(s['components']):
            if not c['ref'].startswith('U'): continue
            if all(p['kind']=='W' for p in c['pins']): continue
            ns,name=c['lib_id'].split(':'); definition=library(ns)[name]
            c.update(ref=f'U{9000+i}',original_ref='U?',unit=1)
            a,b,cc,d=c['matrix']
            c['pins']=[dict(p,x=c['x']+a*p['x']+b*p['y'],y=c['y']+cc*p['x']+d*p['y'])
                       for p in definition['pins'] if p['unit'] in (0,1) and p['convert'] in (0,c['convert'])]
        proposed,changes=allocate(s,self.plan)
        self.assertTrue(any(any(a!=b for a,b in r['pin_map'].items()) for r in changes))
        self.assertEqual(Decoder(proposed).evaluate(0x4000,0,True),expected(0x4000,True,False,0))

    def test_duplicate_gate_unit_rejected(self):
        self.plan[6]['instances'][1][1]=1
        with self.assertRaisesRegex(ValueError,'Duplicate instance or package unit'): allocate(self.sheet,self.plan)

    def test_power_unit_cannot_replace_logic_unit(self):
        self.plan[6]['instances'][0][1]=5
        with self.assertRaisesRegex(ValueError,'moves or changes pins'): allocate(self.sheet,self.plan)


if __name__=='__main__': unittest.main()

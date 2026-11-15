from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dm02.common import ROOT, BUILD
from dm02.legacy import read_sheet
from dm02.alu import expected
from dm02.alu_circuit import Datapath, simulate
from dm02.logisim_alu import trace
from dm02.electrical import audit


class AluDatapath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet=read_sheet(ROOT/'Circuits/KiCad/ALU/ALU.sch')
        BUILD.mkdir(parents=True,exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(prefix='alu-test-',dir=BUILD)
        cls.folder=Path(cls.temp.name)
        # Sparse oracle ROM keeps mutation tests independent of generated banks.
        rom=[];vectors=[]
        for op in range(32):
            for a in range(256):
                b=(a*73+op*19)&255; word=expected(op,a,b)
                rom.append(f'@{(op<<16)|(a<<8)|b:x} {word:04x}\n')
                vectors.append(f'{(op<<32)|(a<<24)|(b<<16)|word:010x}\n')
        (cls.folder/'rom.hex').write_text(''.join(rom))
        (cls.folder/'vectors.hex').write_text(''.join(vectors))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def change_label(self,x,y,value):
        sheet=deepcopy(self.sheet)
        found=[l for l in sheet['labels'] if (l['x'],l['y'])==(x,y)]
        self.assertEqual(len(found),1);found[0]['name']=value
        return Datapath(sheet)

    def rejected(self,circuit,message):
        self.assertTrue(circuit.routes()['errors'])
        ok,log=simulate(circuit,self.folder)
        self.assertFalse(ok,log);self.assertIn(message,log)

    def test_pin_derived_hdl_captures_and_releases(self):
        circuit=Datapath(self.sheet)
        self.assertEqual(circuit.routes()['errors'],[])
        ok,log=simulate(circuit,self.folder);self.assertTrue(ok,log)

    def test_original_operand_address_alias_is_detected(self):
        self.rejected(self.change_label(10750,5000,'A0'),'ROM address route/hold')

    def test_original_raw_stored_flag_alias_is_detected(self):
        self.rejected(self.change_label(12250,5000,'FLAGS0'),'flags changed during operand capture')

    def test_result_driver_direction_fault_is_detected(self):
        self.rejected(self.change_label(7850,8300,'GND'),'result bus')

    def test_physical_rom_address_pin_swap_is_detected(self):
        sheet=deepcopy(self.sheet);rom=next(c for c in sheet['components'] if c['ref']=='U3')
        a,b=[next(p for p in rom['pins'] if p['name']==name) for name in ('A0','A1')]
        for axis in ('x','y'): a[axis],b[axis]=b[axis],a[axis]
        self.rejected(Datapath(sheet),'ROM address route/hold')

    def test_flag_data_lane_swap_is_detected(self):
        self.rejected(self.change_label(6100,4400,'ALU_FLAGS2'),'ALU flag capture')

    def test_common_clock_and_complete_structural_wiring(self):
        self.assertEqual(audit(self.sheet)['findings'],[])
        circuit=Datapath(self.sheet)
        clocks=[circuit.pin(ref,'CP') for ref in ('U5','U6','U7')]
        clocks += [circuit.pin(ref,'C',unit) for ref in ('U1','U2') for unit in (1,2)]
        self.assertEqual(set(clocks),{circuit.labels['CLOCK_PH3']})

    def test_original_flag_selection_phase_is_detected(self):
        self.rejected(self.change_label(6100,5200,'~ALU_load'),'flags changed during operand capture')

    def test_register_enable_stuck_active_is_detected(self):
        self.rejected(self.change_label(1350,5800,'GND'),'ROM address route/hold')

    def test_missing_feedback_is_detected(self):
        self.rejected(self.change_label(10400,7650,'5V'),'flags changed during operand capture')

    def test_phase_qualifier_mutation_is_detected(self):
        sheet=deepcopy(self.sheet)
        # Replace the phase inverter with a buffer by changing its pin mapping
        # in the generated gate model via a source symbol-function mutation.
        component=next(c for c in sheet['components'] if c['stamp']=='69172104')
        component['lib_id']='74xx:74LS32'
        component['pins'].append(dict(next(p for p in component['pins'] if p['kind']=='I'),number='99'))
        ok,log=simulate(Datapath(sheet),self.folder)
        self.assertFalse(ok,log);self.assertIn('flag command outside phase',log)

    def test_logisim_reference_and_changed_flag_wire(self):
        result=trace();self.assertEqual(result['errors'],[])
        self.assertTrue(result['clock_hazard']['reproduced'])
        root=ET.parse(ROOT/'Logisim/DM-02.circ').getroot()
        circuit=root.find("circuit[@name='ALU']")
        wire=next(w for w in circuit.findall('wire') if w.get('from')=='(1000,200)' and w.get('to')=='(1040,200)')
        circuit.remove(wire)
        self.assertTrue(trace(root)['errors'])


class SupplyAndSpareRegression(unittest.TestCase):
    def test_supply_and_spare_units_across_affected_sheets(self):
        for name,power,spare in [('ALU','69172001','69172101'),
                                 ('Registers-StackPointer','69173001','69173101'),
                                 ('Power-Clock',None,'69174101')]:
            sheet=read_sheet(ROOT/f'Circuits/KiCad/{name}/{name}.sch')
            findings=audit(sheet)['findings']
            self.assertFalse([f for f in findings if f['kind'] in
                              ('missing-power-unit','unconnected-supply','unplaced-logic-unit','shorted-supply-rails')])
            if name!='ALU': self.assertEqual(findings,[])
            for stamp in (power,spare):
                if stamp is None: continue
                mutant=deepcopy(sheet)
                component=next(c for c in mutant['components'] if c['stamp']==stamp)
                pin=next(p for p in component['pins'] if p['kind']==('W' if stamp==power else 'I'))
                mutant['labels']=[l for l in mutant['labels'] if (l['x'],l['y'])!=(pin['x'],pin['y'])]
                self.assertGreater(len(audit(mutant)['findings']),len(findings))

    def test_removed_power_unit_is_detected(self):
        sheet=read_sheet(ROOT/'Circuits/KiCad/ALU/ALU.sch')
        sheet['components']=[c for c in sheet['components'] if c['stamp']!='69172001']
        self.assertTrue(any(f['kind']=='missing-power-unit' and f['ref']=='U1' for f in audit(sheet)['findings']))


if __name__=='__main__': unittest.main()

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02 import connector_plan as cn


class ConnectorPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = cn.native_boundary()
        cls.plan = cn.generate(cls.boundary)

    def test_native_partition_and_live_address_are_distinct(self):
        result = cn.validate(self.plan,self.boundary)
        self.assertEqual(result['contacts_checked'],1242)
        self.assertEqual(result['baseline_crossings'],dict(control=71,compute=57,counters=66,memory=92))
        eps = self.boundary['nets']['IO_ADDRESS0']
        self.assertTrue(any(e['board']=='ME1' and 'U15.2' in e['component_pins'] for e in eps))
        self.assertNotIn('U15.2',self.plan['extension_sources']['LIVE_ADDRESS0']['component_pins'])
        self.assertIn('DATA0',self.boundary['crossings']['compute'])
        self.assertIn('BRANCH0_0',self.boundary['crossings']['compute'])

    def test_omission_alias_and_duplicate_contact_fail(self):
        for mode in ('missing','alias','duplicate'):
            with self.subTest(mode=mode):
                plan = deepcopy(self.plan)
                pins = plan['cpu_cards'][1]['connectors'][0]['pins']
                if mode=='duplicate':
                    pins[1]['pin']=pins[0]['pin']
                else:
                    pin = next(p for p in pins if p['net']=='DATA0')
                    if mode=='missing': pin.update(kind='nc',net=None)
                    else: pin['net']='BRANCH0_0'
                with self.assertRaises(ValueError): cn.validate(plan,self.boundary)

    def test_supply_and_coding_collisions_fail(self):
        for contact in ('a1','b8','a2'):
            plan = deepcopy(self.plan)
            p = next(p for p in plan['cpu_cards'][0]['connectors'][0]['pins'] if p['pin']==contact)
            p.update(kind='signal',net='DATA0')
            with self.assertRaises(ValueError): cn.validate(plan,self.boundary)

    def test_private_return_cross_slot_short_fails(self):
        plan = deepcopy(self.plan)
        p = next(p for p in plan['peripheral_cards'][1]['connector']['pins'] if p['net']=='SLOT6_R_DATA0')
        p['net']='SLOT5_R_DATA0'
        with self.assertRaisesRegex(ValueError,'Private slot'): cn.validate(plan,self.boundary)

    def test_stale_write_address_substitution_fails(self):
        plan = deepcopy(self.plan)
        plan['extension_sources']['LIVE_ADDRESS0']['local_net']='IO_ADDR0'
        with self.assertRaisesRegex(ValueError,'extension source'): cn.validate(plan,self.boundary)

    def test_service_power_injection_and_missing_role_fail(self):
        plan = deepcopy(self.plan)
        plan['service'][0]['pins'][0].update(kind='power',net='5V')
        with self.assertRaises(ValueError): cn.validate(plan,self.boundary)
        plan = deepcopy(self.plan)
        plan['cpu_cards'].pop()
        with self.assertRaises(ValueError): cn.validate(plan,self.boundary)

    def test_planning_cannot_become_manufacturing_acceptance(self):
        for flag in ('physical_qualification','manufacturing_release'):
            plan=deepcopy(self.plan);plan[flag]=True
            with self.assertRaises(ValueError): cn.validate(plan,self.boundary)

    def test_published_study_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'manifest.json').write_text('{}')
            (root/'pin-plan.json').write_text('preserved publication')
            with self.assertRaisesRegex(ValueError,'Preserve published'): cn.evaluate(root)
            self.assertEqual((root/'pin-plan.json').read_text(),'preserved publication')


if __name__=='__main__':
    unittest.main()

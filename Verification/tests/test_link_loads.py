from copy import deepcopy
import json
import unittest
from dm02 import link_loads as ll,link_loads_evidence as evidence


class LinkLoadsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.inventory=ll.Inventory();cls.report=cls.inventory.generate()

    def test_complete_pin_and_contact_accounting(self):
        r=self.report
        self.assertEqual(len(r['pins']),7324)
        self.assertEqual(len(r['contacts']),864)
        self.assertEqual(sum(p['electrical_role']=='contact' for p in r['pins'].values()),2018)
        self.assertEqual(len(r['resistors']),40)
        self.assertEqual(sum(r['kind']=='series' for r in r['resistors']),1)
        self.assertEqual(len(r['hct245_directions']),19)
        self.assertTrue(all(r['direction']=='A-to-B' for r in r['hct245_directions']))

    def test_shared_sram_port_counted_once_and_driver_self_cap_excluded(self):
        row=next(n for n in self.report['nets'] if 'U9002.13' in n['pins'])
        self.assertEqual(len(row['scenarios']),2)
        for s in row['scenarios']:
            self.assertNotIn(s['driver'],s['load_pins'])
            self.assertEqual(len(s['load_pins']),2)
            self.assertEqual(s['ic_only_pf'],20)
        buffer=next(s for s in row['scenarios'] if s['driver']=='U9004.18')
        self.assertEqual(buffer['load_pins'].count('U9002.13'),1)
        self.assertFalse(self.report['pins']['U9002.13']['full_OC1_maximum'])

    def test_mar_extensions_and_oscillator_headroom(self):
        mar=[r for r in self.report['prior_comparisons'] if r['study']=='R2' and any('ME1:ADDRESS' in l for l in r['label'])]
        self.assertEqual(len(mar),16)
        self.assertTrue(all(len(r['additional_IC_pins'])==1 for r in mar))
        self.assertEqual(sorted(r['driver_loads'][0]['ic_only_pf'] for r in mar),[44]*14+[48]*2)
        for row in self.report['nets']:
            for s in row['scenarios']:
                if s['driver'].startswith('Y'):
                    self.assertEqual(s['ic_only_pf'],10)
                    self.assertEqual(s['screens'][0]['remaining_before_unknown_pf'],5)
                    self.assertIsNone(s['total_physical_load_pf'])

    def test_port_allocation_and_conditional_maxima_remain_distinct(self):
        p=self.report['pins']['U4005.2']
        self.assertTrue(p['receiver']);self.assertFalse(p['driver'])
        self.assertFalse(p['full_OC1_maximum'])
        self.assertEqual(p['capacitance_status'],'allocation-no-data-port-maximum')
        self.assertFalse(self.report['parts']['SN74AHCT244N']['input_full_OC1'])
        self.assertEqual(self.report['parts']['SN74AHCT244N']['output_typical_only_pf'],3)
        self.assertEqual(self.report['parts']['W27C512-45Z']['selected_fixtures'][0]['load_pf'],30)

    def test_omissions_and_alias_mutations_detected(self):
        mutations=ll.mutations(self.report)
        self.assertEqual(len(mutations),5)
        self.assertTrue(all(r['detected'] for r in mutations.values()))

    def test_duplicated_pin_cannot_hide_in_total(self):
        bad=deepcopy(self.report);row=next(r for r in bad['nets'] if r['scenarios'] and r['receiver_pins'])
        row['pins'].append(row['receiver_pins'][0])
        with self.assertRaisesRegex(ValueError,'duplicated inventory pins'):ll.validate_report(bad,self.report)

    def test_locked_replay(self):
        _,r=evidence.load();self.assertEqual(r,self.report)

    def test_missing_manufacturer_artifact_rejected(self):
        lock=json.loads(evidence.LOCK.read_text())
        del lock['artifacts']['cp1-link-loads/sources/manifest.json']
        with self.assertRaisesRegex(ValueError,'Missing LL1 artifact'):evidence.verify(lock)


if __name__=='__main__':unittest.main()

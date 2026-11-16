import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from dm02 import hct_preference as hp, hct_buffers as hb, hct_evidence as he
from dm02.common import BUILD


class HCTReviewTests(unittest.TestCase):
    def test_complete_native_review_with_conditions(self):
        r=hp.review()
        self.assertEqual(r['families'],dict(ACT=10,AHCT=117,AHC=9,HCT=126,memory=4,HC=6))
        self.assertEqual(len({p['reference'] for p in r['packages']}),142)
        self.assertEqual(r['parts']['244']['delay_ns'],42)
        self.assertEqual(r['parts']['244']['temperature_c'],[-55,125])
        self.assertEqual(r['parts']['244']['input_edge_ns'],6)
        self.assertIn('withheld',r['parts']['157']['timing_status'])
        self.assertEqual(r['parts']['377']['hold_ns'],3)
        self.assertEqual(r['parts']['377']['enable_hold_ns'],5)
        self.assertTrue(all(p['substitution_qualified'] is False for p in r['packages']))
        self.assertEqual({p['reference'] for p in r['packages'] if p['action']=='candidate-first'},set(hb.REFERENCES))

    def test_native_pin_direction_mutation_is_rejected(self):
        inventory=json.loads((BUILD/'cp1-mar-distribution/final/loads.json').read_text())
        inventory['pins']['U17001.2']['symbol_type']='output'
        with self.assertRaisesRegex(ValueError,'pin role mismatch'):hp.review(inventory=inventory)

    def test_only_two_package_values_change(self):
        old=hb.md.Candidate();new=hb.Candidate()
        self.assertEqual(old.groups,new.groups)
        changed={ref for ref,c in old.components.items() if c!=new.components[ref]}
        self.assertEqual(changed,set(hb.REFERENCES))
        for ref in changed:
            c=deepcopy(old.components[ref]);c['value']=hb.PART
            self.assertEqual(c,new.components[ref])
        self.assertEqual(hp.pin_roles('244'),{p['num']:p['type'] for p in new.components['U17001']['pin_signature']})

    def test_profile_extremes_and_sparse_arc_mutation(self):
        arcs=json.loads((BUILD/'cp1-mar-distribution/final/bindings.json').read_text())
        self.assertEqual(set(hb.delays(arcs,0).values()),{0})
        self.assertEqual(set(hb.delays(arcs,1).values()),{42})
        for bit in range(16):self.assertEqual(hb.delays(arcs,2)[bit]+hb.delays(arcs,3)[bit],42)
        with self.assertRaisesRegex(ValueError,'Incomplete'):hb.delays(arcs[:-1],1)
        with self.assertRaisesRegex(ValueError,'Unknown'):hb.delays(arcs,4)

    def test_model_uses_native_wiring_and_enable(self):
        arcs=json.loads((BUILD/'cp1-mar-distribution/final/bindings.json').read_text())
        original='\n'.join(f'assign n[{i+40}]=address[{i}];' for i in range(16))
        altered=deepcopy(arcs);altered[0]['source_bit']=1;altered[2]['enabled']=False
        model=hb.memory_model(original,altered,1)
        self.assertIn('assign #(42) n[40]=address[1];',model)
        self.assertIn("assign #(42) n[42]=1'bz;",model)
        with self.assertRaisesRegex(ValueError,'binding changed'):hb.memory_model(original.replace('address[15]','address[14]'),arcs,1)

    def test_lock_cannot_claim_physical_acceptance(self):
        with self.assertRaisesRegex(ValueError,'scope'):he.verify(dict(revision='CP1-HP1/HB1',physical_qualification=True))

    def test_locked_evidence_and_native_faults(self):
        lock,result=he.load()
        self.assertFalse(result['physical_qualification'])
        self.assertTrue(all(not r['passed'] for r in result['candidate']['native_faults'].values()))
        bad=deepcopy(lock);bad['artifacts'].pop('cp1-hct-preference/sources/sn74hct244.pdf')
        with self.assertRaisesRegex(ValueError,'Missing HCT artifact'):he.verify(bad)

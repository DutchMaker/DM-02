from copy import deepcopy
import json
import unittest
from dm02 import mar_distribution as md,mar_distribution_sim as sim,mar_distribution_evidence as evidence


class MarDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=md.Candidate();cls.native=md.STUDY/'final/native/MD1.xml'
        cls.bindings=cls.candidate.bindings(cls.native)

    def test_native_isolation_and_contracted_equivalence(self):
        r=self.candidate.compare(self.native)
        self.assertTrue(r['passed']);self.assertEqual(r['physical_pins'],7368)
        self.assertEqual(r['dip_count'],272);self.assertEqual(r['components'],610)
        self.assertEqual(len(self.bindings),16)
        self.assertTrue(all(p['bit']==p['source_bit'] and p['enabled'] for p in self.bindings))

    def test_bypass_and_disabled_buffer_cannot_hide_behind_contraction(self):
        for fault in ('buffer-bypass','disabled-buffer'):
            r=self.candidate.compare(md.STUDY/'final'/fault/'MD1.xml')
            self.assertFalse(r['passed']);self.assertTrue(r['unmated_differences'])
            self.assertFalse(r['contracted_CA1_differences'])

    def test_swapped_pin_mapping_is_observable_in_model(self):
        arcs=self.candidate.bindings(md.STUDY/'final/swapped-address/MD1.xml')
        self.assertEqual([p['source_bit'] for p in arcs[:2]],[1,0])
        original='\n'.join(f'assign n[{i+20}]=address[{i}];' for i in range(16))
        changed=sim.memory_model(original,arcs)
        self.assertIn('n[20]=address[1]',changed);self.assertIn('n[21]=address[0]',changed)

    def test_explicit_budget_covers_every_raw_and_buffered_path(self):
        r=md.LoadInventory(self.candidate,self.native).audit(self.candidate)
        self.assertEqual(len(r['mar_paths']),32);self.assertEqual(r['driver_scenarios'],1724)
        raw=[p for p in r['mar_paths'] if p['stage']=='raw'];out=[p for p in r['mar_paths'] if p['stage']=='buffered']
        self.assertEqual([p['ic_only_pf'] for p in raw],[30]*16)
        self.assertEqual([p['ic_only_pf'] for p in out],[24]*14+[28]*2)
        self.assertEqual(min(p['planning_margin_pf'] for p in raw),5)
        self.assertEqual(min(p['planning_margin_pf'] for p in out),7)
        self.assertTrue(all(p['total_physical_load_pf'] is None for p in r['mar_paths']))

    def test_partial_memory_binding_rejected(self):
        with self.assertRaisesRegex(ValueError,'ME1 address binding changed'):
            sim.memory_model('assign n[1]=address[0];',self.bindings)

    def test_locked_native_load_and_simulation_evidence(self):
        _,r=evidence.load();self.assertFalse(r['physical_qualification'])
        self.assertEqual(sum(v['passed'] for v in r['simulations']['results'].values()),5)

    def test_missing_boot_evidence_rejected(self):
        lock=json.loads(evidence.LOCK.read_text());del lock['artifacts']['cp1-mar-distribution/simulation-1/boot-mixed3/result.json']
        with self.assertRaisesRegex(ValueError,'Missing MD1 artifact'):evidence.verify(lock)

    def test_original_memory_fixture_dependencies_are_declared(self):
        lock=json.loads(evidence.LOCK.read_text())
        matrix=json.loads((md.STUDY/'simulation-1/matrix.json').read_text())
        for run in matrix['results'].values():
            self.assertTrue(set(run['input_hashes'])<=lock['artifacts'].keys())


if __name__=='__main__':unittest.main()

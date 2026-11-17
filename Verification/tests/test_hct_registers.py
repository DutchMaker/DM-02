import json
import unittest
from copy import deepcopy
from dm02 import hct_registers as hr, hct_register_evidence as he
from dm02.common import BUILD


class HCTRegisterTests(unittest.TestCase):
    def test_exact_six_package_delta(self):
        old=hr.hb.Candidate();new=hr.Candidate()
        self.assertEqual(old.groups,new.groups)
        changed={r for r in old.components if old.components[r]!=new.components[r]}
        self.assertEqual(changed,{'U5006','U5007','U6003','U6008','U6013','U6018'})
        for ref in changed:
            expected=deepcopy(old.components[ref]);expected['value']='CD74HCT377E'
            self.assertEqual(expected,new.components[ref])

    def test_binding_mutation_rejected_before_simulation(self):
        arcs=json.loads((BUILD/he.PREFIX/'bindings.json').read_text())
        text=(BUILD/'cp1-text-boot/guarded-max/AL1.sv').read_text()
        bad=deepcopy(arcs);bad[0]['arguments']=bad[0]['arguments'].replace('n[117]','n[118]')
        with self.assertRaisesRegex(ValueError,'binding differs'):hr.model_text(text,'AL1',bad,1)
        with self.assertRaisesRegex(ValueError,'Unknown HR1'):hr.model_text(text,'AL1',arcs,4)

    def test_monitor_poison_and_recovery(self):
        # Fresh Icarus run exercises recovery and rejection of reset release
        # without a clean capture, independent of archived result flags.
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            for case in ('reset-recovery','reset-no-recovery','disabled-data-hold'):
                result=hr.model_test(Path(tmp)/case,case)
                self.assertEqual(result['passed'],case=='reset-recovery')
                log=(Path(tmp)/case/'simulation.log').read_text()
                self.assertIn('PASS HR1 model' if case=='reset-recovery' else he.REASONS[case],log)

    def test_physical_scope_and_missing_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError,'scope'):he.verify(dict(revision='CP1-HR1',physical_qualification=True))
        lock=json.loads(he.LOCK.read_text());lock['artifacts'].pop(he.PREFIX+'path-review.json')
        with self.assertRaisesRegex(ValueError,'Missing HR1 artifact'):he.verify(lock)

    def test_full_locked_replay(self):
        _,result=he.load()
        self.assertFalse(result['physical_qualification'])
        self.assertEqual(result['loads']['families']['HCT'],134)
        self.assertGreaterEqual(result['sampled_minimum_reserve_ns']['data_setup'],10)

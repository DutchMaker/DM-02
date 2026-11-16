import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from dm02 import cp1
from dm02.common import digest
from dm02.reporting import freshness, milestones


class CP1AcceptanceTests(unittest.TestCase):
    def test_changed_or_missing_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = root/'simulation.log'
            p.write_text('DONE original\n')
            expected = {p.name:digest(p)}
            cp1.verify_hashes(root,expected)
            p.write_text('DONE altered\n')
            with self.assertRaisesRegex(ValueError,'changed locked'):
                cp1.verify_hashes(root,expected)
            p.unlink()
            with self.assertRaisesRegex(ValueError,'Missing'):
                cp1.verify_hashes(root,expected)

    def test_overlay_and_shared_input_changes_require_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root/'source'
            target = root/'target'
            source.mkdir()
            (target/'overlay').mkdir(parents=True)
            a = source/'oracle.py'
            b = target/'overlay/schematic.sch'
            a.write_text('original oracle')
            b.write_text('accepted circuit')
            lock = dict(sources={a.name:digest(a),b.name:digest(b)},overlay=[b.name])
            with patch.object(cp1,'ROOT',source),patch.object(cp1,'TARGET',target):
                cp1.materialize(lock,root/'output')
                for p in (a,b):
                    original = p.read_text()
                    p.write_text('changed')
                    with self.assertRaisesRegex(ValueError,'requires new verification'):
                        cp1.materialize(lock,root/'output')
                    p.write_text(original)

    def test_paths_cannot_escape_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'escapes'):
                cp1.checked_path(Path(temporary),'../outside')

    def test_changed_active_overlay_makes_report_stale(self):
        source = 'Verification/targets/cp1/overlay/schematic.sch'
        report = dict(state='complete',source_hashes={source:'original'})
        self.assertFalse(freshness(report,{source:'changed'})['fresh'])

    def test_gate_mapping_keeps_physical_requirements_open(self):
        lock = json.loads((cp1.TARGET/'lock.json').read_text())
        checks = cp1.checks_from_evidence(lock)
        requirements = json.loads((cp1.VROOT/'requirements.json').read_text())
        result = milestones(requirements,checks)
        self.assertEqual([m['passed'] for m in result],[3,3,8])
        by_id = {c['id']:c for c in checks}
        for id in ('bom','electrical-review','timing','physical-clock','module-timing','system','pcb','bench'):
            self.assertNotEqual(by_id[id]['status'],'pass')
        reference = json.loads((cp1.BUILD/lock['reference_report']).read_text())
        self.assertEqual({c['id'] for c in reference['checks'] if c['status']=='error'}, {'hardware-programs','boot'})

    def test_missing_lock_finishes_with_error_and_no_accepted_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(cp1,'BUILD',root),patch.object(cp1,'TARGET',root/'missing'),patch.object(cp1,'sources',return_value={'test':'fixed'}):
                status = cp1.run(SimpleNamespace(browser=False,allow_design_failures=True),
                                 lambda:dict(id='harness',status='pass'))
            report = json.loads((root/'report.json').read_text())
            self.assertEqual(status,2)
            self.assertEqual(report['state'],'complete')
            self.assertEqual(report['checks'][0]['status'],'error')
            self.assertTrue(all(m['passed']==0 for m in report['milestones']))


if __name__=='__main__':
    unittest.main()

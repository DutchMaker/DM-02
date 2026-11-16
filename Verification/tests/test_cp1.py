import json
import shutil
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

    def test_archive_selection_supports_legacy_and_rejects_escape(self):
        self.assertEqual(cp1.archive_root({}),(cp1.BUILD/'compact-design').resolve())
        self.assertEqual(cp1.archive_root({'evidence_directory':'revision-x'}),(cp1.BUILD/'revision-x').resolve())
        with self.assertRaisesRegex(ValueError,'escapes'):
            cp1.archive_root({'evidence_directory':'../outside'})

    def test_revision_evidence_routes_to_pinned_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'revision-x';archive.mkdir()
            part=archive/'part-qualification.json'
            part.write_text(json.dumps(dict(passed=True,missing_hold_monitor_mutation_detected=True)))
            ref=root/'reference/report.json';ref.parent.mkdir()
            ref.write_text(json.dumps(dict(checks=[dict(id=id,title=id,status='pass',artifacts=['method.json'])
                for id in ('pilot','mutations','analog','microcode','control-flow')])))
            key='revision-x/part-qualification.json'
            lock=dict(revision='CP1-R2',evidence_directory='revision-x',reference_report='reference/report.json',artifacts={key:digest(part)})
            with patch.object(cp1,'BUILD',root):
                checks={c['id']:c for c in cp1.checks_from_evidence(lock)}
                self.assertIn('revision-x/native-audit.json',checks['migration']['artifacts'])
                self.assertEqual(checks['component-specification']['status'],'pass')
                self.assertEqual(checks['timing']['status'],'blocked')
                self.assertEqual(checks['pilot']['artifacts'],['reference/method.json'])
                part.write_text(json.dumps(dict(passed=False,missing_hold_monitor_mutation_detected=True)))
                with self.assertRaisesRegex(ValueError,'changed locked input'):
                    cp1.checks_from_evidence(lock)
                lock['artifacts'][key]=digest(part)
                with self.assertRaisesRegex(ValueError,'qualification did not pass'):
                    cp1.checks_from_evidence(lock)
                lock['artifacts']={}
                with self.assertRaisesRegex(ValueError,'requires pinned'):
                    cp1.checks_from_evidence(lock)

    def test_missing_declared_artifact_withholds_control_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/'target';target.mkdir()
            archive=root/'revision-x';archive.mkdir()
            (archive/'physical-review.json').write_text('{"open_items":[]}')
            (target/'lock.json').write_text(json.dumps(dict(revision='CP1-R2',artifacts={},evidence_directory='revision-x',release='fixture',reference_report='reference.json')))
            names = list(cp1.operating_contract.load()['evidence']) + [
                'Verification/build/'+cp1.io_contract.NATIVE.format(board=b) for b in ('ME1','BP1')]
            for name in names:
                if name.startswith('Verification/build/'):
                    relative=name.removeprefix('Verification/build/');destination=root/relative
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(cp1.BUILD/relative,destination)
            (root/'cp1').mkdir();(root/'cp1/smoke.log').write_text('fixture smoke')
            checks=[dict(id='control',status='pass',artifacts=['missing.json']),dict(id='timing',status='blocked',artifacts=[])]
            with patch.object(cp1,'BUILD',root),patch.object(cp1,'TARGET',target),patch.object(cp1,'sources',return_value={'test':'fixed'}),patch.object(cp1,'validated_evidence',return_value={'passed':True}),patch.object(cp1,'checks_from_evidence',return_value=checks):
                status=cp1.run(SimpleNamespace(browser=False,allow_design_failures=True),lambda:dict(id='harness',status='pass'))
            report=json.loads((root/'report.json').read_text())
            self.assertEqual(status,2)
            self.assertEqual(next(c for c in report['checks'] if c['id']=='control')['requirement_status'],'blocked')

    def test_decision_evidence_changed_during_tests_withholds_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/'target';target.mkdir()
            archive=root/'revision-x';archive.mkdir()
            (archive/'physical-review.json').write_text('{"open_items":[]}')
            (target/'lock.json').write_text(json.dumps(dict(revision='CP1-R2',artifacts={},evidence_directory='revision-x',release='fixture',reference_report='reference.json')))
            contract=cp1.operating_contract.load()
            names = list(contract['evidence']) + [
                'Verification/build/'+cp1.io_contract.NATIVE.format(board=b) for b in ('ME1','BP1')]
            for name in names:
                if name.startswith('Verification/build/'):
                    relative=name.removeprefix('Verification/build/');destination=root/relative
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(cp1.BUILD/relative,destination)
            def harness():
                path=root/'cp1-readiness/study-validation.json'
                path.write_text(path.read_text()+' ')
                return dict(id='harness',status='pass')
            (root/'cp1').mkdir();(root/'cp1/smoke.log').write_text('fixture smoke')
            checks=[dict(id='control',status='pass',artifacts=[]),dict(id='timing',status='blocked',artifacts=[])]
            with patch.object(cp1,'BUILD',root),patch.object(cp1,'TARGET',target),patch.object(cp1,'sources',return_value={'test':'fixed'}),patch.object(cp1,'validated_evidence',return_value={'passed':True}),patch.object(cp1,'checks_from_evidence',return_value=checks):
                status=cp1.run(SimpleNamespace(browser=False,allow_design_failures=True),harness)
            report=json.loads((root/'report.json').read_text())
            self.assertEqual(status,2)
            self.assertEqual(next(c for c in report['checks'] if c['id']=='evidence-change')['status'],'error')
            self.assertEqual({c['id'] for c in report['checks'] if c['status']=='error'}, {'evidence-change'})
            self.assertEqual(next(c for c in report['checks'] if c['id']=='control')['requirement_status'],'blocked')


if __name__=='__main__':
    unittest.main()

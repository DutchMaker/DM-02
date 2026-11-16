from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from dm02 import io_bridge,io_bridge_boundary,io_bridge_evidence as replay
from designs import io_bridge_candidate as drawing


class BridgeCandidateTests(unittest.TestCase):
    def test_generated_sheets_and_library_match_sources(self):
        self.assertEqual(drawing.LIBRARY.read_text(),drawing.library_text())
        for factory in (drawing.qualifier,drawing.bridge):
            board=factory()
            self.assertEqual((drawing.DEST/(board.name+'.sch')).read_text(),board.finish())

    def test_native_pin_audit_and_candidate_evidence(self):
        lock,result=replay.load()
        boundary=json.loads((drawing.DEST/'boundary.json').read_text())
        circuit=io_bridge.Circuit(io_bridge.BUILD/'cp1-bridge/native',boundary)
        audit=circuit.audit()
        self.assertEqual(audit['dip_count'],41)
        self.assertEqual(audit['over_50pf'],[])
        self.assertTrue(all(r['status']=='pass' for r in result['native'].values()))
        self.assertFalse(result['integrated_into_R2'])

    def test_missing_required_evidence_is_rejected(self):
        lock=json.loads(replay.LOCK.read_text())
        del lock['artifacts']['cp1-bridge/profile-3/simulation.log']
        with self.assertRaisesRegex(ValueError,'Missing required'):replay.verify(lock)

    def test_missing_compiler_or_native_netlist_is_rejected(self):
        original=json.loads(replay.LOCK.read_text())
        for group,name in (('source_hashes','Verification/dm02/io_bridge.py'),
                           ('artifacts','cp1-bridge/native/MQ1/MQ1.xml')):
            lock=deepcopy(original);del lock[group][name]
            with self.assertRaisesRegex(ValueError,'Missing required'):replay.verify(lock)

    def test_reset_alias_and_private_return_swaps_are_rejected(self):
        boundary=json.loads((drawing.DEST/'boundary.json').read_text())
        circuit=io_bridge.Circuit(io_bridge.BUILD/'cp1-bridge/native',boundary)
        baseline=io_bridge_boundary.connector_plan.native_boundary()
        plan=io_bridge_boundary.connector_plan.generate(baseline)
        self.assertEqual(len(io_bridge_boundary.audit(circuit,baseline,plan)['memory_extensions']),17)
        altered=deepcopy(baseline)
        endpoint=next(e for e in altered['nets']['ME1_RESET_n'] if e['board']=='ME1')
        endpoint['local_net']='RESET_RELEASE_n'
        with self.assertRaises(ValueError):io_bridge_boundary.audit(circuit,altered,plan)
        altered=deepcopy(circuit)
        a=altered.labels['BR1','SLOT5_R_DATA0'];b=altered.labels['BR1','SLOT6_R_DATA0']
        altered.nets[a]['name'],altered.nets[b]['name']=altered.nets[b]['name'],altered.nets[a]['name']
        with self.assertRaisesRegex(ValueError,'Peripheral native'):io_bridge_boundary.audit(altered,baseline,plan)

    def test_changed_or_missing_artifact_is_rejected(self):
        lock=json.loads(replay.LOCK.read_text())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=next(iter(lock['artifacts']))
            p=root/first;p.parent.mkdir(parents=True);p.write_text('corrupted evidence')
            with self.assertRaisesRegex(ValueError,'Changed bridge'):replay.verify(lock,root)
            p.unlink()
            with self.assertRaisesRegex(ValueError,'Changed bridge'):replay.verify(lock,root)

    def test_uncharacterized_minima_and_physical_acceptance_stay_open(self):
        lock=json.loads(replay.LOCK.read_text())
        lock['physical_qualification']=True
        with self.assertRaises(ValueError):replay.verify(lock)
        parts=json.loads(io_bridge.PARTS.read_text())
        self.assertIn('zero',parts['minimum_delay_policy'])
        self.assertFalse(any('min_delay_ns' in p for p in parts['devices'].values()))


if __name__=='__main__':unittest.main()

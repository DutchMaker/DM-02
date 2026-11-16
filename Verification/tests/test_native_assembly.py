from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dm02 import native_assembly as na,native_assembly_evidence as evidence


class NativeAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.assembly=na.Assembly()

    def test_pinned_hierarchy_and_mutations(self):
        _,summary,binding=evidence.load()
        self.assertEqual(summary['native']['dip_count'],270)
        self.assertEqual(summary['native']['physical_pins'],6491)
        self.assertEqual(summary['native']['boundary_markers'],58)
        self.assertEqual(len(summary['mutations']),3)
        self.assertTrue(binding['reset_branches_distinct'])
        self.assertTrue(binding['read_write_addresses_distinct'])

    def test_original_library_collision_is_detected_despite_pin_parity(self):
        result=self.assembly.compare(na.STUDY/'iteration-1/native/NA1.xml')
        self.assertFalse(result['passed'])
        self.assertFalse(result['symbol_pin_metadata_match'])
        self.assertTrue(result['component_identity_match'])
        self.assertFalse(result['differences'])

    def test_pin_type_mutation_is_rejected_without_net_change(self):
        tree=ET.parse(na.STUDY/'final/native/NA1.xml')
        p=tree.find('./libparts/libpart/pins/pin');p.set('type','deliberately_invalid')
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'altered.xml';tree.write(path)
            result=self.assembly.compare(path)
        self.assertFalse(result['passed']);self.assertFalse(result['symbol_pin_metadata_match'])
        self.assertFalse(result['differences'])

    def test_boundary_marker_cannot_silently_become_fitted(self):
        tree=ET.parse(na.STUDY/'final/native/NA1.xml')
        marker=next(c for c in tree.findall('./components/comp') if c.find("property[@name='exclude_from_bom']") is not None)
        marker.remove(marker.find("property[@name='exclude_from_bom']"))
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'altered.xml';tree.write(path);result=self.assembly.compare(path)
        self.assertFalse(result['passed']);self.assertFalse(result['fitted_flags_match'])
        self.assertFalse(result['differences'])

    def test_omitted_mutation_evidence_is_rejected(self):
        lock=json.loads(evidence.LOCK.read_text())
        del lock['artifacts']['cp1-native-assembly/final/merged-reset/NA1.xml']
        with self.assertRaisesRegex(ValueError,'Missing NA1 artifact'):evidence.verify(lock)


if __name__=='__main__':unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dm02 import connector_assembly as ca,connector_assembly_evidence as evidence


class ConnectorAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.assembly=ca.Assembly()

    def test_pinned_isolated_cards_and_mated_functional_equivalence(self):
        _,summary=evidence.load();r=summary['native']
        self.assertEqual(r['components'],606);self.assertEqual(r['dip_count'],270)
        self.assertEqual(r['contact_pairs'],768);self.assertEqual(r['physical_contact_pins'],1536)
        self.assertEqual(r['removed_boundary_markers'],58)
        self.assertFalse(r['unmated_differences']);self.assertFalse(r['mated_functional_differences'])

    def test_global_label_bypass_is_rejected_even_with_correct_mated_graph(self):
        r=self.assembly.compare(ca.STUDY/'final/global-bypass/CA1.xml')
        self.assertFalse(r['passed']);self.assertTrue(r['unmated_differences'])
        self.assertFalse(r['mated_functional_differences'])

    def test_reversed_missing_and_aliased_contacts_break_functional_graph(self):
        for fault in ca.FAULTS[:-1]:
            with self.subTest(fault=fault):
                r=self.assembly.compare(ca.STUDY/'final'/fault/'CA1.xml')
                self.assertFalse(r['passed']);self.assertTrue(r['component_identity_match'])
                self.assertTrue(r['mated_functional_differences'])

    def test_correct_nets_cannot_hide_changed_connector_identity(self):
        tree=ET.parse(ca.STUDY/'final/native/CA1.xml')
        tree.find("./components/comp[@ref='J15001']/footprint").text='Connector_DIN:wrong_mating_part'
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'altered.xml';tree.write(path);r=self.assembly.compare(path)
        self.assertFalse(r['passed']);self.assertFalse(r['component_identity_match'])
        self.assertFalse(r['unmated_differences']);self.assertFalse(r['mated_functional_differences'])

    def test_omitted_bypass_evidence_is_rejected(self):
        lock=json.loads(evidence.LOCK.read_text())
        del lock['artifacts']['cp1-connector-assembly/final/global-bypass/CA1.xml']
        with self.assertRaisesRegex(ValueError,'Missing CA1 artifact'):evidence.verify(lock)


if __name__=='__main__':unittest.main()

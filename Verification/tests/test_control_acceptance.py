from copy import deepcopy
import unittest
from run import link_control_contract


class ControlAcceptance(unittest.TestCase):
    def setUp(self):
        self.checks=[dict(id='control',status='limited',artifacts=[]),
                     dict(id='alu-hardware',status='limited',functional_contract_passed=True),
                     dict(id='harness',status='pass')]

    def test_functional_acceptance_keeps_hardware_limited(self):
        link_control_contract(self.checks)
        self.assertEqual(self.checks[0]['requirement_status'],'pass')
        self.assertEqual(self.checks[0]['status'],'limited')
        self.assertEqual(self.checks[1]['status'],'limited')
        self.assertEqual(self.checks[0]['contract_validation']['evidence'],'alu-hardware')
        self.assertIn('alu-hardware/summary.json',self.checks[0]['artifacts'])

    def test_failed_or_incomplete_evidence_cannot_close_gate(self):
        for index,key,value in [(0,'status','fail'),(1,'status','fail'),(1,'functional_contract_passed',False),(2,'status','error')]:
            with self.subTest(index=index,key=key):
                checks=deepcopy(self.checks);checks[index][key]=value;link_control_contract(checks)
                self.assertNotIn('requirement_status',checks[0])
        self.checks.append(dict(id='source-change',status='error'))
        link_control_contract(self.checks);self.assertNotIn('requirement_status',self.checks[0])

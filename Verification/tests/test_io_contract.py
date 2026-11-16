from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from dm02 import io_contract as io


class IOContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = io.load()

    def initialized(self):
        model = io.Interface(self.contract)
        model.release_reset()
        model.initialize_text()
        return model

    def test_complete_address_space_and_transaction_scenarios(self):
        result = io.exercise(self.contract)
        self.assertTrue(result['passed'])
        self.assertEqual(result['full_address_reads'], 65536)
        self.assertEqual(result['io_write_cases'], 1024)

    def test_slow_serializer_repeated_polls_do_not_drop_or_duplicate_bytes(self):
        model = self.initialized()
        sent = bytes(range(256))
        received = []
        for value in sent:
            self.assertEqual(model.read(0xff03), 0x81)
            self.assertTrue(model.write(0xff00, value))
            for _ in range(17):
                self.assertEqual(model.read(0xff03), 0x80)
                self.assertEqual(model.pending, value)
            received.append(model.transmit())
            self.assertIsNone(model.transmit())
        self.assertEqual(bytes(received), sent)

    def test_credit_survives_other_endpoint_activity(self):
        model = io.Interface(self.contract)
        model.attach(0xff10, io.RegisterFixture())
        model.release_reset(); model.initialize_text()
        for value in range(256):
            model.write(0xff10, value)
            self.assertEqual(model.read(0xff10), value)
            self.assertEqual(model.read(0xff03), 0x81)
        self.assertTrue(model.write(0xff00, 0))
        self.assertEqual(model.transmit(), 0)

    def test_wrong_direction_and_non_io_access_have_no_side_effect(self):
        model = self.initialized()
        self.assertTrue(model.write(0xff00, 65))
        for address in (0, 0xfeff, 0xff01, 0xff02, 0xff03, 0xff05, 0xffff):
            self.assertFalse(model.write(address, 255))
        for address in (0xff00, 0xff04, 0xff01, 0xff02):
            self.assertEqual(model.read(address), 0)
        self.assertIsNone(model.read(0xfeff))
        self.assertEqual(model.pending, 65)
        self.assertFalse(model.overrun)

    def test_busy_error_clear_preserves_credit_and_data(self):
        model = self.initialized()
        model.write(0xff00, 1)
        self.assertFalse(model.write(0xff00, 2))
        model.write(0xff04, 0xfd)  # All bits except the documented W1C bit.
        self.assertEqual(model.read(0xff03), 0x82)
        model.write(0xff04, 2)
        self.assertEqual(model.read(0xff03), 0x80)
        self.assertEqual(model.transmit(), 1)
        self.assertEqual(model.read(0xff03), 0x81)

    def test_reset_masks_pending_and_requires_new_initialization(self):
        model = self.initialized()
        model.write(0xff00, 65)
        model.write(0xff00, 66)
        model.assert_reset()
        self.assertEqual(model.read(0xff03), 0)
        self.assertFalse(model.write(0xff00, 67))
        self.assertIsNone(model.transmit())
        with self.assertRaises(ValueError): model.initialize_text()
        model.release_reset()
        self.assertEqual(model.read(0xff03), 0x80)
        model.initialize_text()
        self.assertEqual(model.read(0xff03), 0x81)
        self.assertIsNone(model.pending)

    def test_reserved_duplicate_and_hotplug_allocations_rejected(self):
        model = io.Interface(self.contract)
        for address in (0xfeff, 0xff00, 0xff01, 0xff02, 0xff03, 0xff04, 0xff0f):
            with self.subTest(address=address), self.assertRaises(ValueError):
                model.attach(address, io.RegisterFixture())
        model.attach(0xff10, io.RegisterFixture())
        with self.assertRaisesRegex(ValueError, 'Duplicate'): model.attach(0xff10, io.RegisterFixture())
        model.release_reset()
        with self.assertRaisesRegex(ValueError, 'hot plug'): model.attach(0xff11, io.RegisterFixture())

    def test_contract_changes_cannot_silently_reuse_abi(self):
        mutations = [
            lambda c: c['addressing']['registers'][3].update(offset=1),
            lambda c: c['addressing']['registers'].pop(),
            lambda c: c['addressing'].update(io_base=0xfe00),
            lambda c: c['addressing'].update(expansion_offsets=[0,255]),
            lambda c: c['addressing'].update(unmapped_read_value=255),
            lambda c: c['text'].update(ready_mask=128),
            lambda c: c.update(physical_qualification=True),
        ]
        for mutate in mutations:
            changed = deepcopy(self.contract); mutate(changed)
            with self.assertRaises(ValueError): io.validate(changed)

    def test_boundary_uses_locked_native_connector_and_storage_pins(self):
        result = io.audit_boundary()
        self.assertTrue(result['passed'])
        self.assertTrue(result['write_address_is_registered'])
        self.assertFalse(result['existing_read_address'])
        self.assertFalse(result['existing_read_strobe'])
        self.assertIn(dict(board='ME1',ref='U15',pin='2',net='IO_ADDR0'), result['checked_pins'])

    def test_missing_changed_and_miswired_native_boundary_rejected(self):
        lock = json.loads(io.LOCK.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for board in ('ME1','BP1'):
                name = io.NATIVE.format(board=board)
                target = root/name; target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(io.BUILD/name, target)
            name = io.NATIVE.format(board='BP1'); target = root/name
            target.write_text(target.read_text().replace('/IO_ADDRESS0', '/WRONG_ADDRESS0'))
            with self.assertRaisesRegex(ValueError,'changed IO boundary'): io.audit_boundary(lock, root)
            # Even an independently updated hash cannot make a wrong pin map pass.
            lock['artifacts'][name] = io.digest(target)
            with self.assertRaisesRegex(ValueError,'connector boundary'): io.audit_boundary(lock, root)
            target.unlink()
            with self.assertRaisesRegex(ValueError,'Missing'): io.audit_boundary(lock, root)


if __name__ == '__main__':
    unittest.main()

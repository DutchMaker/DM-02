import unittest
import json
from dm02 import text_boot,text_boot_evidence


class TextBootTests(unittest.TestCase):
    def test_pinned_boot_matrix_and_mutations(self):
        _,matrix=text_boot_evidence.load()
        self.assertEqual(sum(r['passed'] for r in matrix['results'].values()),6)
        self.assertEqual(len(matrix['results']),9)

    def test_missing_mutation_evidence_is_rejected(self):
        lock=json.loads(text_boot_evidence.LOCK.read_text())
        del lock['artifacts']['cp1-text-boot/fault-skip-loader/simulation.log']
        with self.assertRaisesRegex(ValueError,'Missing TB1'):text_boot_evidence.verify(lock)

    def test_rom_loader_reconstructs_relocated_program_from_poison(self):
        images=[text_boot.image(s) for s in (0,0x5a,0xa5,0xff)]
        for data in images:
            proof=text_boot.oracle(data)
            self.assertTrue(proof['passed'])
            self.assertEqual(proof['writes'],len(data['payload']))
            self.assertEqual(proof['stack_pointer'],0xfef0)
            self.assertLess(len(data['loader']),0x4000)
            self.assertNotEqual(data['poison'][0x4000:0x4000+len(data['payload'])],data['payload'])
            for relocation in data['relocations']:
                self.assertGreaterEqual(relocation['target'],0x4000)
                self.assertLess(relocation['target'],0x4000+len(data['payload']))
        self.assertEqual(len({d['rom'] for d in images}),1)
        self.assertEqual(len({d['poison'] for d in images}),4)

    def test_architectural_oracle_rejects_actual_corrupt_rom(self):
        for index in (4,7):
            data=text_boot.image();rom=bytearray(data['rom']);rom[index]^=1;data['rom']=bytes(rom)
            with self.assertRaisesRegex(ValueError,'reconstruction'):text_boot.oracle(data)

    def test_memory_initialization_transform_is_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'anchor changed'):text_boot.models('missing','missing')
        data=text_boot.image()
        old=(text_boot.BUILD/'cp1-hct273/candidate/Verification/build/compact/c1-cases0/tb.sv').read_text()
        bench=text_boot.bench(old,len(data['payload']))
        self.assertNotIn('fixture_byte(',bench)
        self.assertNotIn('$readmemh("payload.hex",physical_memory',bench)
        self.assertIn('TB1 loader write data',bench)


if __name__=='__main__':unittest.main()

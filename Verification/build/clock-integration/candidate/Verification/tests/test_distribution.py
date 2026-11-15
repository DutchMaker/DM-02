import json
import tempfile
import unittest
from pathlib import Path
from designs.distribution_candidate import SOURCE,generate
from dm02.common import BUILD
from dm02.distribution_links import audit
from dm02.distribution_backplane import BACKPLANE,contract,drawing,compare,mutations
from dm02.distribution_timing import review,source_change_risks
from dm02.distribution import local_loads
from dm02.distribution_bench import bench
from dm02.distribution_hardware import load_boards,exported_hdl
from dm02.distribution_run import profile,receiver_results
from dm02.boot_hardware import memory_hdl,testbench,verify_log
from dm02.bootloader import fixtures
from dm02.legacy import read_sheet
from run import INTEGRATION_PREREQUISITES,integration_prerequisites


class DistributionTests(unittest.TestCase):
    def test_current_run_dependencies_fail_closed(self):
        for stage,dependencies in INTEGRATION_PREREQUISITES.items():
            checks=[dict(id=name,status='limited') for name in dependencies]
            integration_prerequisites(stage,set(dependencies),checks)
            for dependency in dependencies:
                with self.subTest(stage=stage,dependency=dependency):
                    with self.assertRaises(RuntimeError):integration_prerequisites(stage,set(dependencies)-{dependency},checks)
                    for status in ('blocked','fail','error'):
                        bad=[dict(c,status=status) if c['id']==dependency else c for c in checks]
                        with self.assertRaises(RuntimeError):integration_prerequisites(stage,set(dependencies),bad)
                    with self.assertRaises(RuntimeError):integration_prerequisites(stage,set(dependencies),[c for c in checks if c['id']!=dependency])

    def test_generated_pin_contract_and_backplane_faults(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as temporary:
            generated=generate(Path(temporary))
            self.assertEqual(len(generated),13)
            for path in generated.values():self.assertEqual(path.read_bytes(),(SOURCE/path.name).read_bytes())
        links=audit(SOURCE);self.assertTrue(links['passed']);self.assertEqual(len(links['rows']),324)
        self.assertEqual(max(r['cap_pf'] for r in links['rows']),50)
        loads=local_loads(SOURCE);self.assertTrue(loads['passed'])
        self.assertEqual(len(loads['unqualified']),8)
        self.assertEqual({r['board'] for r in loads['unqualified']},{'ME1'})
        self.assertTrue(all(r['retained_sram_gap'] for r in loads['unqualified']))
        spec=contract(SOURCE);self.assertEqual(BACKPLANE.read_text(),drawing(spec))
        sheet=read_sheet(BACKPLANE);self.assertTrue(compare(sheet,spec)['passed'])
        self.assertEqual(len(mutations(sheet,spec)),4)

    def test_interval_rejection_and_current_rom_hold_premise(self):
        result=review(SOURCE);self.assertTrue(result['passed'])
        fast,slow=result['results'];self.assertEqual(len(slow['paths']),46)
        self.assertFalse(fast['passed']);self.assertTrue(slow['passed'])
        self.assertEqual({p['path'] for p in fast['paths'] if not p['passed']},{
            'HALT reaches C1 request synchronizer before idle PH1',
            'PH2 early MA1 address through ROM to DF2 receiver setup',
            'PH2 early MA1 address through SRAM to DF2 receiver setup',
            'PH3 IO capture to PH0 external setup'})
        self.assertFalse(result['source_hold_contract']['risks'])
        for word in (0x8000|(11<<11)|(10<<7)|(5<<1),0x8000|(10<<11)|(8<<7)):
            self.assertTrue(source_change_risks([word])['risks'])

    def test_missing_opcode_and_boot_fixtures_are_rejected_before_compile(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as temporary:
            folder=Path(temporary);fixture=folder/'fixture';fixture.mkdir()
            for name in ('alu.bin','program.hex','expected.txt','io-expected.txt'):(fixture/name).touch()
            with self.assertRaisesRegex(ValueError,'cases.txt, instructions.txt'):
                profile(SOURCE,folder/'opcodes',fixture,cases=True)
            with self.assertRaisesRegex(ValueError,'boot-rom.hex'):
                profile(SOURCE,folder/'boot',fixture,demo=True,boot=True)
            self.assertFalse((folder/'opcodes').exists());self.assertFalse((folder/'boot').exists())

    def test_rom_loader_poison_and_hardware_completion_contract(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as temporary:
            folder=Path(temporary);coverage=fixtures(folder,seed=0x37)
            self.assertFalse(coverage['boot_injected']);self.assertEqual(coverage['microcycles'],558200)
            self.assertEqual(coverage['ram_writes'],24326);self.assertEqual(coverage['io_events'],0)
            self.assertEqual(coverage['image']['payload_bytes'],16542)
            self.assertEqual(coverage['boot']['final']['pc'],0x4000)
            rom=(folder/'boot-rom.hex').read_text().splitlines();ram=(folder/'sram-power-on.hex').read_text().splitlines()
            self.assertEqual(len(rom),65536);self.assertEqual(len(ram),131072);self.assertNotEqual(rom[0x4000],ram[0x4000])
            text=memory_hdl(exported_hdl(load_boards(SOURCE)['ME1'],1,'ME1'))
            self.assertNotIn('$readmemh("program.hex"',text)
            self.assertEqual(text.count('$readmemh("boot-rom.hex"'),1)
            self.assertEqual(text.count('$readmemh("sram-power-on.hex"'),1)
            self.assertIn('BL1 loader did not reach application entry',testbench(bench(),coverage))
            full=dict(coverage,full_demo=True)
            self.assertIn('BL1 boot verification missing',testbench(bench(),full))
            log='DONE BL1 payload_bytes=16542 writes=24326\nDONE hardware-demo cycles=558200 io=0\n'
            self.assertTrue(verify_log(log,coverage)['passed'])
            for old,new in [('16542','16541'),('24326','24325'),('558200','558199'),('io=0','io=1')]:
                self.assertFalse(verify_log(log.replace(old,new),coverage)['passed'])
            self.assertFalse(verify_log(log+log,coverage)['passed'])

    def test_receiver_evidence_requires_all_seven_guards(self):
        log='\n'.join(f'DF2 receiver sequencer_tb.guard_{name} captures=1 min_setup_ns=60.000000 min_hold_ns=40.000000'
                      for name in ('AL1','PC1','SQ1','RG1','SP1','MA1','ME1'))
        self.assertTrue(receiver_results(log,require_captures=True)['passed'])
        for bad in (log.replace('guard_ME1','guard_AL1'),log.replace('60.000000','39.000000'),
                    log.replace('40.000000','24.000000'),log.replace('captures=1','captures=0')):
            self.assertFalse(receiver_results(bad,require_captures=True)['passed'])

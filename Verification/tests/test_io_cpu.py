from pathlib import Path
import json
import tempfile
import unittest
from dm02 import io_cpu,io_cpu_evidence


class CPUBridgeTests(unittest.TestCase):
    def test_pinned_matrix_replays_with_expected_negative_controls(self):
        _,matrix=io_cpu_evidence.load()
        self.assertEqual(sum(r['passed'] for r in matrix['results'].values()),29)
        self.assertEqual({n for n,r in matrix['results'].items() if not r['passed']},io_cpu_evidence.NEGATIVE)
        self.assertFalse(matrix['promoted_into_R2'])

    def test_missing_profile_or_source_cannot_be_accepted(self):
        for key,name in (('artifacts','cp1-io-cpu/profiles/fault-stale-read-address/simulation.log'),
                         ('source_hashes','Verification/hdl/io_cpu_probe.sv')):
            lock=json.loads(io_cpu_evidence.LOCK.read_text());del lock[key][name]
            with self.assertRaisesRegex(ValueError,'Missing CPU bridge'):io_cpu_evidence.verify(lock)

    def test_program_executes_direct_io_in_architectural_oracle(self):
        from dm02.control import State,instruction
        from dm02.microcode import reference
        spec=reference((io_cpu.ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
        class Fixture(State):
            def get(self,address):
                if address<0xff00:return super().get(address)
                return 0x81 if address==0xff03 else self.values.get(address,0)
            def put(self,address,value):
                if address==0xff00:self.echoes.append(value)
                elif address in (0xff10,0xff20,0xff30):self.values[address]=value
                elif address<0xff00:super().put(address,value)
        image,expected,_=io_cpu.diagnostic()
        state=Fixture(pc=0);state.memory=dict(enumerate(image));state.values={};state.echoes=[]
        for _ in range(100):
            op=state.get(state.pc);state.pc+=1
            instruction(spec[op]['name'],spec[op]['size'],state)
            if state.halted:break
        self.assertTrue(state.halted)
        self.assertEqual(bytes(state.echoes),expected)

    def test_diagnostic_has_literal_full_and_absent_slot_oracles(self):
        image,expected,size=io_cpu.diagnostic(0)
        self.assertEqual(expected,bytes.fromhex('81 a5 5a 96 00 3c 00 69 c3 3c 81 00 3c 00'))
        self.assertEqual(image[0xfe03],0x3c)
        self.assertEqual(image[size-1],0xe2)
        _,absent,_=io_cpu.diagnostic(15)
        self.assertEqual(absent,bytes.fromhex('00 00 00 00 00 3c 00 00 00 00 00 00 3c 00'))

    def test_composition_preserves_physical_cpu_and_reset_branches(self):
        original=(io_cpu.BUILD/'cp1-hct273/candidate/Verification/build/compact/c1-cases0/tb.sv').read_text()
        bench=io_cpu.compose_bench(original)
        self.assertIn('memory(ME1_PH0,ME1_PH2,ME1_PH3,ME1_RESET_n,mem_n,load_n[10],mar,data_bus,bridge_result',bench)
        self.assertIn('bridge(mar,mem_n,load_n[10],reset_n,ME1_RESET_n',bench)
        self.assertIn('CP1 physical source contention',bench)
        self.assertNotIn('fixture_byte(',bench)
        self.assertNotIn('always @(posedge phase[3]) if(reset_n && valid)',bench)
        with self.assertRaisesRegex(ValueError,'return binding'):
            io_cpu.compose_bench(original.replace("mar,data_bus,8'b0",'mar,data_bus,other_return'))
        with self.assertRaisesRegex(ValueError,'prefix'):
            io_cpu.compose_bench(original.replace('reg [7:0] peripheral_data;','reg [7:0] changed;'))

    def test_existing_run_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'simulation.log').write_text('preserve failed evidence')
            with self.assertRaisesRegex(ValueError,'Preserve existing'):io_cpu.profile(root)
            self.assertEqual((root/'simulation.log').read_text(),'preserve failed evidence')


if __name__=='__main__':unittest.main()

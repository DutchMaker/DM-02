import unittest
import xml.etree.ElementTree as ET
from dm02.common import ROOT
from dm02.logisim_pc import Nibble, ProgramCounter
from dm02.control import State, instruction


class PcCircuit(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.pc=ProgramCounter()

    def test_parallel_load_wins_locally_but_carry_reaches_other_byte(self):
        self.assertEqual(self.pc.step(0x45fe,0x67,1,load_low=True),0x4567)
        self.assertEqual(self.pc.step(0x45ff,0x67,1,load_low=True),0x4667)
        self.assertEqual(self.pc.step(0x45ff,0x67,0,load_low=True),0x4567)
        self.assertEqual(self.pc.step(0xffff,0,1),0)
        self.assertEqual(self.pc.step(0xffff,0x67,1,load_low=True,load_high=True),0x6767)

    def test_reset_priority(self):
        self.assertEqual(self.pc.step(0xffff,0xff,1,True,True,True),0)

    def test_extracted_xor_gate_mutation_changes_result(self):
        root=ET.parse(ROOT/'Logisim/DM-02.circ').getroot()
        gate=root.find("circuit[@name='74161-Bus']/comp[@name='XOR Gate']")
        # OR has a different input offset; increase size to keep the same
        # input pins while mutating the logic function.
        gate.set('name','OR Gate')
        gate.find("a[@name='size']").set('val','40')
        mutated=Nibble(root)
        mismatches=sum(mutated.evaluate(q,0,1,1,1)[0]!=((q+1)&15) for q in range(16))
        self.assertGreater(mismatches,0)

    def test_documented_mov_scratch_preserves_store_source(self):
        state=State(); state.memory.update({state.pc:0x41,state.pc+1:0xff})
        original=state.pair('HL'); instruction('MOV address,HL',3,state)
        self.assertEqual(state.pair('BC'),0x41ff)
        self.assertEqual(state.pair('HL'),original)
        self.assertEqual(state.word(0x41ff),original)

    def test_documented_indirect_arithmetic_scratch(self):
        state=State(); state.memory.update({state.pc:0x42,state.pc+1:0,0x4200:0x56,0x4201:0x78,0x5678:1})
        instruction('ADD (address)',3,state)
        self.assertEqual(state.pair('HL'),0x5678)
        self.assertEqual(state.r['A'],0x80)


if __name__=='__main__': unittest.main()

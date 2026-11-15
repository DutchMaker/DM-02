from copy import deepcopy
import unittest
from dm02.control import State, execute, instruction, differences
from dm02.microcode import reference
from dm02.common import ROOT


def rom(*states):
    words=[0]*65536
    for t,word in enumerate(states):
        words[t*16:(t+1)*16]=[word]*16
    return words


class ControlExecution(unittest.TestCase):
    def test_wrong_bus_source_is_detected(self):
        initial=State(); want=deepcopy(initial)
        instruction('MOV A,B',1,want)
        for word,good in [(0x9080,True),(0x9880,False)]:
            actual=deepcopy(initial)
            execute(rom(word,0x0800),{},0,actual)
            self.assertEqual(not differences(actual,want),good)

    def test_live_flags_select_next_word_but_not_current_word(self):
        words=rom(0x9354,0xb080,0x0800)  # ADC B result, then ALU -> A.
        words[17]=0xb100  # C=1 on next word routes ALU to B instead.
        for capture,expected_reg in [('load','A'),('output','B')]:
            state=State(flags=1); state.r.update(A=1,B=2)
            trace=execute(words,{(10<<16)|(1<<8)|2:4},0,state,flag_capture=capture)
            self.assertEqual(state.r[expected_reg],4)
            self.assertEqual(trace[1]['address'],'0010' if capture=='load' else '0011')

    def test_counter_transfer_samples_before_increment(self):
        # PC_MAR_transfer + PC_inc; MEM -> A; reset.
        for phase in ('before','after'):
            state=State(pc=0xffff); state.memory.update({0xffff:0xa5,0:0x5a})
            execute(rom(0x300a,0xd080,0x0800),{},0,state,phase)
            self.assertEqual((state.pc,state.r['A']),(0,0xa5))

    def test_pc_load_increment_phase_sensitivity(self):
        for phase,want in [('before',0x4667),('after',0x4568)]:
            state=State(pc=0x45ff); state.r['L']=0x67
            execute(rom(0xae0a,0x0800),{},0,state,phase)
            self.assertEqual(state.pc,want)

    def test_undriven_bus_and_unterminated_opcode_fail_closed(self):
        for words,message in [(rom(0x8080),'undriven'),(rom(),'terminate')]:
            with self.assertRaisesRegex(ValueError,message): execute(words,{},0,State())

    def test_extra_write_of_same_value_is_detected(self):
        want=State(); actual=deepcopy(want)
        actual.put(0x5678,actual.get(0x5678))
        self.assertIn('memory',differences(actual,want))

    def test_not_named_destination_contract(self):
        state=State(); state.r.update(A=0x17,B=0xff)
        mask=instruction('NOT B',1,state)
        self.assertEqual((state.r['A'],state.r['B'],state.f&mask),(0x17,0,4))

    def test_call_ret_pair_uses_operand_pc_stack_abi(self):
        spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
        for pc in (0,0x12ff,0xffff):
            state=State(pc=pc,sp=0x9000)
            state.memory.update({pc:0x45,(pc+1)&65535:0x67})
            execute(spec['words'],{},0xcc,state)
            self.assertEqual(state.pc,0x4567)
            self.assertEqual((state.get(0x9000),state.get(0x8fff)),(pc>>8,pc&255))
            execute(spec['words'],{},0xd5,state)
            self.assertEqual((state.pc,state.sp),((pc+2)&65535,0x9000))

    def test_packed_flags_discard_unwired_high_nibble(self):
        spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
        for byte in range(256):
            state=State(sp=0x8fff);state.memory[0x9000]=byte
            execute(spec['words'],{},0x52,state)  # POP F
            self.assertEqual(state.f,byte&15)
            execute(spec['words'],{},0x4a,state)  # PUSH F
            self.assertEqual(state.get(0x9000),byte&15)

    def test_rom_divide_by_zero_bit_is_not_a_stored_flag(self):
        # B -> ALU(DIV), then ALU -> A, then finish.
        words=rom(0x8000|(2<<11)|(6<<7)|64|(18<<1),0xb080,0x0800)
        for capture in ('load','output'):
            state=State();state.r.update(A=7,B=0)
            execute(words,{(18<<16)|(7<<8):0x1400},0,state,flag_capture=capture)
            self.assertEqual(state.f,4)


if __name__=='__main__': unittest.main()

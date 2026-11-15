import json
import struct
import tempfile
import unittest
from pathlib import Path
from dm02.common import ROOT, BUILD, command
from dm02.microcode import reference, encode


def source(body,header='NOP'):
    return f'''.operands
0001:A
0010:B
0110:ALU
.end
.functions
0001:TSTATE_reset
0010:CLOCK_halt
0101:PC_inc
.end
.alu
00000:ZERO
01001:A+B
.end
.instructions
00:1:NOP
.end
.code
{header}
{body}
.end
.end
'''


class CompilerRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True,exist_ok=True)
        code,log=command(['dotnet','build',ROOT/'Code/Microcode/src/Mcc/Mcc.csproj','--no-restore'])
        if code: raise RuntimeError(log)
        cls.dll=ROOT/'Code/Microcode/src/Mcc/bin/Debug/netcoreapp2.2/mcc.dll'

    def compile_fixture(self,text):
        directory=tempfile.TemporaryDirectory(prefix='compiler.fixture.',dir=BUILD)
        self.addCleanup(directory.cleanup)
        path=Path(directory.name)/'input.fixture.src'; path.write_text(text)
        code,log=command(['dotnet','--roll-forward','Major',self.dll,path],timeout=15)
        return code,log,path

    def test_complete_rom_and_independent_encoding(self):
        text=source(': [data][A+B]\n A_out\n ALU_load\n: TSTATE_reset')
        code,log,path=self.compile_fixture(text)
        self.assertEqual(code,0,log)
        raw=path.with_suffix('.rom').read_bytes()
        words=struct.unpack('<65536H',raw)
        self.assertEqual(words[:16],(0x8b52,)*16)
        self.assertEqual(words[16:32],(0x0800,)*16)
        self.assertEqual(words[32:],(0,)*(65536-32))
        image=[int(t,16) for t in path.with_suffix('.img').read_text().split()[2:]]
        self.assertEqual(list(words),image)
        self.assertEqual(list(words),reference(text)['words'])

    def test_final_comment_without_newline(self):
        code,log,path=self.compile_fixture(source(': TSTATE_reset').rstrip()+'\n# EOF comment')
        self.assertEqual(code,0,log)
        self.assertEqual(path.with_suffix('.rom').stat().st_size,131072)

    def test_unencodable_controls_are_rejected(self):
        cases=[
            (': [data][typo]\n A_out\n ALU_load','Unknown ALU'),
            (': [data][A+B]\n A_out\n ALU_load\n PC_inc','Too many function'),
            (': [data]\n A_out\n B_load\n PC_inc\n TSTATE_reset','Too many function'),
            (': PC_inc\n TSTATE_reset\n CLOCK_halt','Too many function'),
            (': [data]\n A_out\n B_out','Multiple operand outputs'),
            (': [data]\n A_load\n B_load','Multiple operand loads'),
            (': A_out\n B_load','requires a data'),
            (': PC_inc\n PC_inc','Duplicate function'),
            ('\n'.join(': PC_inc' for _ in range(17)),'Maximum number'),
        ]
        for body,reason in cases:
            with self.subTest(reason=reason,body=body):
                code,log,path=self.compile_fixture(source(body))
                self.assertNotEqual(code,0)
                self.assertIn(reason,log)
                self.assertFalse(path.with_suffix('.rom').exists())

    def test_flag_conditions_fail_closed(self):
        for condition,reason in [('[C=2]','Unknown flag'),('[C=0]','Missing microcode')]:
            code,log,path=self.compile_fixture(source(': TSTATE_reset','NOP '+condition))
            self.assertNotEqual(code,0)
            self.assertIn(reason,log)

    def test_encoding_width_rejected(self):
        text=source(': TSTATE_reset').replace('0001:A','00001:A')
        code,log,path=self.compile_fixture(text)
        self.assertNotEqual(code,0)
        self.assertIn('Invalid 4-bit encoding',log)

    def test_overlapping_definitions_rejected(self):
        text=source(': TSTATE_reset').replace('.code\n','.code\nNOP\n: PC_inc\n.end\n')
        code,log,path=self.compile_fixture(text)
        self.assertNotEqual(code,0)
        self.assertIn('Overlapping microcode address',log)

    def test_usage_and_missing_source_are_nonzero(self):
        for args in ([],[BUILD/'missing-fixture.src']):
            code,log=command(['dotnet','--roll-forward','Major',self.dll,*args])
            self.assertEqual(code,2,log)


if __name__=='__main__': unittest.main()

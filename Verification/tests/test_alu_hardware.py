from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from dm02.alu_hardware import Circuit,fixtures,simulate,budget
from dm02.instruction_fixtures import generate
from dm02.common import VROOT,command
from dm02.electrical import audit
from designs.alu_candidate import drawing,DEST


class TimedAlu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-al1-');cls.folder=Path(cls.temp.name)
        fixtures(cls.folder/'fixtures');generate(cls.folder/'fixtures',quick=True);cls.circuit=Circuit()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def pin_label(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        c=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in c['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1);at[0]['name']=label;return Circuit(sheet)

    def test_staged_result_sync_flags_and_fetched_execution(self):
        for connected,cases in [(False,False),(True,False),(True,True)]:
            with self.subTest(connected=connected,cases=cases):
                r=simulate(self.circuit,self.folder/f'good-{connected}-{cases}',1,self.folder/'fixtures',connected,quick=True,cases=cases)
                self.assertTrue(r['passed'],r['log'])
        self.assertEqual(audit(self.circuit.sheet)['findings'],[])
        self.assertEqual(DEST.read_text(),drawing())
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.circuit)))

    def test_pin_faults_and_snapshot_bypass_are_detected(self):
        cases=[('snapshot clock','U8','11','OPERAND_CLOCK'),
               ('flag snapshot bypass','U11','3','ROM_D8'),
               ('A hold feedback','U5','5','GND'),
               ('operand address bit','U1','10','B1'),
               ('ALU function pin','U7','3','FUNCTION1'),
               ('flag ordering','U11','3','RESULT9'),
               ('F upper byte zero','U15','17','5V'),
               ('result bus enable','U14','1','GND'),
               ('A reset missing','U2','1','5V')]
        for i,(name,ref,pin,label) in enumerate(cases):
            with self.subTest(name=name):
                r=simulate(self.pin_label(ref,pin,label),self.folder/f'fault{i}',0,self.folder/'fixtures',quick=True)
                self.assertFalse(r['passed'],r['log']);self.assertIn('FATAL:',r['log']);self.assertNotIn('watchdog',r['log'])

    def test_bus_load_finding_is_preserved(self):
        rows=self.circuit.loads();bus=[r for r in rows if r['shared_data_bus']]
        self.assertEqual(len(bus),8);self.assertEqual({r['cap_pf'] for r in bus},{75,85})
        self.assertTrue(all(not r['characterized'] for r in bus))
        self.assertTrue(all(r['characterized'] for r in rows if not r['shared_data_bus']))
        self.assertIn('Obsolete',self.circuit.parts['devices']['M27C322-100F1']['status'])

    def test_operand_timing_faults_have_specific_diagnostics(self):
        prefix='''`timescale 1ns/1ps
module timing;
reg [7:0] d=0;reg clk=0,enable_n=0,reset_n=0;wire [7:0] q;
al1_377 dut(d,clk,enable_n,q,reset_n);
initial begin #100;reset_n=1;#100;
'''
        stimuli={'data setup':'d=1;#1;clk=1;', 'data hold':'clk=1;#1;d=1;',
                 'enable setup':'enable_n=1;#1;clk=1;', 'enable hold':'clk=1;#1;enable_n=1;',
                 'high pulse':'clk=1;#1;clk=0;', 'low pulse':'clk=1;#40;clk=0;#1;clk=1;'}
        for reason,stimulus in stimuli.items():
            with self.subTest(reason=reason):
                src=self.folder/'timing.sv';src.write_text(prefix+stimulus+'#100;$display("MISSED");$finish;end endmodule\n')
                code,log=command(['iverilog','-g2012','-s','timing','-o',self.folder/'timing.vvp',src,VROOT/'hdl/alu_devices.sv'])
                self.assertEqual(code,0,log);code,log=command(['vvp',self.folder/'timing.vvp'])
                self.assertNotEqual(code,0,log);self.assertIn('AL1 operand '+reason,log)

    def test_timeout_keeps_diagnostics(self):
        err=subprocess.TimeoutExpired(['vvp','alu.vvp'],180,output=b'AL1 partial diagnostic\n')
        with patch('dm02.alu_hardware.command',side_effect=[(0,''),err]):
            with self.assertRaises(subprocess.TimeoutExpired):
                simulate(self.circuit,self.folder/'timeout',fixtures=self.folder/'fixtures',quick=True)
        self.assertIn('AL1 partial diagnostic',(self.folder/'timeout/alu.log').read_text())


if __name__=='__main__':unittest.main()

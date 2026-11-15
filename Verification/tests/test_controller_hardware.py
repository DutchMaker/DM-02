from copy import deepcopy
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from dm02.common import VROOT,command
from dm02.controller_hardware import Circuit,simulate,budget
from dm02.electrical import audit


class ControlWord(unittest.TestCase):
    def setUp(self):
        self.circuit=Circuit()
        self.temp=tempfile.TemporaryDirectory(prefix='dm02-controller-')
        self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)

    def pin_label(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        c=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in c['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1);at[0]['name']=label
        return Circuit(sheet)

    def test_max_delay_decode_blank_reset_and_latched_address(self):
        r=simulate(self.circuit,self.folder,1,quick=True)
        self.assertTrue(r['passed'],r['log'])
        self.assertEqual(audit(self.circuit.sheet)['findings'],[])
        self.assertTrue(all(r['within_allocated_test_load'] for r in self.circuit.loads()))
        self.assertTrue(all(r['margin_ns']>=0 for r in budget(self.circuit)))

    def test_pin_faults_are_observed(self):
        cases=[('latch phase','U3','11','CLOCK_PH2','CW word'),
               ('live flag address','U1','10','GND','CW capture word'),
               ('ROM byte lane','U3','3','ROM_D9','CW capture word'),
               ('load selector','U6','23','WORD8','CW decode'),
               ('function suppression','U8','19','WORD15','CW decode'),
               ('function merge','U14','1','FA4_n','CW decode'),
               ('phase blank bypass','U11','5','5V','CW outputs not inhibited'),
               ('valid reset bypass','U10','1','5V','CW reset validity'),
               ('ROM output enable','U1','22','5V','CW capture word')]
        for name,ref,pin,label,message in cases:
            with self.subTest(name=name):
                r=simulate(self.pin_label(ref,pin,label),self.folder,0,quick=True)
                self.assertFalse(r['passed'],r['log']);self.assertIn(message,r['log'])

    def test_load_and_address_window_constraints_are_enforced(self):
        self.circuit.parts['constraints']['connector_load_pf']=100
        self.assertFalse(all(r['within_allocated_test_load'] for r in self.circuit.loads()))
        self.circuit.parts['constraints']['rom_address_setup_ns']=80
        self.circuit.parts['constraints']['rom_address_hold_ns']=10
        failing=[r['path'] for r in budget(self.circuit) if r['margin_ns']<0]
        self.assertIn('ROM address setup contract',failing)
        self.assertIn('ROM address hold with zero contamination delay',failing)

    def test_latch_timing_faults_have_specific_diagnostics(self):
        prefix='''`timescale 1ns/1ps
module timing;
 reg [7:0] d=0;reg clk=0,reset_n=0;wire [7:0] q;
 cw574 dut(d,clk,1'b0,q,reset_n);
 initial begin #100;reset_n=1;#100;
'''
        for reason,stimulus in {
            'data setup':'d=1;#1;clk=1;',
            'data hold':'clk=1;#1;d=1;',
            'high pulse':'clk=1;#1;clk=0;',
            'low pulse':'clk=1;#30;clk=0;#1;clk=1;'}.items():
            with self.subTest(reason=reason):
                source=self.folder/'timing.sv';source.write_text(prefix+stimulus+'#100;$display("MISSED");$finish;end endmodule\n')
                code,log=command(['iverilog','-g2012','-s','timing','-o',self.folder/'timing.vvp',source,VROOT/'hdl/controller_devices.sv'])
                self.assertEqual(code,0,log)
                code,log=command(['vvp',self.folder/'timing.vvp'])
                self.assertNotEqual(code,0,log);self.assertIn('CW '+reason,log)

    def test_timeout_preserves_progress_and_remains_an_error(self):
        timeout=subprocess.TimeoutExpired(['vvp','controller.vvp'],300,output=b'PROGRESS control-word words=8192\n')
        with patch('dm02.controller_hardware.command',side_effect=[(0,''),timeout]):
            with self.assertRaises(subprocess.TimeoutExpired):
                simulate(self.circuit,self.folder,quick=True)
        log=(self.folder/'controller.log').read_text()
        self.assertIn('words=8192',log)
        self.assertIn('timed out after 300 seconds',log)


if __name__=='__main__':unittest.main()

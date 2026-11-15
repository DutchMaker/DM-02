from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.common import VROOT,command
from dm02.pc_hardware import Circuit,simulate
from dm02.electrical import audit


class PhysicalPc(unittest.TestCase):
    def setUp(self):
        self.circuit=Circuit()
        self.temp=tempfile.TemporaryDirectory(prefix='dm02-pc-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def pin_label(self,ref,pin,label):
        sheet=deepcopy(self.circuit.sheet)
        component=next(c for c in sheet['components'] if c['ref']==ref and any(p['number']==pin for p in c['pins']))
        p=next(p for p in component['pins'] if p['number']==pin)
        at=[l for l in sheet['labels'] if (l['x'],l['y'])==(p['x'],p['y'])]
        self.assertEqual(len(at),1)
        at[0]['name']=label
        return Circuit(sheet)

    def test_c1_at_maximum_delay_and_load_findings(self):
        result=simulate(self.circuit,self.folder,1,True,quick=True)
        self.assertTrue(result['passed'],result['log'])
        self.assertEqual(audit(self.circuit.sheet)['findings'],[])
        overloaded=[r for r in self.circuit.loads() if not r['characterized']]
        self.assertEqual(len(overloaded),8)
        self.assertEqual({r['cap_pf'] for r in overloaded},{70})

    def test_wiring_faults_are_observed(self):
        cases=[('carry prefix','U11','12','TERM0',0,'PC capture'),
               ('same-edge staging','U11','9','PC_CLOCK',0,'PC carry hold'),
               ('load mapping','U3','9','~PC_L_load',0,'PC capture'),
               ('data mapping','U1','3','DATA1',0,'PC capture'),
               ('address mapping','U7','2','PC1',0,'PC address bus'),
               ('byte OE','U6','1','LOW_OE_n',0,'PC data bus'),
               ('reset OE bypass','U14','2','GND',0,'PC reset priority/inhibition')]
        for name,ref,pin,label,corner,message in cases:
            with self.subTest(name=name):
                result=simulate(self.pin_label(ref,pin,label),self.folder,corner,quick=True)
                self.assertFalse(result['passed'],result['log'])
                self.assertIn(message,result['log'])

    def test_counter_timing_faults_have_specific_diagnostics(self):
        prefix='''`timescale 1ns/1ps
module timing;
 reg [3:0] d=0;reg clk=0,reset_n=1,load_n=0,cep=0,cet=1;
 wire [3:0] q;wire tc;
 pc161 dut(d,clk,reset_n,load_n,cep,cet,q,tc);
 initial begin #1;reset_n=0;#100;reset_n=1;#100;
'''
        cases={
            'data setup':'d=1;#1;clk=1;',
            'data hold':'clk=1;#1;d=1;',
            'load setup':'load_n=1;#1;clk=1;',
            'load hold':'clk=1;#1;load_n=1;',
            'enable setup':'load_n=1;#30;cep=1;#1;clk=1;',
            'enable hold':'clk=1;#1;cep=1;',
            'reset recovery':'reset_n=0;#40;reset_n=1;#1;clk=1;',
            'reset pulse':'reset_n=0;#1;reset_n=1;',
            'clock low pulse':'clk=1;#40;clk=0;#1;clk=1;'}
        for reason,stimulus in cases.items():
            with self.subTest(reason=reason):
                source=self.folder/'timing.sv'
                source.write_text(prefix+stimulus+'#100;$display("MISSED");$finish;end endmodule\n')
                code,log=command(['iverilog','-g2012','-s','timing','-o',self.folder/'timing.vvp',source,VROOT/'hdl/pc_devices.sv'])
                self.assertEqual(code,0,log)
                code,log=command(['vvp',self.folder/'timing.vvp'])
                self.assertNotEqual(code,0,log)
                self.assertIn('PC '+reason,log)


if __name__=='__main__':unittest.main()

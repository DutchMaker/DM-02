import copy
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dm02.common import ROOT, BUILD
from dm02.legacy import connectivity, read_sheet, inventory, library
from dm02.migrate import validate
from dm02.reporting import freshness, trace, milestones
from dm02.alu import expected


def fixture():
    return dict(name='fixture',source='fixture.sch',components=[],wires=[],labels=[],junctions=[],
                no_connects=[],bus_entries=[],buses=[])


def pin(sheet,ref,x,y,number='1'):
    sheet['components'].append(dict(ref=ref,original_ref=ref,pins=[dict(x=x,y=y,number=number)]))


class ConnectivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True,exist_ok=True)

    def test_crossing_is_not_junction(self):
        s=fixture(); s['wires']=[[0,10,20,10],[10,0,10,20]]
        pin(s,'U1',0,10); pin(s,'U2',20,10); pin(s,'U3',10,0); pin(s,'U4',10,20)
        self.assertEqual(sorted(len(n['nodes']) for n in connectivity(s)),[2,2])
        s['junctions']=[[10,10]]
        self.assertEqual(len(connectivity(s)),1)

    def test_labels_join_separated_wires(self):
        s=fixture(); pin(s,'U1',0,0); pin(s,'U2',100,100)
        s['labels']=[dict(name='D0',x=0,y=0),dict(name='D0',x=100,y=100)]
        self.assertEqual(len(connectivity(s)),1)

    def test_scalar_bus_members_are_not_shorted(self):
        s=fixture(); pin(s,'U1',0,0); pin(s,'U2',100,0)
        s['buses']=[[0,0,100,0]]
        s['labels']=[dict(name='D0',x=0,y=0),dict(name='D1',x=100,y=0)]
        self.assertEqual(len(connectivity(s)),2)

    def test_physical_pin_cannot_have_two_nets(self):
        s=fixture(); pin(s,'U1',0,0); pin(s,'U1',10,10)
        with self.assertRaisesRegex(ValueError,'multiple nets'): connectivity(s)

    def test_named_singletons_are_preserved(self):
        s=fixture(); pin(s,'BUS1',0,0); s['labels']=[dict(name='D0',x=0,y=0)]
        self.assertEqual(connectivity(s),[dict(labels=['D0'],nodes=[['BUS1','1']])])

    def test_reflection_and_hidden_power(self):
        sheet=read_sheet(ROOT/'Circuits/KiCad/Bottom-Plate/Bottom-Plate.sch')
        c=next(c for c in sheet['components'] if c['ref']=='BUS1')
        p=next(p for p in c['pins'] if p['number']=='1')
        self.assertEqual((p['x'],p['y']),(2200,750))
        sheet=read_sheet(ROOT/'Circuits/KiCad/Power-Clock/Power-Clock.sch')
        self.assertTrue(any(l['implicit'] and l['name']=='GND' for l in sheet['labels']))

    def test_missing_library_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'Missing pinned'): library('does-not-exist')

    def test_duplicate_package_unit_rejected(self):
        s=read_sheet(ROOT/'Circuits/KiCad/Registers-StackPointer/Registers-StackPointer.sch')
        c=next(c for c in s['components'] if c['ref']=='U3')
        s['components'].append(copy.deepcopy(c))
        with self.assertRaisesRegex(ValueError,'repeated unit'): inventory(s)

    def test_conflicting_multiunit_identity_rejected(self):
        s=read_sheet(ROOT/'Circuits/KiCad/Registers-StackPointer/Registers-StackPointer.sch')
        c=copy.deepcopy(next(c for c in s['components'] if c['ref']=='U3'))
        c['unit']=2; c['value']='wrong'; s['components'].append(c)
        with self.assertRaisesRegex(ValueError,'Inconsistent'): inventory(s)

    def test_empty_kicad_export_rejected(self):
        s=read_sheet(ROOT/'Circuits/KiCad/Bottom-Plate/Bottom-Plate.sch')
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            folder=Path(directory)
            def fake(args):
                (folder/'Bottom-Plate.xml').write_text('<export><components/><nets/></export>')
                return 0,''
            with patch('dm02.migrate.command',side_effect=fake):
                with self.assertRaisesRegex(ValueError,'Component preservation'): validate(s,folder)

    def test_unsupported_vector_label_rejected(self):
        original=ROOT/'Circuits/KiCad/Bottom-Plate/Bottom-Plate.sch'
        text=original.read_text().replace('\nDATA0\n','\nDATA[0..7]\n')
        self.assertIn('\nDATA[0..7]\n',text)
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            path=Path(directory)/'bus.sch'; path.write_text(text)
            with self.assertRaisesRegex(ValueError,'Vector/group'): read_sheet(path)

    def test_rotation_and_hidden_power_pin(self):
        text='''EESchema Schematic File Version 4
$Comp
L Test:Gate U1
U 1 1 1234
P 1000 2000
F 0 "U1" H 0 0 50 0000 C CNN
F 1 "Gate" H 0 0 50 0000 C CNN
1 1000 2000
0 -1 1 0
$EndComp
'''
        definition=dict(power=False,path='test.lib',pins=[dict(name='VCC',number='14',x=100,y=200,unit=0,convert=0,kind='W',hidden=True)])
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            path=Path(directory)/'rotation.sch'; path.write_text(text)
            with patch('dm02.legacy.library',return_value={'Gate':definition}): sheet=read_sheet(path)
        p=sheet['components'][0]['pins'][0]
        self.assertEqual((p['x'],p['y']),(800,2100))
        self.assertEqual(sheet['labels'],[dict(name='VCC',x=800,y=2100,implicit=True)])

    def test_register_slice_detects_swapped_schematic_outputs(self):
        from dm02.modules import registers
        s=read_sheet(ROOT/'Circuits/KiCad/Registers-StackPointer/Registers-StackPointer.sch')
        ir=next(c for c in s['components'] if c['ref']=='U14')
        a,b=(next(p for p in ir['pins'] if p['number']==n) for n in ('12','13'))
        for axis in ('x','y'): a[axis],b[axis]=b[axis],a[axis]
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            with patch('dm02.modules.BUILD',Path(directory)):
                result=registers(s)
            self.assertEqual(result['status'],'fail')
            self.assertIn('FATAL:',(Path(directory)/'registers/slice.log').read_text())


class OracleTests(unittest.TestCase):
    def test_bcd_carry_and_borrow(self):
        self.assertEqual(expected(30,0x99,1)&0x1ff,0x100)
        self.assertEqual(expected(31,0,1)&0x1ff,0x199)

    def test_overflow_boundaries(self):
        self.assertTrue(expected(9,127,1)&0x200)
        self.assertFalse(expected(9,255,1)&0x200)
        self.assertTrue(expected(11,128,1)&0x200)
        self.assertEqual(expected(11,128,1)&255,127)

    def test_shift_and_rotate(self):
        self.assertEqual(expected(22,0x80,255)&255,255)
        self.assertEqual(expected(21,0x80,255)&255,0)
        self.assertEqual(expected(23,0x81,9)&255,3)

    def test_special_zero_and_divide_by_zero(self):
        self.assertFalse(expected(12,3,3)&0x400)
        self.assertTrue(expected(18,123,0)&0x1000)


class ReportingTests(unittest.TestCase):
    def test_harness_timeout_preserves_partial_log_and_error_evidence(self):
        import run
        err=subprocess.TimeoutExpired(['python','-m','unittest'],600,output=b'test_slow ... \xff')
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            with patch('run.BUILD',Path(directory)),patch('run.command',side_effect=err):
                result=run.harness_check()
            self.assertEqual(result['status'],'error')
            self.assertEqual(result['exit_code'],124)
            log=(Path(directory)/'tests.log').read_text()
            self.assertIn('test_slow',log)
            self.assertIn('timed out after 600 seconds',log)

    def test_harness_launch_error_is_reported(self):
        import run
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            with patch('run.BUILD',Path(directory)),patch('run.command',side_effect=FileNotFoundError('python missing')):
                result=run.harness_check()
            self.assertEqual(result['status'],'error')
            self.assertIn('python missing',(Path(directory)/'tests.log').read_text())

    def test_encoding_duplicates_fail_closed(self):
        from dm02.encoding import unique
        with self.assertRaisesRegex(ValueError,'Duplicate encoding'):
            unique([(0,'A'),(0,'B')])

    def test_source_encoding_consistency(self):
        from dm02.encoding import run
        BUILD.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            with patch('dm02.encoding.BUILD',Path(directory)):
                result=run()
            self.assertEqual(result['status'],'pass')

    def test_freshness_catches_change_addition_deletion(self):
        report=dict(state='complete',source_hashes={'a':'1'})
        self.assertTrue(freshness(report,{'a':'1'})['fresh'])
        for current in ({'a':'2'},{'a':'1','b':'2'},{}):
            self.assertFalse(freshness(report,current)['fresh'])

    def test_in_progress_is_not_current_evidence(self):
        self.assertFalse(freshness(dict(state='running',source_hashes={'a':'1'}),{'a':'1'})['fresh'])

    def test_missing_requirement_evidence_is_blocked(self):
        self.assertEqual(trace(dict(requirements=[dict(id='R',gate='missing')]),[])[0]['status'],'blocked')

    def test_partial_check_does_not_close_full_requirement(self):
        checks=[dict(id='migration',status='pass',requirement_status='limited')]
        self.assertEqual(trace(dict(requirements=[dict(id='R',gate='migration')]),checks)[0]['status'],'limited')

    def test_milestones_require_all_acceptance_evidence(self):
        spec=dict(requirements=[dict(id='R',gate='g')],milestones=[dict(number=1,title='test',requirements=['R'])])
        self.assertEqual(milestones(spec,[])[0]['status'],'blocked')
        for status in ('limited','fail','error','blocked'):
            self.assertNotEqual(milestones(spec,[dict(id='g',status=status)])[0]['status'],'complete')
        self.assertEqual(milestones(spec,[dict(id='g',status='pass')])[0]['status'],'complete')
        self.assertNotEqual(milestones(spec,[dict(id='g',status='pass',requirement_status='limited')])[0]['status'],'complete')


if __name__=='__main__': unittest.main()

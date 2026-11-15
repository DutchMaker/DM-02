"""Independent analytical and acceptance-window tests for the transient path."""
import math
import copy
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scipy.linalg import expm
from dm02.ibis_factors import coefficients
from dm02.ibis_transient import factors, independent_ode, measure
from dm02.analog_acceptance import evaluate
from dm02.common import VROOT
from dm02 import loaded_output, ibis_driver


def linear_model():
    # A 50-ohm pullup/pulldown, with zero clamps, has closed-form RC/RLC
    # solutions. These are independent of the manufacturer model tables.
    up=[[x,-x/50,-x/50,-x/50] for x in (-20,0,20)]
    down=[[x,x/50,x/50,x/50] for x in (-20,0,20)]
    zero=[[-20,0,0,0],[20,0,0,0]]
    return dict(voltage=[5,5,5],capacitance=[4e-12]*3,
        tables={'Pullup':up,'Pulldown':down,'GND Clamp':zero,'POWER Clamp':zero})


class TransientMath(unittest.TestCase):
    def test_dynamic_extraction_against_closed_form_rc(self):
        data=linear_model();data['waves']=[]
        for fixture in (0,5):
            data['waves'].append(dict(edge='rising',rows=[[0,fixture]],
                params=dict(V_fixture=fixture,R_fixture=1000)))
        duration=1e-9
        conductance=1/50+1/1000
        tau=4e-12/conductance
        slope=(5/50/duration)/conductance
        def analytic(rows,t,col):
            fixture=rows[0][1]
            equilibrium=(fixture/1000)/conductance
            return equilibrium+slope*(t-tau+tau*math.exp(-t/tau)),slope*(1-math.exp(-t/tau))
        for t in (.12e-9,.5e-9,.95e-9):
            ku,kd,_=coefficients(data,'rising',1,t,wave_sampler=analytic)
            self.assertAlmostEqual(ku,t/duration,places=12)
            self.assertAlmostEqual(kd,1-t/duration,places=12)

    def test_singular_fixtures_are_rejected(self):
        data=linear_model()
        data['waves']=[dict(edge='rising',rows=[[0,0,0,0],[50e-9,0,0,0]],
            params=dict(V_fixture=0,R_fixture=1000))]*2
        with self.assertRaises(ZeroDivisionError):
            factors(data,'rising',1)

    def test_window_monitor_detects_between_sample_glitch(self):
        waveform=np.array([[0,5],[265e-9,5],[280e-9,5],[281e-9,1],[282e-9,5],[315e-9,5],[500e-9,5]])
        checked=measure(waveform,'rising',265,315)
        self.assertFalse(checked['passed'])
        self.assertEqual(checked['window_min_v'],1)
        self.assertAlmostEqual(checked['stable_threshold_ns'],281.25)

    def test_window_boundaries_are_checked(self):
        waveform=np.array([[0,0],[264e-9,0],[266e-9,3],[500e-9,3]])
        self.assertFalse(measure(waveform,'rising',265,315)['passed'])
        self.assertTrue(measure(waveform,'rising',267,315)['passed'])

    def test_invalid_waveforms_cannot_be_extrapolated_into_a_pass(self):
        for samples in ([[0,5],[264e-9,5]], [[266e-9,5],[500e-9,5]],
                        [[0,5],[300e-9,float('nan')],[500e-9,5]],
                        [[0,5],[300e-9,5],[290e-9,5],[500e-9,5]],
                        [[0,5],[300e-9,5],[300e-9,5],[500e-9,5]]):
            with self.subTest(samples=samples), self.assertRaisesRegex(ValueError,'incomplete capture'):
                measure(np.array(samples),'rising',265,315)
        with self.assertRaises(ValueError):
            measure(np.array([[0,5],[500e-9,5]]),'rising',float('nan'),315)

    def test_independent_ode_against_linear_rlc_matrix_solution(self):
        package=(.047,7.118e-9,.439e-12)
        model=linear_model()
        factor=np.array([[0,1,0],[50e-9,1,0]])
        actual=independent_ode(model,factor,'rising',package,50,0,stop_ns=10)
        cdie=4;cout=50.439;inductance=7.118;resistance=.047;driver=50
        # Kirchhoff's equations in ns, pF and mA. Matrix exponential is an
        # exact solution of this constant linear network, unlike Radau steps.
        matrix=np.array([[-1000/(driver*cdie),0,-1/cdie],
            [0,0,1/cout],[1000/inductance,-1000/inductance,-resistance/inductance]])
        equilibrium=np.array([5,5,0])
        for t in (.1,.5,1,2,5,10):
            expected=equilibrium+expm(matrix*t)@(-equilibrium)
            measured=np.interp(t*1e-9,actual[:,0],actual[:,1])
            self.assertAlmostEqual(measured,expected[1],places=6)


class AcceptanceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((VROOT/'analog-contract.json').read_text())
        cls.data=json.loads((VROOT/'tests/fixtures/analog-reference.json').read_text())
        cls.requirements=json.loads((VROOT/'requirements.json').read_text())
        # The archived experiment predates serialized stimulus metadata. Its
        # original script explicitly used these values; numeric results stay
        # unchanged. New runs emit these fields directly and are checked below.
        for row in cls.data['loads']:
            row['shape_launch_ns']=300 if row['fault']=='late-launch' else 173
            row['driver_enabled']=row['fault']!='disabled'

    def test_real_experiment_satisfies_contract(self):
        self.assertTrue(evaluate(self.contract,self.data,self.requirements)['passed'])

    def test_false_success_flag_cannot_hide_bad_voltage(self):
        bad=copy.deepcopy(self.data)
        row=next(r for r in bad['loads'] if r['case']=='rising-normal')
        row['window_min_v']=1.9
        with self.assertRaisesRegex(ValueError,'verdict disagrees'):
            evaluate(self.contract,bad,self.requirements)

    def test_independent_voltage_disagreement_blocks_acceptance(self):
        bad=copy.deepcopy(self.data)
        bad['independent'][0]['max_voltage_difference_v']=.5
        with self.assertRaisesRegex(ValueError,'Independent solver disagreement'):
            evaluate(self.contract,bad,self.requirements)

    def test_capture_cannot_be_relaxed(self):
        contract=copy.deepcopy(self.contract);contract['capture_ns']=400
        with self.assertRaisesRegex(ValueError,'Contract mismatch: capture_ns'):
            evaluate(contract,self.data,self.requirements)

    def test_reduced_load_cannot_be_substituted(self):
        bad=copy.deepcopy(self.data)
        next(r for r in bad['loads'] if r['case']=='falling-normal')['capacitance_pf']=5
        with self.assertRaisesRegex(ValueError,'Load changed'):
            evaluate(self.contract,bad,self.requirements)

    def test_missing_fault_blocks_acceptance(self):
        bad=copy.deepcopy(self.data);bad['loads']=bad['loads'][:-1]
        with self.assertRaisesRegex(ValueError,'Load/fault coverage'):
            evaluate(self.contract,bad,self.requirements)

    def test_fast_corner_cannot_inherit_nominal_acceptance(self):
        contract=copy.deepcopy(self.contract);contract['qualified_corner']='max'
        with self.assertRaisesRegex(ValueError,'Unqualified corner promoted'):
            evaluate(contract,self.data,self.requirements)

    def test_tolerances_and_fault_stimuli_cannot_be_relaxed(self):
        for key in ('fixture_max_voltage_error_v','fixture_threshold_error_ns',
                    'independent_solver_max_voltage_error_v','refinement_threshold_difference_ns'):
            contract=copy.deepcopy(self.contract);contract[key]*=10
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'Contract mismatch'):
                evaluate(contract,self.data,self.requirements)
        contract=copy.deepcopy(self.contract);contract['faults']['late_shape_launch_ns']=400
        with self.assertRaisesRegex(ValueError,'Fault stimulus changed'):
            evaluate(contract,self.data,self.requirements)

    def test_serialized_stimulus_must_match_the_case(self):
        for case,key,value in (('rising-normal','shape_launch_ns',0),
                               ('falling-disabled','driver_enabled',True),
                               ('rising-late-launch','shape_launch_ns',173)):
            bad=copy.deepcopy(self.data)
            next(r for r in bad['loads'] if r['case']==case)[key]=value
            with self.subTest(case=case), self.assertRaisesRegex(ValueError,'Stimulus identity'):
                evaluate(self.contract,bad,self.requirements)

    def test_nonfinite_evidence_is_rejected(self):
        for value in (float('nan'),float('inf'),float('-inf')):
            bad=copy.deepcopy(self.data);bad['loads'][0]['window_min_v']=value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError,'Nonfinite'):
                evaluate(self.contract,bad,self.requirements)


class IntegrationGuards(unittest.TestCase):
    def test_missing_cache_blocks_even_with_previous_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); cache=root/'cache';cache.mkdir()
            build=root/'build';folder=build/'analog/loaded';folder.mkdir(parents=True)
            (folder/'acceptance.json').write_text('{"requirement_status":"pass"}')
            with patch.dict(os.environ,DM02_MODEL_CACHE=str(cache)),patch.object(loaded_output,'BUILD',build), \
                    patch.object(ibis_driver,'qualify') as qualify:
                result=loaded_output.run()
            self.assertEqual(result['status'],'blocked')
            self.assertEqual(result['artifacts'],['analog/loaded/state.json'])
            self.assertEqual(json.loads((folder/'state.json').read_text())['state'],'blocked')
            qualify.assert_not_called()

    def test_served_and_symlinked_cache_paths_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside the served'):
            loaded_output.require_private(VROOT/'build/model-cache')
        with tempfile.TemporaryDirectory() as directory:
            link=Path(directory)/'model';link.symlink_to(VROOT/'models.json')
            with self.assertRaisesRegex(ValueError,'outside the served'):
                loaded_output.require_private(link)

    def test_changed_model_or_checker_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'sclm097a.ibs';checker=root/'ibischk7_64'
            model.write_bytes(b'changed');checker.write_bytes(b'changed checker')
            with patch.object(ibis_driver,'checker_run') as execute:
                with self.assertRaises(AssertionError):
                    ibis_driver.qualify(model,checker,root/'work',root/'out')
                with patch.object(ibis_driver,'MODEL_HASH',hashlib.sha256(model.read_bytes()).hexdigest()):
                    with self.assertRaises(AssertionError):
                        ibis_driver.qualify(model,checker,root/'work',root/'out')
                execute.assert_not_called()

    def test_checker_zero_exit_does_not_imply_success(self):
        for verdict,errors,code,passed in (('File Failed',2,0,False),('File Passed',2,0,False),
                                          ('File Passed',0,1,False),('File Passed',0,0,True)):
            result=subprocess.CompletedProcess([],code,stdout=f'IBISCHK7 V7.2.1\nErrors : {errors}\n{verdict}',stderr='')
            with self.subTest(verdict=verdict,errors=errors,code=code), \
                    patch.object(ibis_driver.subprocess,'run',return_value=result):
                checked,_=ibis_driver.checker_run(Path('checker'),Path('model'))
                self.assertEqual(checked['passed'],passed)

    def test_qualification_error_cannot_reuse_prior_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cache=root/'cache';cache.mkdir()
            for name in ('sclm097a.ibs','ibischk7_64'): (cache/name).write_text('invalid')
            with patch.dict(os.environ,DM02_MODEL_CACHE=str(cache)),patch.object(loaded_output,'BUILD',root/'build'), \
                    patch('dm02.ibis_transient.experiment') as experiment:
                with self.assertRaises(AssertionError): loaded_output.run()
                experiment.assert_not_called()
            self.assertEqual(json.loads((root/'build/analog/loaded/state.json').read_text())['state'],'error')


if __name__=='__main__': unittest.main()

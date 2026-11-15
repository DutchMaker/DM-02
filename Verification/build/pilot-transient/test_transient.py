"""Independent analytical and acceptance-window tests for the transient path."""
import math
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from scipy.linalg import expm
from explore import coefficients
from transient import factors, independent_ode, measure
from accept import evaluate


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
        here=Path(__file__).resolve().parent
        cls.contract=json.loads((here/'contract.json').read_text())
        cls.data=json.loads((here/'exploration.json').read_text())
        cls.requirements=json.loads((here.parents[2]/'Verification/requirements.json').read_text())

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


if __name__=='__main__': unittest.main()

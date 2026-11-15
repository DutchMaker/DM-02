"""Analytical checks independent of TI's numeric data; run with unittest."""
import unittest
from audit import crossing, current, endpoint_audit, interp, number, root


class AuditMath(unittest.TestCase):
    def test_units_and_missing_values(self):
        self.assertEqual(number('NA'), None)
        self.assertAlmostEqual(number('4.0pF'), 4e-12)
        self.assertAlmostEqual(number('7.118e-09'), 7.118e-9)
        self.assertAlmostEqual(number('3.495nH'), 3.495e-9)

    def test_interpolation_and_constant_tails(self):
        table = [[-1, -3], [1, 5], [2, 6]]
        self.assertEqual(interp(table, 0, 1), 1)
        self.assertEqual(interp(table, -5, 1), -3)
        self.assertEqual(interp(table, 9, 1), 6)

    def test_last_crossing_after_ringing(self):
        rising = [[0, 0], [1, 3], [2, 1], [3, 4]]
        self.assertAlmostEqual(crossing(rising, 1, 2, True), 2+1/3)
        falling = [[t, 4-v] for t, v in rising]
        self.assertAlmostEqual(crossing(falling, 1, 2, False), 2+1/3)
        self.assertIsNone(crossing(rising, 1, 5, True))

    def test_linear_driver_against_resistor_divider(self):
        # 50-ohm high/low output resistance against the 1-kohm fixture.
        # All three supplies and both fixture rails have closed-form answers.
        up = [[x, -x/50, -x/50, -x/50] for x in (-5, 0, 10)]
        down = [[x, x/50, x/50, x/50] for x in (-5, 0, 10)]
        zero = [[-5, 0, 0, 0], [10, 0, 0, 0]]
        data = dict(voltage=[5, 4.5, 5.5], tables={'Pullup': up, 'Pulldown': down, 'GND Clamp': zero, 'POWER Clamp': zero})
        for col, vcc in enumerate(data['voltage'], 1):
            for state in ('high', 'low'):
                for fixture in (0, vcc):
                    expected = ((vcc if state == 'high' else 0)/50 + fixture/1000)/(1/50+1/1000)
                    got = root(lambda v: current(data, v, col, state)+(v-fixture)/1000, -1, 7)
                    self.assertAlmostEqual(got, expected, places=12)
        # Synthetic waveform endpoints follow those same divider voltages.
        data['waves'] = []
        for edge in ('rising', 'falling'):
            for rail in (0, 1):
                params = dict(R_fixture=1000, C_fixture=0, L_fixture=0,
                    V_fixture=rail*5, V_fixture_min=rail*4.5, V_fixture_max=rail*5.5)
                low = [v*rail/21 for v in data['voltage']]
                high = [v*(20+rail)/21 for v in data['voltage']]
                first, last = (low, high) if edge == 'rising' else (high, low)
                data['waves'].append(dict(edge=edge, line=0, params=params, rows=[[0]+first, [50e-9]+last]))
        endpoints, _ = endpoint_audit(data)
        self.assertEqual(len(endpoints), 24)
        self.assertLess(max(abs(r['difference_v']) for r in endpoints), 1e-12)


if __name__ == '__main__':
    unittest.main()

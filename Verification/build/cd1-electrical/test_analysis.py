"""Analytical geometry fixtures and fault injections for the CD1 audit."""
from copy import deepcopy
from pathlib import Path
import io
import json
import math
import unittest
from shapely.geometry import Polygon, box
from analyze import audit, microstrip, plane_geometry

HERE = Path(__file__).resolve().parent


def fixture():
    return dict(tracks=[dict(id='clock', net='/CLOCK', layer='F.Cu', width_mm=.25,
                            start=[0, 5], end=[10, 5], length_mm=10)])


class GeometryTests(unittest.TestCase):
    def test_solid_plane(self):
        nets, _ = audit(fixture(), {'B.Cu': box(-1, -1, 11, 11)})
        self.assertEqual(nets['/CLOCK']['uncovered_centerline_mm'], 0)

    def test_slot_not_missed_between_samples(self):
        plane = box(-1, -1, 11, 11).difference(box(4.001, -1, 4.011, 11))
        nets, _ = audit(fixture(), {'B.Cu': plane})
        self.assertAlmostEqual(nets['/CLOCK']['uncovered_centerline_mm'], .01)

    def test_hole(self):
        plane = Polygon([(-1, -1), (11, -1), (11, 11), (-1, 11)],
                        [[(3, 3), (7, 3), (7, 7), (3, 7)]])
        nets, _ = audit(fixture(), {'B.Cu': plane})
        self.assertAlmostEqual(nets['/CLOCK']['uncovered_centerline_mm'], 4)

    def test_same_layer_pour_does_not_count(self):
        nets, _ = audit(fixture(), {'F.Cu': box(-1, -1, 11, 11), 'B.Cu': Polygon()})
        self.assertEqual(nets['/CLOCK']['uncovered_centerline_mm'], 10)

    def test_diagonal_intersection(self):
        data = fixture()
        data['tracks'][0].update(start=[0, 0], end=[10, 10], length_mm=math.sqrt(200))
        nets, _ = audit(data, {'B.Cu': box(2, 2, 8, 8)})
        self.assertAlmostEqual(nets['/CLOCK']['uncovered_centerline_mm'], 4 * math.sqrt(2))

    def test_recorded_length_mutation(self):
        data = fixture()
        data['tracks'][0]['length_mm'] = 11
        with self.assertRaises(AssertionError):
            audit(data, {'B.Cu': box(-1, -1, 11, 11)})

    def test_native_polygon_classification_mutation(self):
        data = json.loads((HERE / 'geometry.json').read_text())
        mutant = deepcopy(data)
        mutant['native_zone_samples'][0]['inside'] = not mutant['native_zone_samples'][0]['inside']
        with self.assertRaises(AssertionError):
            plane_geometry(mutant)

    def test_layer_swap_mutation(self):
        data = json.loads((HERE / 'geometry.json').read_text())
        for zone in data['ground_zones']:
            zone['layer'] = {'F.Cu': 'B.Cu', 'B.Cu': 'F.Cu'}[zone['layer']]
        with self.assertRaises(AssertionError):
            plane_geometry(data)


class MicrostripTests(unittest.TestCase):
    def test_air_speed_and_dimensional_scaling(self):
        a = microstrip(.25, .8, 1)
        b = microstrip(2.5, 8, 1)
        self.assertEqual(a, b)
        self.assertEqual(a['effective_er'], 1)
        self.assertAlmostEqual(a['delay_ps_per_mm'], 3.335640952, places=8)

    def test_wide_air_strip_parallel_plate_limit(self):
        # Independent electrostatic limit C' -> epsilon0 * W/h in F/m.
        result = microstrip(1000, 1, 1)
        expected_pf_per_mm = 8.8541878128e-12 * 1000 * 1e9
        self.assertLess(abs(result['capacitance_pf_per_mm']/expected_pf_per_mm - 1), .004)

    def test_height_sensitivity(self):
        close = microstrip(.25, .2, 4.8)
        far = microstrip(.25, 1.53, 4.8)
        self.assertGreater(close['capacitance_pf_per_mm'], far['capacitance_pf_per_mm'])
        self.assertLess(close['impedance_ohm'], far['impedance_ohm'])

    def test_invalid_geometry_rejected(self):
        for args in ((0, 1, 4), (1, 0, 4), (1, 1, .5)):
            with self.assertRaises(AssertionError):
                microstrip(*args)


if __name__ == '__main__':
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    (HERE / 'test-results.json').write_text(json.dumps(dict(
        passed=result.wasSuccessful(), tests=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), log=log), indent=2) + '\n')
    print(log)
    raise SystemExit(0 if result.wasSuccessful() else 1)

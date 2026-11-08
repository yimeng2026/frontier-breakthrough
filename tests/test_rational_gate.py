import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rational_gate import assess_prediction_domain, rational_jacobian, rational_root_records
from analyze_hahn1_high_temperature import PARAMETER_NAMES as CUBIC_NAMES, hahn_model
from analyze_kirby2_prospective_gate import PARAMETER_NAMES as QUADRATIC_NAMES, kirby_model


class RationalGateTests(unittest.TestCase):
    def test_cubic_jacobian_matches_finite_differences(self):
        parameters = dict(zip(CUBIC_NAMES, [2.0, 0.1, 0.01, 0.001, 0.02, -0.001, 0.0001]))
        x = np.array([0.2, 0.5, 1.0])
        analytic = rational_jacobian(x, parameters, CUBIC_NAMES[:4], CUBIC_NAMES[4:], hahn_model)
        numeric = np.empty_like(analytic)
        step = 1.0e-6
        for index, name in enumerate(CUBIC_NAMES):
            upper, lower = dict(parameters), dict(parameters)
            upper[name] += step
            lower[name] -= step
            numeric[:, index] = (hahn_model(x, *upper.values()) - hahn_model(x, *lower.values())) / (2 * step)
        np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=1.0e-8)

    def test_quadratic_domain_and_roots_match_known_answer(self):
        parameters = {"b1": 1.0, "b2": 0.0, "b3": 0.0, "b4": -3.0, "b5": 2.0}
        names = QUADRATIC_NAMES
        roots = rational_root_records(parameters, names[:3], names[3:])
        real_roots = [root["root_x"] for root in roots if root["is_real"]]
        np.testing.assert_allclose(real_roots, [0.5, 1.0], rtol=0, atol=1.0e-12)
        inside = assess_prediction_domain(parameters, np.array([0.4, 0.6]), kirby_model, names[:3], names[3:])
        outside = assess_prediction_domain(parameters, np.array([0.6, 0.8]), kirby_model, names[:3], names[3:])
        self.assertFalse(inside["domain_admissible"])
        self.assertTrue(outside["domain_admissible"])

    def test_cubic_domain_rejects_two_poles_in_interval(self):
        parameters = {"b1": 1.0, "b2": 0.0, "b3": 0.0, "b4": 0.0, "b5": -6.0, "b6": 11.0, "b7": -6.0}
        result = assess_prediction_domain(parameters, np.array([0.4, 0.6]), hahn_model, CUBIC_NAMES[:4], CUBIC_NAMES[4:])
        self.assertFalse(result["domain_admissible"])
        self.assertEqual(len(result["real_roots_in_closed_interval"]), 1)
        self.assertAlmostEqual(result["real_roots_in_closed_interval"][0], 0.5)


if __name__ == "__main__":
    unittest.main()

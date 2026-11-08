import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_kirby2_prospective_gate import PARAMETER_NAMES, analyze, assess_prediction_domain, kirby_jacobian, kirby_model, load_kirby_data, validate_summary


class Kirby2ProspectiveGateTests(unittest.TestCase):
    def test_raw_data_and_quadratic_domain_answers(self):
        x, y = load_kirby_data(ROOT / "data/Kirby2.dat", "cbd288dd9d8586ec97ca408277d1a27ef41b19b543c158d594af189de80ae61c")
        self.assertEqual((len(x), len(y)), (151, 151))
        self.assertEqual((x[0], y[0]), (9.65, 0.0082))
        parameters = {"b1": 1.0, "b2": 0.0, "b3": 0.0, "b4": -3.0, "b5": 2.0}
        inside = assess_prediction_domain(parameters, np.array([0.4, 0.6]))
        outside = assess_prediction_domain(parameters, np.array([0.6, 0.8]))
        self.assertFalse(inside["domain_admissible"])
        self.assertEqual(len(inside["real_roots_in_closed_interval"]), 1)
        self.assertAlmostEqual(inside["real_roots_in_closed_interval"][0], 0.5)
        self.assertTrue(outside["domain_admissible"])

    def test_analytic_jacobian_matches_finite_differences(self):
        parameters = dict(zip(PARAMETER_NAMES, [1.0, 0.1, 0.01, 0.02, 0.001]))
        x = np.array([0.2, 0.5, 1.0])
        analytic = kirby_jacobian(x, parameters)
        numeric = np.empty_like(analytic)
        step = 1.0e-6
        for index, name in enumerate(PARAMETER_NAMES):
            upper, lower = dict(parameters), dict(parameters)
            upper[name] += step
            lower[name] -= step
            numeric[:, index] = (kirby_model(x, *upper.values()) - kirby_model(x, *lower.values())) / (2 * step)
        np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=1.0e-8)

    def test_full_fit_certifies_and_gate_logic_is_complete(self):
        summary = analyze()
        self.assertEqual(validate_summary(summary), [])
        self.assertTrue(summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"])
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual(sum(fold["test_count"] for fold in summary["folds"]), 151)
        for fold in summary["folds"]:
            expected = fold["domain_audit"]["domain_admissible"] and fold["identifiability"]["minimal_numerical_identifiability"] and fold["test_metrics"]["rmse"] <= fold["baseline_test_metrics"]["rmse"]
            self.assertEqual(fold["decision"]["gated_limited_support"], expected)
        self.assertFalse(summary["decision"]["universal_law_claimed"])


if __name__ == "__main__":
    unittest.main()

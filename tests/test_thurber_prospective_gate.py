import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_thurber_prospective_gate import analyze, assess_prediction_domain, load_thurber_data, validate_summary


class ThurberProspectiveGateTests(unittest.TestCase):
    def test_raw_data_and_known_domain_answers(self):
        x, y = load_thurber_data(ROOT / "data/Thurber.dat", "806b8d00a5365eff907561db796fec3af8a26a5f353297d4311fd46ed5b0146f")
        self.assertEqual((len(x), len(y)), (37, 37))
        self.assertEqual((x[0], y[0], x[-1], y[-1]), (-3.067, 80.574, 2.2, 1457.628))
        parameters = {"b1": 1.0, "b2": 0.0, "b3": 0.0, "b4": 0.0, "b5": -6.0, "b6": 11.0, "b7": -6.0}
        inside = assess_prediction_domain(parameters, np.array([0.4, 0.6]))
        outside = assess_prediction_domain(parameters, np.array([2.0, 3.0]))
        self.assertFalse(inside["domain_admissible"])
        self.assertEqual(len(inside["real_roots_in_closed_interval"]), 1)
        self.assertAlmostEqual(inside["real_roots_in_closed_interval"][0], 0.5)
        self.assertTrue(outside["domain_admissible"])

    def test_full_fit_certifies_and_every_fold_preserves_gate_logic(self):
        summary = analyze()
        self.assertEqual(validate_summary(summary), [])
        self.assertTrue(summary["full_fit_certification"]["matches_nist_within_frozen_tolerances"])
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual(sum(fold["test_count"] for fold in summary["folds"]), 37)
        self.assertFalse(summary["analysis_scope"]["dataset_used_to_design_gate"])
        for fold in summary["folds"]:
            expected = fold["domain_audit"]["domain_admissible"] and fold["identifiability"]["minimal_numerical_identifiability"] and fold["test_metrics"]["rmse"] <= fold["baseline_test_metrics"]["rmse"]
            self.assertEqual(fold["decision"]["gated_limited_support"], expected)
        self.assertFalse(summary["decision"]["universal_law_claimed"])


if __name__ == "__main__":
    unittest.main()

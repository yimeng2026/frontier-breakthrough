import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_hahn1_fold1_identifiability import analyze, hahn_jacobian, validate_summary
from analyze_hahn1_high_temperature import PARAMETER_NAMES, hahn_model


class Hahn1Fold1IdentifiabilityTests(unittest.TestCase):
    def test_analytic_jacobian_matches_finite_differences(self):
        parameters = dict(zip(PARAMETER_NAMES, [2.0, 0.1, 0.01, 0.001, 0.02, -0.001, 0.0001]))
        x = np.array([0.2, 0.5, 1.0])
        analytic = hahn_jacobian(x, parameters)
        numeric = np.empty_like(analytic)
        step = 1.0e-6
        for index, name in enumerate(PARAMETER_NAMES):
            upper = dict(parameters)
            lower = dict(parameters)
            upper[name] += step
            lower[name] -= step
            numeric[:, index] = (hahn_model(x, *upper.values()) - hahn_model(x, *lower.values())) / (2 * step)
        np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=1.0e-8)

    def test_post_hoc_analysis_preserves_frozen_fits_and_failure(self):
        summary = analyze()
        original = json.loads((ROOT / "validation/grouped-stress.json").read_text(encoding="utf-8"))
        original_hahn = next(item for item in original["datasets"] if item["id"] == "hahn1")
        self.assertEqual(validate_summary(summary), [])
        self.assertEqual(len(summary["folds"]), 5)
        self.assertTrue(summary["analysis_scope"]["post_hoc"])
        self.assertFalse(summary["analysis_scope"]["refit"])
        for fold, source in zip(summary["folds"], original_hahn["folds"]):
            self.assertEqual(fold["model_parameters"], source["model_parameters"])
            self.assertEqual(fold["test_metrics"], source["model_metrics"])
            self.assertEqual(fold["training_jacobian"]["parameter_count"], 7)
            self.assertGreaterEqual(fold["training_jacobian"]["scaled_condition_number"], 1.0)
            self.assertGreaterEqual(fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"], 0.0)
        first = summary["folds"][0]
        self.assertEqual(first["train_count"], 189)
        self.assertEqual(first["test_count"], 47)
        self.assertEqual(len(first["held_out_points"]), 47)
        self.assertAlmostEqual(first["test_metrics"]["rmse"], 354.02266177305074)
        self.assertFalse(summary["decision"]["fold_1_failure_reversed"])


if __name__ == "__main__":
    unittest.main()

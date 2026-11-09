import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_chwirut1_native_holdout.py"
PROTOCOL = ROOT / "validation/chwirut1-native-holdout-protocol.json"
CANDIDATE = ROOT / "validation/chwirut1-ellipsoid-coverage.json"


class Chwirut1NativeHoldoutTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native Chwirut1 analysis: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_chwirut1_native_holdout", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_native_exponential_formula_and_denominator_singularity(self):
        module = self.load_module()
        x = np.array([0.5, 1.0, 2.0])
        p = (0.15, 0.008, 0.01)
        np.testing.assert_allclose(module.native_model(x, *p), np.exp(-p[0]*x)/(p[1]+p[2]*x), rtol=0, atol=1e-14)
        self.assertTrue(np.isnan(module.native_model(np.array([1.0]), 0.1, -0.01, 0.01)[0]))

    def test_known_answer_reproduction_is_not_holdout_evidence(self):
        module = self.load_module()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        known = module.analyze()["known_answer"]
        self.assertTrue(known["optimizer_success"])
        self.assertTrue(known["within_certified_tolerances"])
        self.assertEqual(known["evidence_class"], "known_answer_reproduction_not_holdout")
        self.assertAlmostEqual(known["rss"], protocol["known_answer_rule"]["certified_rss"], delta=protocol["known_answer_rule"]["rss_absolute_tolerance"])
        for name, certified in protocol["known_answer_rule"]["certified_parameters"].items():
            self.assertTrue(math.isclose(known["parameters"][name], certified, rel_tol=protocol["known_answer_rule"]["parameter_relative_tolerance"], abs_tol=protocol["known_answer_rule"]["parameter_absolute_tolerance"]), name)

    def test_five_fold_metrics_repeated_observations_and_frozen_inputs(self):
        module = self.load_module()
        summary = module.analyze()
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual([len(fold["point_results"]) for fold in summary["folds"]], [57, 54, 51, 23, 29])
        self.assertEqual(sum(len(fold["point_results"]) for fold in summary["folds"]), 214)
        self.assertEqual(summary["metadata_amendment_sha256"], module.sha256(module.ROOT / "validation/chwirut1-native-holdout-protocol-amendment-01.json"))
        for fold, old in zip(summary["folds"], candidate["folds"]):
            self.assertEqual(fold["rational_candidate_test_metrics"], old["test_metrics"])
            self.assertEqual(fold["cubic_baseline_test_metrics"], old["baseline_test_metrics"])
            self.assertEqual([point["x"] for point in fold["point_results"]], [point["x"] for point in old["point_results"]])
            for point, old_point in zip(fold["point_results"], old["point_results"]):
                self.assertEqual(point["observed_y"], old_point["observed_y"])
                self.assertEqual(point["rational_snapshot_prediction"], old_point["snapshot_prediction"])
                self.assertEqual(point["rational_absolute_residual"], old_point["actual_absolute_residual"])
                if fold["optimizer_success"]:
                    self.assertTrue(math.isfinite(point["native_prediction"]))
                    self.assertAlmostEqual(point["native_absolute_residual"], abs(point["observed_y"] - point["native_prediction"]), places=12)
            if fold["optimizer_success"]:
                residuals = np.array([point["observed_y"] - point["native_prediction"] for point in fold["point_results"]])
                metrics = fold["native_test_metrics"]
                self.assertAlmostEqual(metrics["rmse"], float(np.sqrt(np.mean(residuals ** 2))), places=12)
                self.assertAlmostEqual(metrics["mae"], float(np.mean(np.abs(residuals))), places=12)
                self.assertAlmostEqual(metrics["max_absolute_residual"], float(np.max(np.abs(residuals))), places=12)
            else:
                self.assertIsNone(fold["native_test_metrics"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_native_bounds_and_independence_are_not_overclaimed_and_outputs_are_real(self):
        module = self.load_module()
        summary = module.analyze()
        for key in ["native_physical_law_validated", "native_probability_calibration_claimed", "native_deterministic_bounds_claimed", "rational_bounds_transferred_to_native", "independent_physical_experiment_claimed", "independent_model_family_claimed", "certified_full_fit_used_as_holdout", "failed_fits_hidden"]:
            self.assertFalse(summary["decision"][key], key)
        self.assertEqual(summary["totals"]["native_optimizer_failure_count"], sum(not fold["optimizer_success"] for fold in summary["folds"]))
        self.assertEqual(set(summary["parameter_stability"]), {"b1", "b2", "b3"})
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(summary, stored)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

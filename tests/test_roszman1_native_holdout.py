import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_roszman1_native_holdout.py"
PROTOCOL = ROOT / "validation/roszman1-native-holdout-protocol.json"
CANDIDATE = ROOT / "validation/roszman1-ellipsoid-coverage.json"


class Roszman1NativeHoldoutTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native Roszman1 analysis: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_roszman1_native_holdout", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_native_model_formula_and_exact_singularity(self):
        module = self.load_module()
        x = np.array([-1000.0, -500.0, -200.0])
        parameters = (0.2, -0.000005, 1200.0, -150.0)
        expected = parameters[0] - parameters[1] * x - np.arctan(parameters[2] / (x - parameters[3])) / np.pi
        np.testing.assert_allclose(module.native_model(x, *parameters), expected, rtol=0, atol=1e-15)
        self.assertTrue(np.isnan(module.native_model(np.array([-150.0]), *parameters)[0]))

    def test_known_answer_reproduction_is_not_holdout_evidence(self):
        module = self.load_module()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        known = module.analyze()["known_answer"]
        self.assertTrue(known["optimizer_success"])
        self.assertEqual(known["evidence_class"], "known_answer_reproduction_not_holdout")
        self.assertAlmostEqual(known["rss"], protocol["known_answer_rule"]["certified_rss"], delta=protocol["known_answer_rule"]["rss_absolute_tolerance"])
        for name, certified in protocol["known_answer_rule"]["certified_parameters"].items():
            self.assertTrue(math.isclose(known["parameters"][name], certified, rel_tol=protocol["known_answer_rule"]["parameter_relative_tolerance"], abs_tol=protocol["known_answer_rule"]["parameter_absolute_tolerance"]), name)

    def test_five_fold_metrics_and_frozen_rational_inputs_are_recomputed(self):
        module = self.load_module()
        summary = module.analyze()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual(sum(len(fold["point_results"]) for fold in summary["folds"]), 25)
        for fold, old in zip(summary["folds"], candidate["folds"]):
            self.assertEqual([point["x"] for point in fold["point_results"]], protocol["fold_rule"]["assignments"][str(fold["fold"])])
            self.assertEqual(fold["rational_candidate_test_metrics"], old["test_metrics"])
            self.assertEqual(fold["cubic_baseline_test_metrics"], old["baseline_test_metrics"])
            for point, old_point in zip(fold["point_results"], old["point_results"]):
                self.assertEqual(point["observed_y"], old_point["observed_y"])
                self.assertEqual(point["rational_snapshot_prediction"], old_point["snapshot_prediction"])
                self.assertEqual(point["rational_absolute_residual"], old_point["actual_absolute_residual"])
                if fold["optimizer_success"]:
                    self.assertTrue(math.isfinite(point["native_prediction"]))
                    self.assertAlmostEqual(point["native_absolute_residual"], abs(point["observed_y"] - point["native_prediction"]), places=14)
            if fold["optimizer_success"]:
                residuals = np.array([point["observed_y"] - point["native_prediction"] for point in fold["point_results"]])
                metrics = fold["native_test_metrics"]
                self.assertAlmostEqual(metrics["rmse"], float(np.sqrt(np.mean(residuals ** 2))), places=14)
                self.assertAlmostEqual(metrics["mae"], float(np.mean(np.abs(residuals))), places=14)
                self.assertAlmostEqual(metrics["max_absolute_residual"], float(np.max(np.abs(residuals))), places=14)
            else:
                self.assertIsNone(fold["native_test_metrics"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_native_bounds_are_not_transferred_and_final_outputs_are_real(self):
        module = self.load_module()
        summary = module.analyze()
        for key in ["native_physical_law_validated", "native_probability_calibration_claimed", "native_deterministic_bounds_claimed", "rational_bounds_transferred_to_native", "independent_physical_experiment_claimed", "certified_full_fit_used_as_holdout", "failed_fits_hidden"]:
            self.assertFalse(summary["decision"][key], key)
        self.assertEqual(summary["totals"]["native_optimizer_failure_count"], sum(not fold["optimizer_success"] for fold in summary["folds"]))
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(summary, stored)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

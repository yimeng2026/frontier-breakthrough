import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_enso_native_holdout.py"
PROTOCOL = ROOT / "validation/enso-native-holdout-protocol.json"
CANDIDATE = ROOT / "validation/enso-ellipsoid-coverage.json"


class EnsoNativeHoldoutTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native ENSO analysis: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_enso_native_holdout", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_native_fourier_formula_and_zero_periods(self):
        module = self.load_module()
        p = (10.0, 3.0, 0.5, 44.0, -1.5, 0.5, 26.0, -0.1, 1.5)
        x = np.array([1.0, 12.0, 60.0])
        expected = p[0] + p[1]*np.cos(2*np.pi*x/12) + p[2]*np.sin(2*np.pi*x/12) + p[4]*np.cos(2*np.pi*x/p[3]) + p[5]*np.sin(2*np.pi*x/p[3]) + p[7]*np.cos(2*np.pi*x/p[6]) + p[8]*np.sin(2*np.pi*x/p[6])
        np.testing.assert_allclose(module.native_model(x, *p), expected, rtol=0, atol=1e-14)
        self.assertTrue(np.isnan(module.native_model(x, *p[:3], 0.0, *p[4:])[0]))
        self.assertTrue(np.isnan(module.native_model(x, *p[:6], 0.0, *p[7:])[0]))

    def test_known_answer_reproduction_is_not_holdout_evidence(self):
        module = self.load_module()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        known = module.analyze()["known_answer"]
        self.assertTrue(known["optimizer_success"])
        self.assertFalse(known["within_certified_tolerances"])
        self.assertFalse(known["parameter_checks_passed"])
        self.assertFalse(known["rss_check_passed"])
        self.assertEqual(known["evidence_class"], "known_answer_reproduction_not_holdout")
        self.assertTrue(known["certified_forward_rss_check_passed"])
        self.assertAlmostEqual(known["certified_forward_rss"], protocol["known_answer_rule"]["certified_rss"], delta=protocol["known_answer_rule"]["rss_absolute_tolerance"])
        self.assertEqual(known["certified_forward_evidence_class"], "known_answer_forward_evaluation_not_optimizer_or_holdout")
        self.assertFalse(known["original_tolerances_relaxed"])
        self.assertFalse(known["optimizer_mismatch_hidden"])
        self.assertTrue(known["amendment_sha256"])

    def test_five_fold_metrics_and_frozen_rational_inputs_are_recomputed(self):
        module = self.load_module()
        summary = module.analyze()
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual([len(fold["point_results"]) for fold in summary["folds"]], [34, 34, 34, 33, 33])
        self.assertEqual(sum(len(fold["point_results"]) for fold in summary["folds"]), 168)
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

    def test_native_bounds_are_not_transferred_and_final_outputs_are_real(self):
        module = self.load_module()
        summary = module.analyze()
        for key in ["native_physical_law_validated", "native_probability_calibration_claimed", "native_deterministic_bounds_claimed", "rational_bounds_transferred_to_native", "independent_physical_experiment_claimed", "certified_full_fit_used_as_holdout", "failed_fits_hidden"]:
            self.assertFalse(summary["decision"][key], key)
        self.assertEqual(summary["totals"]["native_optimizer_failure_count"], sum(not fold["optimizer_success"] for fold in summary["folds"]))
        self.assertEqual(set(summary["parameter_stability"]), {f"b{index}" for index in range(1, 10)})
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(summary, stored)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

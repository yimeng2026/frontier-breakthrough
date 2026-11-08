import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_roszman1_native_identifiability.py"
SOURCE = ROOT / "validation/roszman1-native-holdout.json"


class Roszman1NativeIdentifiabilityTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native identifiability analysis: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_roszman1_native_identifiability", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_analytic_jacobian_matches_central_difference(self):
        module = self.load_module()
        parameters = {"b1": 0.2, "b2": -0.000005, "b3": 1200.0, "b4": -150.0}
        x = np.array([-1000.0, -500.0, -200.0])
        analytic = module.native_jacobian(x, parameters)
        numeric = np.empty_like(analytic)
        for index, name in enumerate(["b1", "b2", "b3", "b4"]):
            step = 1.0e-5 * max(1.0, abs(parameters[name]))
            upper = dict(parameters)
            lower = dict(parameters)
            upper[name] += step
            lower[name] -= step
            numeric[:, index] = (module.native_model(x, *list(upper.values())) - module.native_model(x, *list(lower.values()))) / (2 * step)
        np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=1.0e-8)

    def test_frozen_fits_and_local_diagnostics_are_reproduced_without_refitting(self):
        module = self.load_module()
        summary = module.analyze()
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        self.assertTrue(summary["analysis_scope"]["post_hoc"])
        self.assertFalse(summary["analysis_scope"]["refit"])
        self.assertEqual(len(summary["folds"]), 5)
        for fold, frozen in zip(summary["folds"], source["folds"]):
            self.assertEqual(fold["train_count"], 20)
            self.assertEqual(fold["test_count"], 5)
            self.assertEqual(fold["native_parameters"], frozen["native_parameters"])
            self.assertEqual(fold["test_metrics"], frozen["native_test_metrics"])
            self.assertEqual(fold["training_jacobian"]["shape"], [20, 4])
            self.assertGreaterEqual(fold["training_jacobian"]["numerical_rank"], 1)
            self.assertLessEqual(fold["training_jacobian"]["numerical_rank"], 4)
            self.assertGreaterEqual(fold["training_jacobian"]["scaled_condition_number"], 1.0)
            self.assertTrue(np.isfinite(fold["training_jacobian"]["scaled_condition_number"]))
            self.assertGreaterEqual(fold["held_out_prediction_sensitivity"]["max_local_standard_deviation"], 0.0)
            self.assertEqual(len(fold["held_out_points"]), 5)
            for point, old_point in zip(fold["held_out_points"], frozen["point_results"]):
                self.assertEqual(point["x"], old_point["x"])
                self.assertEqual(point["native_prediction"], old_point["native_prediction"])
                self.assertGreaterEqual(point["local_linearized_prediction_standard_deviation"], 0.0)
        self.assertEqual(summary["totals"]["full_numerical_rank_fold_count"], sum(fold["training_jacobian"]["numerical_rank"] == 4 for fold in summary["folds"]))
        self.assertEqual(module.validate_summary(summary), [])
        for key in ["global_structural_identifiability_proved", "physical_parameter_endogeneity_proved", "calibrated_prediction_intervals_produced", "rational_bounds_transferred_to_native", "prediction_stability_equals_parameter_uniqueness"]:
            self.assertFalse(summary["decision"][key], key)

    def test_parameter_ranges_and_final_outputs_are_real(self):
        module = self.load_module()
        summary = module.analyze()
        self.assertEqual(set(summary["parameter_stability"]), {"b1", "b2", "b3", "b4"})
        for name, record in summary["parameter_stability"].items():
            values = [fold["native_parameters"][name] for fold in summary["folds"]]
            self.assertEqual(record["minimum"], min(values))
            self.assertEqual(record["maximum"], max(values))
            self.assertEqual(record["median"], float(np.median(values)))
            self.assertEqual(record["range"], max(values) - min(values))
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(summary, stored)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

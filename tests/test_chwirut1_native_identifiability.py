import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_chwirut1_native_identifiability import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    native_jacobian,
    native_model,
    render_figure,
    validate_summary,
)

SOURCE = ROOT / "validation/chwirut1-native-holdout.json"


class Chwirut1NativeIdentifiabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_analytic_jacobian_matches_central_difference(self):
        parameters = {"b1": 0.19, "b2": 0.006, "b3": 0.0105}
        x = np.array([0.5, 1.5, 4.0])
        analytic = native_jacobian(x, parameters)
        numeric = np.empty_like(analytic)
        for index, name in enumerate(["b1", "b2", "b3"]):
            step = 1.0e-6 * max(1.0e-3, abs(parameters[name]))
            upper = dict(parameters)
            lower = dict(parameters)
            upper[name] += step
            lower[name] -= step
            numeric[:, index] = (
                native_model(x, *list(upper.values())) - native_model(x, *list(lower.values()))
            ) / (2 * step)
        np.testing.assert_allclose(analytic, numeric, rtol=2.0e-6, atol=2.0e-8)

    def test_frozen_fits_fold_designs_and_degrees_of_freedom_are_reproduced(self):
        self.assertEqual(len(self.summary["folds"]), 5)
        self.assertEqual(self.protocol["fold_rule"]["residual_degrees_of_freedom_per_fold"], [154, 157, 160, 188, 182])
        for fold, frozen in zip(self.summary["folds"], self.source["folds"]):
            number = fold["fold"]
            self.assertEqual(fold["train_count"], self.protocol["fold_rule"]["train_points_per_fold"][number - 1])
            self.assertEqual(fold["test_count"], self.protocol["fold_rule"]["test_points_per_fold"][number - 1])
            self.assertEqual(fold["train_unique_distance_count"], self.protocol["fold_rule"]["train_unique_distances_per_fold"][number - 1])
            self.assertEqual(fold["native_parameters"], frozen["native_parameters"])
            self.assertEqual(fold["test_metrics"], frozen["native_test_metrics"])
            self.assertTrue(math.isclose(fold["training_rss"], frozen["training_rss"], rel_tol=1e-9, abs_tol=1e-12))
            jacobian = fold["training_jacobian"]
            self.assertEqual(jacobian["shape"], [fold["train_count"], 3])
            self.assertGreaterEqual(jacobian["numerical_rank"], 1)
            self.assertLessEqual(jacobian["numerical_rank"], 3)
            self.assertGreaterEqual(jacobian["scaled_condition_number"], 1.0)
            self.assertTrue(math.isfinite(jacobian["scaled_condition_number"]))
            expected_sigma2 = fold["training_rss"] / (fold["train_count"] - 3)
            self.assertTrue(math.isclose(jacobian["training_residual_variance_estimate"], expected_sigma2, rel_tol=1e-12, abs_tol=1e-12))
            self.assertEqual(len(fold["held_out_points"]), fold["test_count"])
            for point, old_point in zip(fold["held_out_points"], frozen["point_results"]):
                self.assertEqual(point["x"], old_point["x"])
                self.assertEqual(point["native_prediction"], old_point["native_prediction"])
                self.assertGreaterEqual(point["local_linearized_prediction_standard_deviation"], 0.0)
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertTrue(self.summary["analysis_scope"]["analytic_jacobian"])

    def test_denominator_pole_and_local_diagnostic_counts_are_explicit(self):
        for fold in self.summary["folds"]:
            denominator = fold["denominator_diagnostics"]
            self.assertGreater(denominator["minimum_absolute_denominator_train"], 0)
            self.assertGreater(denominator["minimum_absolute_denominator_held_out"], 0)
            self.assertGreater(denominator["minimum_absolute_denominator_all"], 0)
            self.assertTrue(math.isfinite(denominator["pole_x"]))
            self.assertIsInstance(denominator["pole_inside_observed_closed_range"], bool)
            self.assertFalse(denominator["singular_evaluation_hidden"])
        totals = self.summary["totals"]
        self.assertEqual(totals["full_numerical_rank_fold_count"], sum(fold["training_jacobian"]["numerical_rank"] == 3 for fold in self.summary["folds"]))
        self.assertEqual(totals["local_diagnostic_failure_count"], sum(not fold["training_jacobian"]["local_covariance_valid"] for fold in self.summary["folds"]))
        self.assertEqual(totals["pole_inside_observed_range_fold_count"], sum(fold["denominator_diagnostics"]["pole_inside_observed_closed_range"] for fold in self.summary["folds"]))
        self.assertEqual(validate_summary(self.summary), [])

    def test_parameter_ranges_and_no_overclaim(self):
        self.assertEqual(set(self.summary["parameter_stability"]), {"b1", "b2", "b3"})
        for name, record in self.summary["parameter_stability"].items():
            values = [fold["native_parameters"][name] for fold in self.summary["folds"]]
            self.assertEqual(record["minimum"], min(values))
            self.assertEqual(record["maximum"], max(values))
            self.assertEqual(record["median"], float(np.median(values)))
            self.assertEqual(record["range"], max(values) - min(values))
        for key in ["global_structural_identifiability_proved", "physical_parameter_endogeneity_proved", "calibrated_prediction_intervals_produced", "rational_bounds_transferred_to_native", "prediction_stability_equals_parameter_uniqueness", "independent_model_family_claimed", "native_deterministic_bounds_claimed"]:
            self.assertFalse(self.summary["decision"][key], key)

    def test_validator_rejects_frozen_fit_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["native_parameters"]["b2"] = -1
        self.assertTrue(any("frozen fit" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["global_structural_identifiability_proved"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))

    def test_input_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed = copy.deepcopy(self.protocol)
            changed["inputs"]["native_holdout"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                analyze(path)

    def test_figure_and_stored_output_are_real(self):
        stored = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(self.summary, stored)
        self.assertTrue(FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            render_figure(self.summary, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(output.stat().st_size, 40000)


if __name__ == "__main__":
    unittest.main()

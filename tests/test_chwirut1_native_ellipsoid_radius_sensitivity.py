import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_chwirut1_native_ellipsoid_radius_sensitivity import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    critical_radius,
    denominator_bounds,
    prediction_envelope,
    render_figure,
    validate_summary,
)


class Chwirut1NativeEllipsoidRadiusSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_critical_radius_and_strict_negative_control(self):
        parameters = {"b1": 0.2, "b2": 0.01, "b3": 0.02}
        covariance = [[0.0001, 0.0, 0.0], [0.0, 0.000001, 0.0], [0.0, 0.0, 0.000001]]
        result = critical_radius(parameters, covariance, 0.5, 2.0)
        expected_left = 0.02 / (0.001 * math.sqrt(1.25))
        expected_right = 0.05 / (0.001 * math.sqrt(5.0))
        self.assertTrue(math.isclose(result["left_radius"], expected_left, rel_tol=1e-10, abs_tol=1e-12))
        self.assertTrue(math.isclose(result["right_radius"], expected_right, rel_tol=1e-10, abs_tol=1e-12))
        self.assertEqual(result["radius"], result["left_radius"])
        self.assertEqual(result["limiting_endpoint"], "left")
        self.assertTrue(denominator_bounds(parameters, covariance, result["radius"] / 2, 0.5, 2.0)["positive_certified"])
        self.assertFalse(denominator_bounds(parameters, covariance, result["radius"], 0.5, 2.0)["positive_certified"])
        with self.assertRaisesRegex(ValueError, "denominator positivity"):
            prediction_envelope(parameters, covariance, result["radius"], 0.5)
        with self.assertRaisesRegex(ValueError, "No positive denominator-safe radius"):
            critical_radius({"b1": 0.2, "b2": -0.01, "b3": 0.02}, covariance, 0.5, 2.0)

    def test_structure_grid_and_baseline_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["radius_count"], 5)
        self.assertEqual(totals["case_count"], 25)
        self.assertEqual(totals["held_out_point_count_per_case"], 214)
        self.assertEqual(totals["unique_distance_count"], 22)
        self.assertEqual(totals["maximum_point_evaluations"], 1070)
        self.assertEqual(totals["maximum_envelope_evaluations"], 110)
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        baseline = self.summary["baseline"]
        self.assertTrue(baseline["matches_frozen_baseline"])
        self.assertEqual(baseline["certified_fold_count"], 5)
        self.assertEqual(baseline["available_point_count"], 214)
        self.assertEqual(baseline["covered_point_count"], 214)
        self.assertEqual(baseline["violation_point_count"], 0)
        self.assertEqual(baseline["unavailable_point_count"], 0)
        self.assertAlmostEqual(baseline["max_envelope_width"], 170.14630922307612)
        self.assertAlmostEqual(baseline["median_envelope_width"], 19.222110234669167)
        self.assertAlmostEqual(baseline["max_residual_upper_bound"], 165.679601537622)
        self.assertAlmostEqual(baseline["median_residual_upper_bound"], 15.050994997990879)

    def test_every_case_matches_analytic_radius_and_accounts_for_points(self):
        for fold in self.summary["folds"]:
            critical = fold["critical"]["radius"]
            self.assertGreater(critical, 0)
            self.assertTrue(fold["negative_control"]["half_radius_accepted"])
            self.assertTrue(fold["negative_control"]["exact_radius_rejected"])
            for case in fold["cases"]:
                below = case["radius"] < critical
                self.assertEqual(case["analytic_relation"], "below_critical" if below else "at_or_above_critical")
                self.assertEqual(case["prediction_envelope_available"], below)
                coverage = case["coverage"]
                self.assertEqual(coverage["available_point_count"] + coverage["unavailable_point_count"], len(case["points"]))
                self.assertEqual(coverage["covered_point_count"] + coverage["violation_point_count"], coverage["available_point_count"])
                self.assertEqual(coverage["center_prediction_envelope_mismatch_count"], 0)
                if below:
                    self.assertGreater(case["continuous_denominator"]["minimum"], 0)
                    self.assertEqual(len(case["envelopes"]), len({point["x"] for point in case["points"]}))
                    for point in case["points"]:
                        self.assertLessEqual(point["prediction_minimum"], point["native_prediction"])
                        self.assertLessEqual(point["native_prediction"], point["prediction_maximum"])
                        self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
                        self.assertTrue(point["covered"])
                else:
                    self.assertEqual(case["envelopes"], [])
                    for point in case["points"]:
                        self.assertIsNone(point["residual_upper_bound"])
                        self.assertIsNone(point["covered"])

    def test_no_probability_or_radius_optimization_claim(self):
        for key in ["probability_region_claimed", "optimal_radius_selected", "critical_radius_is_confidence_level", "critical_radius_is_universal_maximum", "grid_maximum_called_exact_safe_maximum", "exact_critical_radius_accepted", "unavailable_cases_given_bounds", "center_consistency_used_as_external_validation", "exact_rational_certificate_claimed", "independent_model_family_claimed", "failed_cases_hidden"]:
            self.assertFalse(self.summary["decision"][key], key)

    def test_validator_rejects_critical_radius_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["critical"]["radius"] = 1
        self.assertTrue(any("critical" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["optimal_radius_selected"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))

    def test_input_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed = copy.deepcopy(self.protocol)
            changed["inputs"]["native_identifiability"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                analyze(path)

    def test_stored_output_and_figure_are_real(self):
        stored = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(self.summary, stored)
        self.assertTrue(FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            render_figure(self.summary, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(output.stat().st_size, 50000)


if __name__ == "__main__":
    unittest.main()

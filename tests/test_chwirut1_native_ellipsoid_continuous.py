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
from analyze_chwirut1_native_ellipsoid_continuous import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    denominator_bounds,
    prediction_envelope,
    render_figure,
    support_value,
    validate_summary,
)


class Chwirut1NativeEllipsoidContinuousTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_support_identity(self):
        covariance = [[4.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        value = support_value(covariance, [0.0, 1.0, 2.0], 2.0)
        self.assertTrue(math.isclose(float(value), 2 * math.sqrt(5), rel_tol=1e-12, abs_tol=1e-12))

    def test_endpoint_concavity_and_nonpositive_matrix_rejection(self):
        parameters = {"b1": 0.2, "b2": 0.01, "b3": 0.02}
        covariance = [[0.0001, 0.0, 0.0], [0.0, 0.000001, 0.0], [0.0, 0.0, 0.000001]]
        result = denominator_bounds(parameters, covariance, 1.0, 0.5, 2.0)
        self.assertTrue(result["positive_certified"])
        self.assertEqual(result["concavity_rule"], "d_min concave; d_max convex; endpoint extrema")
        grid = np.linspace(0.5, 2.0, 1001)
        minimum = float("inf")
        maximum = -float("inf")
        for x in grid:
            point = denominator_bounds(parameters, covariance, 1.0, float(x), float(x))
            minimum = min(minimum, point["minimum"])
            maximum = max(maximum, point["maximum"])
        self.assertLessEqual(result["minimum"], minimum)
        self.assertGreaterEqual(result["maximum"], maximum)
        with self.assertRaisesRegex(ValueError, "positive definite"):
            denominator_bounds(parameters, [[0.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]], 1.0, 0.5, 2.0)

    def test_sign_failure_does_not_generate_prediction_envelope(self):
        parameters = {"b1": 0.2, "b2": 0.001, "b3": 0.0}
        covariance = [[0.0001, 0.0, 0.0], [0.0, 0.000001, 0.0], [0.0, 0.0, 0.000001]]
        result = denominator_bounds(parameters, covariance, 10.0, 0.5, 1.0)
        self.assertFalse(result["positive_certified"])
        self.assertIn("cannot be certified", result["unavailable_reason"])
        with self.assertRaisesRegex(ValueError, "denominator positivity"):
            prediction_envelope(parameters, covariance, 10.0, 0.5)

    def test_all_folds_points_and_envelopes_are_accounted_for(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 214)
        self.assertEqual(totals["unique_distance_count"], 22)
        self.assertEqual(totals["available_point_count"] + totals["unavailable_point_count"], 214)
        self.assertEqual(totals["covered_point_count"] + totals["violation_point_count"], totals["available_point_count"])
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        for fold in self.summary["folds"]:
            available = fold["prediction_envelope_available"]
            self.assertEqual(available, fold["continuous_denominator"]["positive_certified"])
            if available:
                self.assertGreater(fold["continuous_denominator"]["minimum"], 0)
            else:
                self.assertTrue(fold["continuous_denominator"]["unavailable_reason"])
            for point in fold["points"]:
                if available:
                    self.assertLessEqual(point["prediction_minimum"], point["native_prediction"])
                    self.assertLessEqual(point["native_prediction"], point["prediction_maximum"])
                    self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
                    self.assertTrue(point["covered"])
                    self.assertGreaterEqual(point["envelope_width"], 0)
                else:
                    for key in ["prediction_minimum", "prediction_maximum", "residual_upper_bound", "covered", "envelope_width"]:
                        self.assertIsNone(point[key])
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["probability_region"])

    def test_no_probability_or_uncertified_bound_claim(self):
        for key in ["probability_region_claimed", "confidence_interval_claimed", "exact_rational_certificate_claimed", "all_parameters_or_all_x_certified", "uncertified_folds_given_bounds", "actual_coverage_used_as_probability", "center_consistency_used_as_external_validation", "independent_model_family_claimed", "failed_folds_hidden"]:
            self.assertFalse(self.summary["decision"][key], key)

    def test_validator_rejects_bound_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["decision"]["uncertified_folds_given_bounds"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        available = next(fold for fold in changed["folds"] if fold["prediction_envelope_available"])
        available["points"][0]["residual_upper_bound"] = -1
        self.assertTrue(any("bound" in error.lower() for error in validate_summary(changed)))

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

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_native_ellipsoid_continuous import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    critical_sign_radius,
    prediction_envelope,
    render_figure,
    sign_bounds,
    support_value,
    validate_summary,
)


class Roszman1NativeEllipsoidContinuousTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_support_identity_four_parameters(self):
        covariance = [[4.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        value = support_value(covariance, [0.0, 0.0, 0.0, 2.0], 2.0)
        self.assertTrue(math.isclose(float(value), 4.0, rel_tol=1e-12, abs_tol=1e-12))

    def test_sign_certificate_and_strict_critical_radius(self):
        parameters = {"b1": 0.2, "b2": -0.000005, "b3": 1200.0, "b4": -100.0}
        covariance = [[0.0001, 0.0, 0.0, 0.0], [0.0, 0.0001, 0.0, 0.0], [0.0, 0.0, 0.0001, 0.0], [0.0, 0.0, 0.0, 1.0]]
        critical = critical_sign_radius(parameters, covariance, -120.0, -110.0)
        self.assertTrue(math.isclose(critical["radius"], 10.0, rel_tol=1e-10, abs_tol=1e-12))
        self.assertEqual(critical["limiting_endpoint"], "right")
        self.assertTrue(sign_bounds(parameters, covariance, critical["radius"] / 2, -120.0, -110.0)["nonzero_certified"])
        self.assertFalse(sign_bounds(parameters, covariance, critical["radius"], -120.0, -110.0)["nonzero_certified"])
        with self.assertRaisesRegex(ValueError, "nonzero sign"):
            prediction_envelope(parameters, covariance, critical["radius"], -110.0)
        with self.assertRaisesRegex(ValueError, "same sign"):
            critical_sign_radius({"b1": 0.2, "b2": -0.000005, "b3": 1200.0, "b4": -110.0}, covariance, -120.0, -100.0)

    def test_prediction_envelope_contains_center(self):
        parameters = {"b1": 0.2, "b2": -0.000005, "b3": 1200.0, "b4": -100.0}
        covariance = [[0.0001, 0.0, 0.0, 0.0], [0.0, 0.0001, 0.0, 0.0], [0.0, 0.0, 0.0001, 0.0], [0.0, 0.0, 0.0, 1.0]]
        x = -115.0
        envelope = prediction_envelope(parameters, covariance, 1.0, x)
        center = parameters["b1"] - parameters["b2"] * x - math.atan(parameters["b3"] / (x - parameters["b4"])) / math.pi
        self.assertLessEqual(envelope["prediction_minimum"], center)
        self.assertLessEqual(center, envelope["prediction_maximum"])
        self.assertLessEqual(envelope["argument_minimum"], envelope["argument_maximum"])

    def test_all_folds_points_and_envelopes_are_accounted_for(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["unique_x_count"], 25)
        self.assertEqual(totals["available_point_count"] + totals["unavailable_point_count"], 25)
        self.assertEqual(totals["covered_point_count"] + totals["violation_point_count"], totals["available_point_count"])
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        for fold in self.summary["folds"]:
            self.assertTrue(fold["negative_control"]["half_radius_accepted"])
            self.assertTrue(fold["negative_control"]["exact_radius_rejected"])
            self.assertEqual(fold["prediction_envelope_available"], fold["sign_certificate"]["nonzero_certified"])
            for point in fold["points"]:
                if fold["prediction_envelope_available"]:
                    self.assertLessEqual(point["prediction_minimum"], point["native_prediction"])
                    self.assertLessEqual(point["native_prediction"], point["prediction_maximum"])
                    self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
                    self.assertTrue(point["covered"])
                else:
                    for key in ["prediction_minimum", "prediction_maximum", "residual_upper_bound", "covered", "envelope_width"]:
                        self.assertIsNone(point[key])
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["probability_region"])

    def test_no_probability_or_uncertified_bound_claim(self):
        for key in ["probability_region_claimed", "confidence_interval_claimed", "exact_rational_certificate_claimed", "all_parameters_or_all_x_certified", "uncertified_folds_given_bounds", "actual_coverage_used_as_probability", "center_consistency_used_as_external_validation", "independent_physical_experiment_claimed", "failed_folds_hidden"]:
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

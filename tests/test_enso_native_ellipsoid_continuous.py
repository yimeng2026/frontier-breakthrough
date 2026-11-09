import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_enso_native_ellipsoid_continuous import (  # noqa: E402
    FIGURE,
    OUT,
    PARAMETER_NAMES,
    PROTOCOL,
    analyze,
    critical_period_radius,
    period_certificate,
    prediction_envelope,
    render_figure,
    support_value,
    validate_summary,
)


class EnsoNativeEllipsoidContinuousTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()
        cls.parameters = {name: value for name, value in zip(
            PARAMETER_NAMES,
            [10.5, 3.0, 0.5, 44.0, -1.5, 0.5, 26.0, 0.2, 1.5],
        )}
        cls.covariance = [[0.0001 if i == j else 0.0 for j in range(9)] for i in range(9)]

    def test_support_identity_nine_parameters(self):
        covariance = [[1.0 if i == j else 0.0 for j in range(9)] for i in range(9)]
        value = support_value(covariance, [0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0], 2.0)
        self.assertTrue(math.isclose(float(value), 4.0, rel_tol=1e-12, abs_tol=1e-12))

    def test_positive_period_certificate_and_strict_critical_radius(self):
        critical = critical_period_radius(self.parameters, self.covariance)
        self.assertTrue(math.isclose(critical["b4_radius"], 4400.0, rel_tol=1e-10, abs_tol=1e-6))
        self.assertTrue(math.isclose(critical["b7_radius"], 2600.0, rel_tol=1e-10, abs_tol=1e-6))
        self.assertEqual(critical["limiting_parameter"], "b7")
        self.assertTrue(period_certificate(self.parameters, self.covariance, critical["radius"] / 2)["positive_certified"])
        self.assertFalse(period_certificate(self.parameters, self.covariance, critical["radius"])["positive_certified"])
        with self.assertRaisesRegex(ValueError, "positive periods"):
            prediction_envelope(self.parameters, self.covariance, critical["radius"], 1.0)
        changed = dict(self.parameters)
        changed["b4"] = -1.0
        with self.assertRaisesRegex(ValueError, "positive"):
            critical_period_radius(changed, self.covariance)

    def test_prediction_envelope_contains_center_at_multiple_months(self):
        for x in [1.0, 12.0, 60.0]:
            envelope = prediction_envelope(self.parameters, self.covariance, 1.0, x)
            p = self.parameters
            center = (
                p["b1"] + p["b2"] * math.cos(2 * math.pi * x / 12) + p["b3"] * math.sin(2 * math.pi * x / 12)
                + p["b5"] * math.cos(2 * math.pi * x / p["b4"]) + p["b6"] * math.sin(2 * math.pi * x / p["b4"])
                + p["b8"] * math.cos(2 * math.pi * x / p["b7"]) + p["b9"] * math.sin(2 * math.pi * x / p["b7"])
            )
            self.assertLessEqual(envelope["prediction_minimum"], center)
            self.assertLessEqual(center, envelope["prediction_maximum"])
            self.assertEqual(len(envelope["terms"]), 6)
            for term in envelope["terms"]:
                self.assertLessEqual(term["minimum"], term["maximum"])

    def test_all_folds_points_and_envelopes_are_accounted_for(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 168)
        self.assertEqual(totals["unique_month_count"], 168)
        self.assertEqual(totals["available_point_count"] + totals["unavailable_point_count"], 168)
        self.assertEqual(totals["covered_point_count"] + totals["violation_point_count"], totals["available_point_count"])
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        for fold in self.summary["folds"]:
            self.assertTrue(fold["negative_control"]["half_radius_accepted"])
            self.assertTrue(fold["negative_control"]["exact_radius_rejected"])
            self.assertEqual(fold["prediction_envelope_available"], fold["period_certificate"]["positive_certified"])
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
        for key in ["probability_region_claimed", "confidence_interval_claimed", "new_physical_periods_proved", "exact_rational_certificate_claimed", "all_parameters_or_all_x_certified", "uncertified_folds_given_bounds", "actual_coverage_used_as_probability", "center_consistency_used_as_external_validation", "independent_physical_experiment_claimed", "failed_folds_hidden"]:
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

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_enso_native_ellipsoid_radius_sensitivity import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    critical_period_radius,
    period_certificate,
    prediction_envelope,
    render_figure,
    validate_summary,
)


class EnsoNativeEllipsoidRadiusSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_period_critical_radius_and_strict_negative_control(self):
        parameters = {"b4": 40, "b7": 20}
        covariance = [[0.0] * 9 for _ in range(9)]
        for index in range(9):
            covariance[index][index] = 0.01
        covariance[3][3] = 0.25
        covariance[6][6] = 0.04
        result = critical_period_radius(parameters, covariance)
        self.assertTrue(math.isclose(result["b4_radius"], 80, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["b7_radius"], 100, rel_tol=1e-12))
        self.assertEqual(result["limiting_parameter"], "b4")
        self.assertTrue(period_certificate(parameters, covariance, result["radius"] / 2)["positive_certified"])
        self.assertFalse(period_certificate(parameters, covariance, result["radius"])["positive_certified"])
        with self.assertRaisesRegex(ValueError, "positive periods"):
            prediction_envelope(parameters, covariance, result["radius"], 1)

    def test_structure_counts_and_unavailable_cases_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["radius_count"], 6)
        self.assertEqual(totals["case_count"], 30)
        self.assertEqual(totals["held_out_point_count_per_radius"], 168)
        self.assertEqual(totals["fold_held_out_point_counts"], [34, 34, 34, 33, 33])
        self.assertEqual(totals["maximum_point_evaluations"], 1008)
        self.assertEqual(totals["maximum_envelope_evaluations"], 1008)
        self.assertEqual(totals["actual_envelope_evaluation_count"], 942)
        self.assertEqual(totals["available_point_count"], 942)
        self.assertEqual(totals["covered_point_count"], 942)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertEqual(totals["unavailable_point_count"], 66)
        self.assertEqual(totals["unavailable_case_ids"], ["enso:4:r32", "enso:5:r32"])
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        self.assertAlmostEqual(totals["minimum_critical_period_radius"], 26.76683884611663)
        self.assertEqual(totals["minimum_critical_period_radius_fold"], 4)
        self.assertEqual(totals["minimum_critical_period_parameter"], "b4")
        self.assertEqual([fold["max_certified_grid_radius"] for fold in self.summary["folds"]], [32, 32, 32, 16, 16])

    def test_every_case_matches_analytic_radius_and_accounts_for_points(self):
        for fold in self.summary["folds"]:
            critical = fold["critical_period"]["radius"]
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
                    self.assertGreater(case["period_certificate"]["b4_minimum"], 0)
                    self.assertGreater(case["period_certificate"]["b7_minimum"], 0)
                    self.assertEqual(len(case["envelopes"]), len({point["x"] for point in case["points"]}))
                    for point in case["points"]:
                        self.assertLessEqual(point["prediction_minimum"], point["native_prediction"])
                        self.assertLessEqual(point["native_prediction"], point["prediction_maximum"])
                        self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
                        self.assertTrue(point["covered"])
                else:
                    self.assertEqual(case["envelopes"], [])
                    self.assertIsNone(case["max_envelope_width"])
                    for point in case["points"]:
                        self.assertIsNone(point["residual_upper_bound"])
                        self.assertIsNone(point["covered"])

    def test_radius4_baseline_matches_every_frozen_fold_and_total(self):
        baseline = self.summary["baseline"]
        self.assertTrue(baseline["matches_frozen_baseline"])
        self.assertEqual(baseline["exact_fold_projection_match_count"], 5)
        self.assertEqual(baseline["certified_fold_count"], 5)
        self.assertEqual(baseline["available_point_count"], 168)
        self.assertEqual(baseline["covered_point_count"], 168)
        self.assertEqual(baseline["violation_point_count"], 0)
        self.assertEqual(baseline["unavailable_point_count"], 0)
        self.assertAlmostEqual(baseline["max_envelope_width"], 17.64192935677042)
        self.assertAlmostEqual(baseline["median_envelope_width"], 13.164436414771593)
        self.assertAlmostEqual(baseline["max_residual_upper_bound"], 14.576765863967406)
        self.assertAlmostEqual(baseline["median_residual_upper_bound"], 8.516811559710845)

    def test_no_probability_radius_optimization_or_physical_period_claim(self):
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.summary["analysis_scope"]["prospective_independent_validation"])
        self.assertFalse(self.summary["analysis_scope"]["joint_nonlinear_optimum_claimed"])

    def test_validator_rejects_critical_radius_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["critical_period"]["radius"] = 1
        self.assertTrue(any("critical" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["optimal_radius_selected"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["native_identifiability"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed_protocol), encoding="utf-8")
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

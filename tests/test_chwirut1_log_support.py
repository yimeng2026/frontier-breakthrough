import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_chwirut1_log_support import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    intersect_bounds,
    log_support_envelope,
    render_figure,
    secant_parameters,
    support_candidates,
    tangent_parameters,
    validate_summary,
)
from analyze_chwirut1_native_ellipsoid_continuous import prediction_envelope


class Chwirut1LogSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 0.1, "b2": 1.0, "b3": 0.1}

    @staticmethod
    def toy_covariance():
        return [[0.01, 0.0, 0.0], [0.0, 1.0e-24, 0.0], [0.0, 0.0, 1.0e-24]]

    def test_secant_and_tangent_enclose_concave_log(self):
        slope, intercept = secant_parameters(1, 2)
        midpoint = 1.5
        secant_value = slope * midpoint + intercept
        self.assertLessEqual(secant_value, math.log(midpoint))
        for point in [1, 1.5, 2]:
            tangent_slope, tangent_intercept = tangent_parameters(point)
            tangent_value = tangent_slope * midpoint + tangent_intercept
            self.assertGreaterEqual(tangent_value, math.log(midpoint) - 1.0e-12)

    def test_fixed_denominator_recovers_original_exponential_interval(self):
        parameters = self.toy_parameters()
        covariance = self.toy_covariance()
        independent = prediction_envelope(parameters, covariance, 1, 1)
        result = log_support_envelope(parameters, covariance, 1, 1, independent)
        expected_minimum = math.exp(-0.2) / 1.1
        expected_maximum = 1 / 1.1
        self.assertTrue(math.isclose(result["prediction_minimum"], expected_minimum, rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_maximum"], expected_maximum, rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_minimum"], independent["prediction_minimum"], rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_maximum"], independent["prediction_maximum"], rel_tol=1e-10, abs_tol=1e-10))
        intersection = intersect_bounds(result["prediction_minimum"], result["prediction_maximum"], independent["prediction_minimum"], independent["prediction_maximum"])
        self.assertLessEqual(intersection["prediction_minimum"], intersection["prediction_maximum"])

    def test_support_candidates_are_full_covariance_boundary_points(self):
        candidates = support_candidates(self.toy_parameters(), self.toy_covariance(), 1)
        self.assertEqual(len(candidates), 6)
        self.assertEqual([candidate["direction"] for candidate in candidates], ["b1_minus", "b1_plus", "b2_minus", "b2_plus", "b3_minus", "b3_plus"])
        plus = candidates[1]
        self.assertTrue(math.isclose(plus["parameters"]["b1"], 0.2, rel_tol=1e-12))
        for candidate in candidates:
            self.assertTrue(candidate["feasible"])
            self.assertTrue(math.isclose(candidate["ellipsoid_quadratic"], 1.0, rel_tol=1e-10, abs_tol=1e-10))

    def test_structure_counts_and_receipt_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 214)
        self.assertEqual(totals["unique_distance_count"], 22)
        self.assertEqual(totals["log_alternative_bound_count"], 22)
        self.assertEqual(totals["intersection_bound_count"], 22)
        self.assertEqual(totals["candidate_direction_count"], 30)
        self.assertEqual(totals["candidate_evaluation_count"], 132)
        self.assertEqual(totals["nonempty_intersection_count"], 22)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["covered_point_count"], 214)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertTrue(self.summary["independent_receipt_verified"])

    def test_intersection_never_widens_independent_baseline(self):
        tightened = 0
        unchanged = 0
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                self.assertLessEqual(envelope["independent_minimum"], envelope["intersection_minimum"])
                self.assertLessEqual(envelope["intersection_maximum"], envelope["independent_maximum"])
                self.assertLessEqual(envelope["intersection_minimum"], envelope["intersection_maximum"])
                ratio = envelope["intersection_to_independent_width_ratio"]
                self.assertGreater(ratio, 0)
                self.assertLessEqual(ratio, 1 + 1e-12)
                self.assertGreaterEqual(envelope["intersection_width_reduction"], -1e-10)
                if envelope["intersection_tightened"]:
                    tightened += 1
                else:
                    unchanged += 1
        self.assertEqual(tightened + unchanged, 22)
        self.assertEqual(tightened, self.summary["totals"]["intersection_tightened_count"])
        self.assertEqual(unchanged, self.summary["totals"]["intersection_unchanged_count"])

    def test_all_candidates_and_observations_remain_consistent(self):
        candidate_count = 0
        point_count = 0
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertAlmostEqual(candidate["ellipsoid_quadratic"], 16.0, places=9)
                    self.assertTrue(candidate["denominator_positive"])
                    self.assertTrue(candidate["inside_independent"])
                    self.assertTrue(candidate["inside_log_alternative"])
                    self.assertTrue(candidate["inside_intersection"])
            for point in fold["points"]:
                point_count += 1
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
                self.assertLessEqual(point["intersection_minimum"], point["native_prediction"])
                self.assertLessEqual(point["native_prediction"], point["intersection_maximum"])
                self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
        self.assertEqual(candidate_count, 132)
        self.assertEqual(point_count, 214)

    def test_comparison_and_global_optimum_scope_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["alternative_tighter_count"] + totals["alternative_wider_count"] + totals["alternative_equal_count"], 22)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertIsNone(self.summary["full_nonlinear_global_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["finite_tangent_set_not_global_optimizer"])
        self.assertFalse(self.summary["analysis_scope"]["independent_model_family_replication"])

    def test_validator_rejects_ratio_violation_scope_and_hash_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["intersection_to_independent_width_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["intersection_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["log_alternative_is_global_optimum"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["independent_bounds"]["sha256"] = "0" * 64
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

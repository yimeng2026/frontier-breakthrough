import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_joint_linear_arctan import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    intersect_bounds,
    joint_arctan_envelope,
    joint_linear_support,
    render_figure,
    support_candidates,
    validate_summary,
)
from analyze_roszman1_native_ellipsoid_continuous import prediction_envelope


class Roszman1JointLinearArctanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 1.0, "b2": 0.1, "b3": 100.0, "b4": -1000.0}

    @staticmethod
    def toy_covariance():
        return [[0.01, 0.0, 0.0, 0.0], [0.0, 0.04, 0.0, 0.0], [0.0, 0.0, 0.01, 0.0], [0.0, 0.0, 0.0, 0.01]]

    def test_joint_linear_support_is_inside_independent_corners(self):
        result = joint_linear_support(self.toy_parameters(), self.toy_covariance(), 1, 2)
        self.assertTrue(math.isclose(result["center"], 0.8, rel_tol=1e-12))
        self.assertGreaterEqual(result["minimum"], 0.3 - 1e-10)
        self.assertLessEqual(result["maximum"], 1.3 + 1e-10)
        self.assertLess(result["minimum"], result["center"])
        self.assertGreater(result["maximum"], result["center"])
        self.assertTrue(math.isclose(result["support"], math.sqrt(0.17), rel_tol=1e-10, abs_tol=1e-10))
        baseline = prediction_envelope(self.toy_parameters(), self.toy_covariance(), 1, 2)
        alternative = joint_arctan_envelope(self.toy_parameters(), self.toy_covariance(), 1, 2, baseline)
        self.assertLessEqual(baseline["prediction_minimum"], alternative["prediction_minimum"])
        self.assertLessEqual(alternative["prediction_maximum"], baseline["prediction_maximum"])
        self.assertLessEqual(alternative["prediction_minimum"], alternative["center_prediction"])
        self.assertLessEqual(alternative["center_prediction"], alternative["prediction_maximum"])
        intersection = intersect_bounds(alternative["prediction_minimum"], alternative["prediction_maximum"], baseline["prediction_minimum"], baseline["prediction_maximum"])
        self.assertLessEqual(intersection["prediction_minimum"], intersection["prediction_maximum"])

    def test_support_candidates_are_full_covariance_boundary_points(self):
        candidates = support_candidates(self.toy_parameters(), self.toy_covariance(), 1)
        self.assertEqual(len(candidates), 8)
        self.assertEqual([candidate["direction"] for candidate in candidates], ["b1_minus", "b1_plus", "b2_minus", "b2_plus", "b3_minus", "b3_plus", "b4_minus", "b4_plus"])
        for candidate in candidates:
            self.assertTrue(candidate["feasible"])
            self.assertTrue(math.isclose(candidate["ellipsoid_quadratic"], 1.0, rel_tol=1e-10, abs_tol=1e-10))

    def test_structure_and_unavailable_fold_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["available_point_count"], 20)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unavailable_fold_ids"], [5])
        self.assertEqual(totals["joint_alternative_bound_count"], 20)
        self.assertEqual(totals["intersection_bound_count"], 20)
        self.assertEqual(totals["candidate_direction_count"], 32)
        self.assertEqual(totals["candidate_evaluation_count"], 160)
        self.assertEqual(totals["nonempty_intersection_count"], 20)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["covered_point_count"], 20)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertTrue(self.summary["independent_receipt_verified"])

    def test_intersection_never_widens_independent_baseline(self):
        tightened = 0
        unchanged = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                self.assertLessEqual(envelope["independent_minimum"], envelope["intersection_minimum"])
                self.assertLessEqual(envelope["intersection_maximum"], envelope["independent_maximum"])
                self.assertLessEqual(envelope["intersection_minimum"], envelope["intersection_maximum"])
                ratio = envelope["intersection_to_independent_width_ratio"]
                self.assertGreater(ratio, 0)
                self.assertLessEqual(ratio, 1 + 1e-12)
                self.assertGreaterEqual(envelope["intersection_width_reduction"], -1e-12)
                if envelope["intersection_tightened"]:
                    tightened += 1
                else:
                    unchanged += 1
        self.assertEqual(tightened + unchanged, 20)
        self.assertEqual(tightened, self.summary["totals"]["intersection_tightened_count"])
        self.assertEqual(unchanged, self.summary["totals"]["intersection_unchanged_count"])

    def test_all_candidates_and_available_points_are_consistent(self):
        candidate_count = 0
        point_count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["denominator_sign_preserved"])
                    self.assertTrue(candidate["inside_independent"])
                    self.assertTrue(candidate["inside_joint_alternative"])
                    self.assertTrue(candidate["inside_intersection"])
            for point in fold["points"]:
                point_count += 1
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
                self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
        self.assertEqual(candidate_count, 160)
        self.assertEqual(point_count, 20)

    def test_fold5_has_no_alternative_intersection_or_residual_bound(self):
        fold5 = self.summary["folds"][4]
        self.assertFalse(fold5["prediction_envelope_available"])
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(fold5["candidate_directions"], [])
        self.assertEqual(fold5["candidate_evaluation_count"], 0)
        self.assertEqual(len(fold5["points"]), 5)
        for point in fold5["points"]:
            self.assertIsNone(point["intersection_minimum"])
            self.assertIsNone(point["intersection_maximum"])
            self.assertIsNone(point["residual_upper_bound"])
            self.assertIsNone(point["covered"])
            self.assertIsNone(point["center_prediction_inside"])

    def test_comparison_and_global_optimum_scope_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["alternative_tighter_count"] + totals["alternative_wider_count"] + totals["alternative_equal_count"], 20)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertIsNone(self.summary["full_nonlinear_global_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["joint_linear_not_full_nonlinear_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["crossing_fold_receives_no_bound"])

    def test_validator_rejects_ratio_violation_scope_and_hash_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["intersection_to_independent_width_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["intersection_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["fold5_given_finite_bound"] = True
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

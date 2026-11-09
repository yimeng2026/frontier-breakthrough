import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_enso_full_ellipsoid_lipschitz import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    intersect_bounds,
    lipschitz_envelope,
    render_figure,
    validate_summary,
)
from analyze_enso_native_ellipsoid_continuous import prediction_envelope


class EnsoFullEllipsoidLipschitzTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 1, "b2": 1, "b3": 1, "b4": 40, "b5": 1, "b6": 1, "b7": 20, "b8": 1, "b9": 1}

    @staticmethod
    def toy_covariance():
        covariance = [[0.0] * 9 for _ in range(9)]
        for index in range(9):
            covariance[index][index] = 4.0 if index in [3, 6] else 1.0
        return covariance

    def test_zero_month_has_zero_period_remainder(self):
        result = lipschitz_envelope(self.toy_parameters(), self.toy_covariance(), 2, 0, {"b4_minimum": 36, "b7_minimum": 16})
        self.assertTrue(math.isclose(result["center_prediction"], 4.0, rel_tol=1e-12))
        self.assertEqual(result["d4"], 0)
        self.assertEqual(result["d7"], 0)
        self.assertEqual(result["remainder_support"], 0)
        self.assertTrue(math.isclose(result["linear_support"], 4.0, rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_minimum"], 0.0, rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_maximum"], 8.0, rel_tol=1e-10, abs_tol=1e-10))
        independent = prediction_envelope(self.toy_parameters(), self.toy_covariance(), 2, 0)
        intersection = intersect_bounds(result["prediction_minimum"], result["prediction_maximum"], independent["prediction_minimum"], independent["prediction_maximum"])
        self.assertTrue(math.isclose(intersection["prediction_minimum"], 0.0, abs_tol=1e-10))
        self.assertTrue(math.isclose(intersection["prediction_maximum"], 8.0, rel_tol=1e-10, abs_tol=1e-10))

    def test_phase_remainder_uses_period_minimum_and_lipschitz_cap(self):
        result = lipschitz_envelope(self.toy_parameters(), self.toy_covariance(), 2, 1, {"b4_minimum": 36, "b7_minimum": 16})
        expected_d4 = min(2, 2 * math.pi * 4 / (40 * 36))
        expected_d7 = min(2, 2 * math.pi * 4 / (20 * 16))
        self.assertTrue(math.isclose(result["d4"], expected_d4, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["d7"], expected_d7, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["amplitude_cap_b4"], 6.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["amplitude_cap_b7"], 6.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["remainder_support"], 6 * (expected_d4 + expected_d7), rel_tol=1e-10, abs_tol=1e-10))
        self.assertGreater(result["full_support"], result["linear_support"])
        large_x = lipschitz_envelope(self.toy_parameters(), self.toy_covariance(), 2, 10000, {"b4_minimum": 36, "b7_minimum": 16})
        self.assertEqual(large_x["d4"], 2)
        self.assertEqual(large_x["d7"], 2)

    def test_structure_and_receipts_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 168)
        self.assertEqual(totals["alternative_bound_count"], 168)
        self.assertEqual(totals["intersection_bound_count"], 168)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["nonempty_intersection_count"], 168)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertTrue(self.summary["independent_receipt_verified"])
        self.assertTrue(self.summary["slice_receipt_verified"])

    def test_intersection_never_widens_the_independent_baseline(self):
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
        self.assertEqual(tightened + unchanged, 168)
        self.assertEqual(tightened, self.summary["totals"]["intersection_tightened_count"])
        self.assertEqual(unchanged, self.summary["totals"]["intersection_unchanged_count"])

    def test_all_candidates_remain_inside_alternative_and_intersection(self):
        count = 0
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertAlmostEqual(candidate["ellipsoid_quadratic"], 16.0, places=9)
                    self.assertTrue(candidate["inside_independent"])
                    self.assertTrue(candidate["inside_alternative"])
                    self.assertTrue(candidate["inside_intersection"])
                    self.assertLessEqual(envelope["alternative_minimum"], candidate["prediction"])
                    self.assertLessEqual(candidate["prediction"], envelope["alternative_maximum"])
                    self.assertLessEqual(envelope["intersection_minimum"], candidate["prediction"])
                    self.assertLessEqual(candidate["prediction"], envelope["intersection_maximum"])
        self.assertEqual(count, 672)

    def test_alternative_comparison_and_scope_are_not_overclaimed(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["alternative_tighter_count"] + totals["alternative_wider_count"] + totals["alternative_equal_count"], 168)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertIsNone(self.summary["full_ellipsoid_joint_nonlinear_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["full_ellipsoid_triangle_inequality_not_joint_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["candidate_checks_are_consistency_not_proof"])
        self.assertTrue(self.summary["analysis_scope"]["marginal_linear_support_not_conditional_slice"])

    def test_validator_rejects_ratio_violation_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["intersection_to_independent_width_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["intersection_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["intersection_is_global_optimum"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["slice_witnesses"]["sha256"] = "0" * 64
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

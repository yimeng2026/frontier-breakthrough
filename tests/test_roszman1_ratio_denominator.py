import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_ratio_denominator import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    ratio_denominator_interval,
    render_figure,
    validate_summary,
)


class Roszman1RatioDenominatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 1.0, "b2": 0.1, "b3": 1.0, "b4": 2.0}

    @staticmethod
    def toy_covariance():
        return [[float(row == column) for column in range(4)] for row in range(4)]

    def test_known_answer_has_exact_branches_and_feasible_witnesses(self):
        result = ratio_denominator_interval(self.toy_parameters(), self.toy_covariance(), 1, 0)
        self.assertAlmostEqual(result["lower_root"], -4 / 3, places=12)
        self.assertAlmostEqual(result["upper_root"], 0.0, places=12)
        self.assertLessEqual(result["ratio_minimum"], -4 / 3)
        self.assertGreaterEqual(result["ratio_maximum"], 0.0)
        self.assertEqual(result["denominator_sign"], "negative")
        witnesses = result["algebraic_extremizers"]
        self.assertEqual([item["direction"] for item in witnesses], ["ratio_minimum", "ratio_maximum"])
        self.assertAlmostEqual(witnesses[0]["displacement"][2], 0.6, places=12)
        self.assertAlmostEqual(witnesses[0]["displacement"][3], -0.8, places=12)
        self.assertAlmostEqual(witnesses[1]["displacement"][2], -1.0, places=12)
        self.assertAlmostEqual(witnesses[1]["displacement"][3], 0.0, places=12)
        for witness, root in zip(witnesses, [-4 / 3, 0.0]):
            self.assertAlmostEqual(witness["ratio"], root, places=12)
            self.assertAlmostEqual(witness["ellipsoid_quadratic"], 1.0, places=10)
            self.assertLess(witness["denominator"], 0)
            self.assertTrue(witness["feasible"])

    def test_tiny_storage_asymmetry_uses_the_actual_symmetric_quadratic_form(self):
        covariance = self.toy_covariance()
        covariance[2][3] = 0.25 + 1.0e-12
        covariance[3][2] = 0.25
        symmetric = [row[:] for row in covariance]
        symmetric[2][3] = symmetric[3][2] = 0.25 + 0.5e-12
        result = ratio_denominator_interval(self.toy_parameters(), covariance, 1, 0)
        expected = ratio_denominator_interval(self.toy_parameters(), symmetric, 1, 0)
        self.assertAlmostEqual(result["lower_root"], expected["lower_root"], places=12)
        self.assertAlmostEqual(result["upper_root"], expected["upper_root"], places=12)
        for witness in result["algebraic_extremizers"]:
            self.assertAlmostEqual(witness["ratio"], witness["root"], places=12)
            self.assertTrue(witness["feasible"])

    def test_singular_denominator_is_rejected_before_root_solving(self):
        parameters = self.toy_parameters()
        parameters["b4"] = 1.0
        with self.assertRaisesRegex(ValueError, "nonzero sign|negative denominator"):
            ratio_denominator_interval(parameters, self.toy_covariance(), 1, 0)
        with self.assertRaisesRegex(ValueError, "Interval|nonzero sign|negative denominator"):
            ratio_denominator_interval(self.toy_parameters(), self.toy_covariance(), 1, 2)

    def test_structure_counts_and_receipts_are_complete(self):
        totals = self.summary["totals"]
        for key, value in self.protocol["expected_structure"].items():
            self.assertEqual(totals[key], value, key)
        self.assertEqual(totals["candidate_direction_count"], 32)
        self.assertTrue(self.summary["independent_receipt_verified"])
        self.assertTrue(self.summary["joint_linear_receipt_verified"])
        self.assertEqual(self.summary["analysis_scope"]["high_precision_decimal_digits"], 80)
        self.assertIsNone(self.summary["full_nonlinear_global_optimum"])
        for value in self.summary["decision"].values():
            self.assertFalse(value)

    def test_ratio_intervals_are_inside_independent_intervals(self):
        count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                count += 1
                self.assertLessEqual(envelope["ratio_minimum"], envelope["center_ratio"])
                self.assertLessEqual(envelope["center_ratio"], envelope["ratio_maximum"])
                self.assertGreaterEqual(envelope["ratio_minimum"], envelope["independent_argument_minimum"] - 1e-10)
                self.assertLessEqual(envelope["ratio_maximum"], envelope["independent_argument_maximum"] + 1e-10)
                self.assertAlmostEqual(envelope["alternative_minimum"], envelope["linear_minimum"] - math.atan(envelope["ratio_maximum"]) / math.pi, places=12)
                self.assertLessEqual(envelope["alternative_minimum"], envelope["alternative_maximum"])
                self.assertAlmostEqual(envelope["alternative_maximum"], envelope["linear_maximum"] - math.atan(envelope["ratio_minimum"]) / math.pi, places=12)
                self.assertEqual(len(envelope["algebraic_extremizers"]), 2)
        self.assertEqual(count, 20)

    def test_intersection_never_widens_joint_linear_baseline(self):
        tightened = 0
        unchanged = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                self.assertLessEqual(envelope["joint_linear_minimum"], envelope["intersection_minimum"])
                self.assertLessEqual(envelope["intersection_maximum"], envelope["joint_linear_maximum"])
                self.assertLessEqual(envelope["intersection_minimum"], envelope["intersection_maximum"])
                self.assertLessEqual(envelope["intersection_to_joint_linear_width_ratio"], 1 + 1e-12)
                self.assertGreaterEqual(envelope["intersection_width_reduction"], -1e-12)
                tightened += envelope["intersection_tightened"]
                unchanged += not envelope["intersection_tightened"]
        self.assertEqual(tightened, self.summary["totals"]["intersection_tightened_count"])
        self.assertEqual(unchanged, self.summary["totals"]["intersection_unchanged_count"])
        self.assertEqual(tightened + unchanged, 20)

    def test_all_200_candidates_and_points_are_consistent(self):
        candidate_count = 0
        extremizer_count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                self.assertEqual(len(envelope["candidate_evaluations"]), 10)
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    extremizer_count += candidate["kind"] == "algebraic_extremizer"
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["denominator_sign_preserved"])
                    self.assertTrue(candidate["inside_ratio_interval"])
                    self.assertTrue(candidate["inside_independent"])
                    self.assertTrue(candidate["inside_joint_linear"])
                    self.assertTrue(candidate["inside_alternative"])
                    self.assertTrue(candidate["inside_intersection"])
            for point in fold["points"]:
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
                self.assertGreaterEqual(point["residual_upper_bound"], point["actual_absolute_residual"])
        self.assertEqual(candidate_count, 200)
        self.assertEqual(extremizer_count, 40)

    def test_fold5_has_no_ratio_interval_candidate_or_finite_bound(self):
        fold5 = self.summary["folds"][4]
        self.assertFalse(fold5["prediction_envelope_available"])
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(fold5["candidate_directions"], [])
        self.assertEqual(fold5["candidate_evaluation_count"], 0)
        self.assertEqual(fold5["algebraic_extremizer_count"], 0)
        self.assertEqual(len(fold5["points"]), 5)
        for point in fold5["points"]:
            self.assertIsNone(point["intersection_minimum"])
            self.assertIsNone(point["intersection_maximum"])
            self.assertIsNone(point["residual_upper_bound"])
            self.assertIsNone(point["covered"])

    def test_validator_rejects_ratio_scope_and_frozen_input_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["intersection_to_joint_linear_width_ratio"] = 2
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["ratio_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["full_nonlinear_global_optimum_claimed"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["joint_linear_bounds"]["sha256"] = "0" * 64
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

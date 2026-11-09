import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_enso_conditional_period_slice import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    conditional_covariance,
    ellipsoid_quadratic,
    period_candidates,
    render_figure,
    slice_envelope,
    validate_summary,
)


class EnsoConditionalPeriodSliceTests(unittest.TestCase):
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
            covariance[index][index] = 1.0
        covariance[3][3] = 4.0
        covariance[6][6] = 4.0
        covariance[3][4] = covariance[4][3] = 0.5
        return covariance

    def test_schur_complement_is_slice_not_marginal_block(self):
        conditional = conditional_covariance(self.toy_covariance())
        self.assertTrue(math.isclose(conditional[3][3], 0.9375, rel_tol=1e-12, abs_tol=1e-12))
        self.assertNotEqual(conditional[3][3], self.toy_covariance()[4][4])
        self.assertTrue(math.isclose(conditional[0][0], 1.0, rel_tol=1e-12))
        diagonal = [[0.0] * 9 for _ in range(9)]
        for index in range(9):
            diagonal[index][index] = 4.0 if index in [3, 6] else 1.0
        conditional_diagonal = conditional_covariance(diagonal)
        for row in range(7):
            for column in range(7):
                self.assertTrue(math.isclose(conditional_diagonal[row][column], 1.0 if row == column else 0.0, rel_tol=1e-12, abs_tol=1e-12))

    def test_known_answer_slice_support_and_candidate_feasibility(self):
        parameters = self.toy_parameters()
        covariance = [[0.0] * 9 for _ in range(9)]
        for index in range(9):
            covariance[index][index] = 4.0 if index in [3, 6] else 1.0
        result = slice_envelope(parameters, covariance, 2, 0)
        self.assertTrue(math.isclose(result["center_prediction"], 4.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["prediction_minimum"], 0.0, rel_tol=1e-10, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_maximum"], 8.0, rel_tol=1e-10, abs_tol=1e-10))
        candidates = period_candidates(parameters, covariance, 2)
        self.assertEqual(len(candidates), 4)
        self.assertEqual([item["direction"] for item in candidates], ["b4_minus", "b4_plus", "b7_minus", "b7_plus"])
        plus = candidates[1]
        self.assertTrue(math.isclose(plus["parameters"]["b4"], 44.0, rel_tol=1e-12))
        for candidate in candidates:
            self.assertTrue(candidate["feasible"])
            self.assertTrue(math.isclose(candidate["ellipsoid_quadratic"], 4.0, rel_tol=1e-10, abs_tol=1e-10))
            self.assertTrue(math.isclose(ellipsoid_quadratic(parameters, candidate["exact_parameters"], covariance), 4.0, rel_tol=1e-10, abs_tol=1e-10))

    def test_structure_counts_and_baseline_receipt_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 168)
        self.assertEqual(totals["slice_envelope_count"], 168)
        self.assertEqual(totals["candidate_direction_count"], 20)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["full_independent_violation_count"], 0)
        self.assertEqual(totals["slice_containment_violation_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["conditional_matrix_failure_count"], 0)
        self.assertTrue(self.summary["baseline_receipt_verified"])
        self.assertEqual(self.summary["baseline_envelope_match_count"], 168)

    def test_every_slice_is_contained_and_width_reduction_is_nonnegative(self):
        for fold in self.summary["folds"]:
            self.assertEqual(len(fold["conditional_covariance"]), 7)
            for envelope in fold["slice_envelopes"]:
                self.assertLessEqual(envelope["independent_minimum"], envelope["prediction_minimum"])
                self.assertLessEqual(envelope["prediction_maximum"], envelope["independent_maximum"])
                self.assertGreaterEqual(envelope["width_reduction"], -1e-10)
                ratio = envelope["slice_to_independent_width_ratio"]
                self.assertGreater(ratio, 0)
                self.assertLessEqual(ratio, 1 + 1e-12)
                self.assertLessEqual(envelope["prediction_minimum"], envelope["center_prediction"])
                self.assertLessEqual(envelope["center_prediction"], envelope["prediction_maximum"])

    def test_all_candidates_and_violation_witnesses_are_preserved(self):
        totals = self.summary["totals"]
        evaluation_count = 0
        violation_count = 0
        for fold in self.summary["folds"]:
            for envelope in fold["slice_envelopes"]:
                self.assertEqual(len(envelope["candidate_evaluations"]), 4)
                for candidate in envelope["candidate_evaluations"]:
                    evaluation_count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["inside_independent_baseline"])
                    self.assertAlmostEqual(candidate["ellipsoid_quadratic"], 16.0, places=9)
                    if candidate["outside_slice"]:
                        violation_count += 1
                        self.assertTrue(candidate["prediction"] < envelope["prediction_minimum"] or candidate["prediction"] > envelope["prediction_maximum"])
                        self.assertGreater(candidate["slice_exceedance"], 0)
                    else:
                        self.assertEqual(candidate["slice_exceedance"], 0)
        self.assertEqual(evaluation_count, 672)
        self.assertEqual(violation_count, totals["slice_violation_evaluation_count"])
        if violation_count:
            self.assertEqual(totals["slice_global_validity"], "falsified_by_feasible_candidate")
            self.assertGreater(totals["max_slice_violation_exceedance"], 0)
            self.assertIsNotNone(totals["largest_violation_witness"])
        else:
            self.assertEqual(totals["slice_global_validity"], "not_established")
            self.assertIsNone(totals["largest_violation_witness"])

    def test_no_full_optimum_probability_or_physical_period_claim(self):
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertTrue(self.summary["analysis_scope"]["conditional_slice_not_full_ellipsoid"])
        self.assertFalse(self.summary["analysis_scope"]["candidate_directions_are_global_optimizers"])
        self.assertTrue(self.summary["analysis_scope"]["zero_witness_would_not_prove_full_safety"])
        self.assertIsNone(self.summary["full_ellipsoid_joint_nonlinear_optimum"])

    def test_validator_rejects_ratio_witness_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["slice_envelopes"][0]["slice_to_independent_width_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["slice_violation_evaluation_count"] = -1
        self.assertTrue(any("witness" in error.lower() or "violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["slice_bound_called_full_ellipsoid_bound"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["baseline_bounds"]["sha256"] = "0" * 64
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

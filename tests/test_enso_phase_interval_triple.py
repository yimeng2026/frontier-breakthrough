import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_enso_phase_interval_triple import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    intersect_three_bounds,
    phase_envelope,
    product_interval,
    render_figure,
    trigonometric_interval,
    validate_summary,
)
from analyze_enso_native_ellipsoid_continuous import prediction_envelope


class EnsoPhaseIntervalTripleTests(unittest.TestCase):
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

    def test_trigonometric_intervals_cover_endpoints_and_critical_points(self):
        cases = [
            ("sin", 0, math.pi / 2, 0, 1),
            ("cos", 0, math.pi / 2, 0, 1),
            ("sin", 0, math.pi, 0, 1),
            ("cos", 0, math.pi, -1, 1),
            ("sin", -math.pi / 2, 0, -1, 0),
            ("cos", math.pi / 2, 3 * math.pi / 2, -1, 0),
        ]
        for kind, lower, upper, expected_min, expected_max in cases:
            result = trigonometric_interval(lower, upper, kind)
            self.assertTrue(math.isclose(result["minimum"], expected_min, rel_tol=1e-12, abs_tol=1e-12), (kind, result))
            self.assertTrue(math.isclose(result["maximum"], expected_max, rel_tol=1e-12, abs_tol=1e-12), (kind, result))
        full = trigonometric_interval(0, 2 * math.pi, "sin")
        self.assertEqual(full["minimum"], -1)
        self.assertEqual(full["maximum"], 1)
        wide = trigonometric_interval(-10, 10, "cos")
        self.assertEqual(wide["minimum"], -1)
        self.assertEqual(wide["maximum"], 1)

    def test_product_interval_uses_all_four_endpoint_products(self):
        result = product_interval(-2, 3, -1, 4)
        self.assertEqual(result["minimum"], -8)
        self.assertEqual(result["maximum"], 12)
        positive = product_interval(2, 3, 4, 5)
        self.assertEqual(positive["minimum"], 8)
        self.assertEqual(positive["maximum"], 15)

    def test_zero_month_phase_remainder_vanishes(self):
        parameters = self.toy_parameters()
        covariance = self.toy_covariance()
        independent = prediction_envelope(parameters, covariance, 2, 0)
        result = phase_envelope(parameters, covariance, 2, 0, {"b4_minimum": 36, "b4_maximum": 44, "b7_minimum": 16, "b7_maximum": 24}, independent)
        self.assertEqual(result["remainder_minimum"], 0)
        self.assertEqual(result["remainder_maximum"], 0)
        self.assertTrue(math.isclose(result["center_prediction"], 4.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["prediction_minimum"], 0.0, abs_tol=1e-10))
        self.assertTrue(math.isclose(result["prediction_maximum"], 8.0, rel_tol=1e-10, abs_tol=1e-10))

    def test_structure_and_all_receipts_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 168)
        self.assertEqual(totals["phase_alternative_bound_count"], 168)
        self.assertEqual(totals["triple_intersection_bound_count"], 168)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["nonempty_triple_intersection_count"], 168)
        self.assertEqual(totals["phase_candidate_violation_count"], 0)
        self.assertEqual(totals["triple_candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertTrue(self.summary["independent_receipt_verified"])
        self.assertTrue(self.summary["slice_receipt_verified"])
        self.assertTrue(self.summary["lipschitz_receipt_verified"])

    def test_triple_intersection_never_widens_lipschitz_intersection(self):
        tightened = 0
        unchanged = 0
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                self.assertLessEqual(envelope["lipschitz_intersection_minimum"], envelope["triple_minimum"])
                self.assertLessEqual(envelope["triple_maximum"], envelope["lipschitz_intersection_maximum"])
                self.assertLessEqual(envelope["triple_minimum"], envelope["triple_maximum"])
                ratio = envelope["triple_to_lipschitz_width_ratio"]
                self.assertGreater(ratio, 0)
                self.assertLessEqual(ratio, 1 + 1e-12)
                self.assertGreaterEqual(envelope["triple_width_reduction"], -1e-10)
                if envelope["triple_tightened"]:
                    tightened += 1
                else:
                    unchanged += 1
        self.assertEqual(tightened + unchanged, 168)
        self.assertEqual(tightened, self.summary["totals"]["triple_tightened_count"])
        self.assertEqual(unchanged, self.summary["totals"]["triple_unchanged_count"])

    def test_all_candidates_remain_inside_phase_alternative_and_triple(self):
        count = 0
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["inside_independent"])
                    self.assertTrue(candidate["inside_lipschitz_intersection"])
                    self.assertTrue(candidate["inside_phase_alternative"])
                    self.assertTrue(candidate["inside_triple_intersection"])
                    self.assertLessEqual(envelope["phase_minimum"], candidate["prediction"])
                    self.assertLessEqual(candidate["prediction"], envelope["phase_maximum"])
                    self.assertLessEqual(envelope["triple_minimum"], candidate["prediction"])
                    self.assertLessEqual(candidate["prediction"], envelope["triple_maximum"])
        self.assertEqual(count, 672)

    def test_comparison_and_global_optimum_scope_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["phase_tighter_than_independent_count"] + totals["phase_wider_than_independent_count"] + totals["phase_equal_to_independent_count"], 168)
        self.assertEqual(totals["phase_tighter_than_lipschitz_count"] + totals["phase_wider_than_lipschitz_count"] + totals["phase_equal_to_lipschitz_count"], 168)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertIsNone(self.summary["full_ellipsoid_joint_nonlinear_optimum"])
        self.assertTrue(self.summary["analysis_scope"]["all_trigonometric_critical_points_enumerated"])
        self.assertTrue(self.summary["analysis_scope"]["candidate_checks_are_consistency_not_proof"])

    def test_validator_rejects_ratio_violation_scope_and_hash_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["triple_to_lipschitz_width_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["triple_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["triple_intersection_is_global_optimum"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["lipschitz_bounds"]["sha256"] = "0" * 64
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

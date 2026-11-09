import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_whitened_cover_grid_erratum import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    vertex_interval_audit,
    whitened_cell_interval,
    whitened_grid,
    whitening,
    render_figure,
    validate_summary,
)


class Roszman1WhitenedCoverGridErratumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def parameters():
        source = json.loads((ROOT / "validation/roszman1-native-identifiability.json").read_text(encoding="utf-8"))
        return source["folds"][0]

    def test_counterexample_has_correct_denominator_and_prediction_intervals(self):
        fold = self.parameters()
        parameters = fold["native_parameters"]
        covariance = fold["training_jacobian"]["parameter_covariance_matrix"]
        factor = whitening(parameters, covariance, 4)["factor"]
        lower, upper = [3.0, -3.0, -2.0, -2.0], [4.0, -2.0, -1.0, -1.0]
        cell = whitened_cell_interval(parameters, factor, 4, -4868.68, lower, upper)
        self.assertLessEqual(cell["denominator_minimum"], -5245.427923332379)
        self.assertLessEqual(-5245.427923332379, cell["denominator_maximum"])
        self.assertLessEqual(cell["prediction_minimum"], 0.1630709253053592)
        self.assertLessEqual(0.1630709253053592, cell["prediction_maximum"])
        cell = {"indices": [7, 1, 2, 2], **cell}
        audit = vertex_interval_audit(parameters, factor, 4, -4868.68, cell, "union_minimum")
        self.assertEqual(audit["vertex_interval_violation_count"], 0)
        self.assertEqual(len(audit["vertices"]), 16)
        for vertex in audit["vertices"]:
            self.assertTrue(vertex["denominator_interval_contains"])
            self.assertTrue(vertex["prediction_interval_contains"])

    def test_corrected_known_answer_and_unresolved_negative_control(self):
        parameters = {"b1": 1.0, "b2": 0.1, "b3": 1.0, "b4": 2.0}
        covariance = [[float(row == column) for column in range(4)] for row in range(4)]
        grid = whitened_grid(parameters, covariance, 1, 0, 1)
        self.assertTrue(grid["union_bounded"])
        self.assertLessEqual(grid["union_minimum"], 0.0)
        self.assertGreaterEqual(grid["union_maximum"], 2.25)
        parameters["b4"] = 0.5
        unresolved = whitened_grid(parameters, covariance, 1, 0, 1)
        self.assertFalse(unresolved["union_bounded"])
        self.assertIsNone(unresolved["union_minimum"])
        self.assertGreater(unresolved["unresolved_cell_count"], 0)

    def test_structure_counts_receipts_and_original_invalid_scope(self):
        totals = self.summary["totals"]
        for key, value in self.protocol["expected_structure"].items():
            self.assertEqual(totals[key], value, key)
        self.assertTrue(self.summary["ratio_receipt_verified"])
        self.assertEqual(self.summary["original_proof_validity"], "invalid_for_conservative_proof")
        self.assertTrue(self.summary["analysis_scope"]["original_results_invalid_for_cover"])
        self.assertTrue(self.summary["analysis_scope"]["corrected_negative_denominator_displacement"])
        self.assertIsNone(self.summary["exact_global_optimum"])
        for value in self.summary["decision"].values():
            self.assertFalse(value)
        self.assertEqual(totals["native_cell_evaluation_count"] + totals["outside_cell_count"] + totals["unresolved_cell_count"], 5460)
        self.assertEqual(totals["bounded_grid_count"] + totals["unbounded_grid_count"], 60)

    def test_nested_bounds_and_vertex_interval_gates(self):
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                for grid in envelope["grids"]:
                    if grid["union_bounded"]:
                        self.assertEqual(grid["vertex_interval_violation_count"], 0)
                        for audit in grid["vertex_witnesses"]:
                            for vertex in audit["vertices"]:
                                self.assertTrue(vertex["denominator_interval_contains"])
                                self.assertTrue(vertex["prediction_interval_contains"])
                for finer, previous in [(envelope["grids"][1], envelope["grids"][0]), (envelope["grids"][2], envelope["grids"][1])]:
                    if previous["union_bounded"]:
                        self.assertTrue(finer["union_bounded"])
                        self.assertGreaterEqual(finer["union_minimum"], previous["union_minimum"] - 1e-10)
                        self.assertLessEqual(finer["union_maximum"], previous["union_maximum"] + 1e-10)
                    self.assertGreaterEqual(finer["intersection_minimum"], previous["intersection_minimum"] - 1e-10)
                    self.assertLessEqual(finer["intersection_maximum"], previous["intersection_maximum"] + 1e-10)

    def test_all_candidates_and_points_are_consistent(self):
        count = 0
        checks = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    count += 1
                    self.assertTrue(candidate["transform_valid"])
                    self.assertTrue(candidate["feasible"])
                    for check in candidate["grid_checks"]:
                        checks += 1
                        self.assertTrue(check["inside_union"])
                        self.assertTrue(check["inside_intersection"])
            for point in fold["points"]:
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
        self.assertEqual(count, 200)
        self.assertEqual(checks, 600)

    def test_fold5_has_no_cells_candidates_or_finite_bounds(self):
        fold5 = self.summary["folds"][4]
        self.assertFalse(fold5["prediction_envelope_available"])
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(fold5["partition_cell_count"], 0)
        self.assertEqual(fold5["candidate_evaluation_count"], 0)
        self.assertEqual(len(fold5["points"]), 5)
        self.assertTrue(all(point["residual_upper_bound"] is None for point in fold5["points"]))

    def test_validator_rejects_scope_ratio_and_frozen_input_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["grids"][2]["intersection_to_ratio_width_ratio"] = 2
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["vertex_interval_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["original_results_used_as_valid_cover"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            protocol = copy.deepcopy(self.protocol)
            protocol["inputs"]["original_whitened_bounds"]["sha256"] = "0" * 64
            path.write_text(json.dumps(protocol), encoding="utf-8")
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

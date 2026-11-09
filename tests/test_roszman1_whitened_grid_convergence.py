import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_whitened_grid_convergence import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    evaluate_grid8,
    render_figure,
    validate_summary,
    vertex_witnesses,
)
from analyze_roszman1_whitened_cover_grid import whitening, whitened_grid


class Roszman1WhitenedGridConvergenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 1.0, "b2": 0.1, "b3": 1.0, "b4": 2.0}

    @staticmethod
    def identity_covariance():
        return [[float(row == column) for column in range(4)] for row in range(4)]

    def test_grid8_is_streamed_bounded_and_nested_for_known_answer(self):
        grid8 = evaluate_grid8(self.toy_parameters(), self.identity_covariance(), 1, 0)
        grid4 = whitened_grid(self.toy_parameters(), self.identity_covariance(), 1, 0, 4)
        self.assertEqual(grid8["partition_cell_count"], 4096)
        self.assertTrue(grid8["union_bounded"])
        self.assertNotIn("cells", grid8)
        self.assertGreaterEqual(grid8["union_minimum"], grid4["union_minimum"] - 1e-12)
        self.assertLessEqual(grid8["union_maximum"], grid4["union_maximum"] + 1e-12)
        self.assertEqual(grid8["evaluated_cell_count"] + grid8["outside_cell_count"] + grid8["unresolved_cell_count"], 4096)

    def test_grid1_vertex_witnesses_are_outer_not_feasible(self):
        grid = whitened_grid(self.toy_parameters(), self.identity_covariance(), 1, 0, 1)
        factor = whitening(self.toy_parameters(), self.identity_covariance(), 1)["factor"]
        witnesses = vertex_witnesses(self.toy_parameters(), factor, 1, 0, grid["cells"][0], "union_minimum")
        self.assertEqual(len(witnesses["vertices"]), 16)
        for vertex in witnesses["vertices"]:
            self.assertAlmostEqual(vertex["whitened_norm"], 2.0, places=12)
            self.assertFalse(vertex["feasible_extremum_candidate"])
            self.assertEqual(vertex["witness_status"], "outer_cover_witness")
        self.assertEqual(witnesses["feasible_vertex_count"], 0)

    def test_unresolved_grid_has_no_finite_vertex_witnesses(self):
        parameters = self.toy_parameters()
        parameters["b4"] = 0.5
        grid = evaluate_grid8(parameters, self.identity_covariance(), 1, 0)
        self.assertFalse(grid["union_bounded"])
        self.assertIsNone(grid["union_minimum"])
        self.assertIsNone(grid["union_maximum"])
        self.assertEqual(grid["witness_cell_count"], 0)
        self.assertEqual(grid["vertex_evaluation_count"], 0)
        self.assertGreater(grid["unresolved_cell_count"], 0)

    def test_structure_counts_receipts_and_storage_budget(self):
        totals = self.summary["totals"]
        amendment = json.loads((ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-03.json").read_text(encoding="utf-8"))
        expected = dict(self.protocol["expected_structure"])
        expected["outside_cell_count"] = amendment["correction"]["expected_outside_cell_count"]
        for key, value in expected.items():
            self.assertEqual(totals[key], value, key)
        self.assertEqual(self.summary["analysis_scope"]["outside_count_amendment"], "03")
        self.assertTrue(self.summary["whitened_receipt_verified"])
        self.assertTrue(self.summary["stage56_receipt_verified"])
        self.assertEqual(totals["native_cell_evaluation_count"] + totals["outside_cell_count"] + totals["unresolved_cell_count"], 81920)
        self.assertEqual(totals["grid8_bounded_grid_count"] + totals["grid8_unbounded_grid_count"], 20)
        self.assertEqual(totals["grid8_vertex_evaluation_count"], 16 * totals["grid8_witness_cell_count"])
        self.assertIsNone(self.summary["exact_global_optimum"])
        for value in self.summary["decision"].values():
            self.assertFalse(value)
        for fold in self.summary["folds"]:
            for envelope in fold["envelopes"]:
                self.assertNotIn("cells", envelope["grid8"])

    def test_grid8_is_nested_and_incremental_outcomes_are_complete(self):
        additional = 0
        plateau = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                grid8 = envelope["grid8"]
                grid4 = envelope["grid4_reference"]
                self.assertGreaterEqual(grid8["intersection_minimum"], grid4["intersection_minimum"] - 1e-10)
                self.assertLessEqual(grid8["intersection_maximum"], grid4["intersection_maximum"] + 1e-10)
                self.assertLessEqual(grid8["grid8_to_grid4_width_ratio"], 1 + 1e-12)
                self.assertGreaterEqual(grid8["intersection_minimum"], envelope["ratio_minimum"])
                self.assertLessEqual(grid8["intersection_maximum"], envelope["ratio_maximum"])
                additional += grid8["additional_tightened"]
                plateau += grid8["plateau"]
        self.assertEqual(additional, self.summary["totals"]["grid8_additional_tightened_count"])
        self.assertEqual(plateau, self.summary["totals"]["grid8_plateau_count"])
        self.assertEqual(additional + plateau, 20)

    def test_all_candidates_and_vertex_witnesses_are_consistent(self):
        candidate_count = 0
        vertex_count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    self.assertTrue(candidate["transform_valid"])
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["grid8_check"]["inside_union"])
                    self.assertTrue(candidate["grid8_check"]["inside_intersection"])
                for witness in envelope["grid8"]["vertex_witnesses"]:
                    for vertex in witness["vertices"]:
                        vertex_count += 1
                        self.assertGreaterEqual(vertex["interval_gap"], -1e-10)
                        self.assertLess(vertex["denominator"], 0)
                        if vertex["feasible_extremum_candidate"]:
                            self.assertLessEqual(vertex["whitened_norm"], 4 + 1e-9)
        self.assertEqual(candidate_count, 200)
        self.assertEqual(vertex_count, self.summary["totals"]["grid8_vertex_evaluation_count"])

    def test_points_and_fold5_are_complete(self):
        for fold in self.summary["folds"][:4]:
            for point in fold["points"]:
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
                self.assertTrue(point["grid8_check"]["covered"])
                self.assertTrue(point["grid8_check"]["center_prediction_inside"])
        fold5 = self.summary["folds"][4]
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(fold5["grid8_partition_cell_count"], 0)
        self.assertEqual(fold5["candidate_evaluation_count"], 0)
        self.assertEqual(len(fold5["points"]), 5)
        self.assertTrue(all(point["residual_upper_bound"] is None for point in fold5["points"]))

    def test_validator_rejects_scope_ratio_and_frozen_input_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["grid8"]["grid8_to_grid4_width_ratio"] = 2
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["grid8_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["plateau_called_convergence_proof"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            protocol = copy.deepcopy(self.protocol)
            protocol["inputs"]["whitened_bounds"]["sha256"] = "0" * 64
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

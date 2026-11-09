import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_whitened_cover_grid import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    candidate_transform,
    minimum_norm_squared,
    whitening,
    whitened_cell_interval,
    whitened_grid,
    render_figure,
    validate_summary,
)


class Roszman1WhitenedCoverGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    @staticmethod
    def toy_parameters():
        return {"b1": 1.0, "b2": 0.1, "b3": 1.0, "b4": 2.0}

    @staticmethod
    def toy_covariance():
        return [[4.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

    def test_nonidentity_whitening_and_candidate_reconstruction(self):
        result = whitening(self.toy_parameters(), self.toy_covariance(), 1)
        self.assertAlmostEqual(result["factor"][0, 0], 2.0, places=12)
        for row in range(4):
            for column in range(4):
                if row != column:
                    self.assertAlmostEqual(result["factor"][row, column], 0.0, places=12)
        self.assertLess(result["reconstruction_max_error"], 1e-30)
        candidate = {"b1": 1.0, "b2": 0.1, "b3": 1.6, "b4": 1.2}
        transformed = candidate_transform(self.toy_parameters(), result["factor"], 1, candidate)
        self.assertAlmostEqual(transformed["whitened_norm"], 1.0, places=12)
        self.assertTrue(transformed["transform_valid"])
        for name in ["b1", "b2", "b3", "b4"]:
            self.assertAlmostEqual(transformed["reconstructed_parameters"][name], candidate[name], places=12)

    def test_known_answer_native_interval_and_nested_grids(self):
        grid1 = whitened_grid(self.toy_parameters(), self.toy_covariance(), 1, 0, 1)
        grid2 = whitened_grid(self.toy_parameters(), self.toy_covariance(), 1, 0, 2)
        grid4 = whitened_grid(self.toy_parameters(), self.toy_covariance(), 1, 0, 4)
        self.assertTrue(grid1["union_bounded"])
        self.assertLessEqual(grid1["union_minimum"], -1.0)
        self.assertGreaterEqual(grid1["union_maximum"], 3.25)
        self.assertEqual([len(grid["cells"]) for grid in [grid1, grid2, grid4]], [1, 16, 256])
        for finer, previous in [(grid2, grid1), (grid4, grid2)]:
            self.assertGreaterEqual(finer["union_minimum"], previous["union_minimum"] - 1e-12)
            self.assertLessEqual(finer["union_maximum"], previous["union_maximum"] + 1e-12)

    def test_outside_cell_is_rejected_but_possible_ball_cell_is_not(self):
        self.assertGreater(minimum_norm_squared([0.75] * 4, [1.25] * 4), 1.0)
        self.assertLessEqual(minimum_norm_squared([0.25] * 4, [0.75] * 4), 1.0)
        factor = whitening(self.toy_parameters(), self.toy_covariance(), 1)["factor"]
        outside = whitened_cell_interval(self.toy_parameters(), factor, 1, 0, [0.75] * 4, [1.25] * 4)
        self.assertEqual(outside["status"], "outside_ball")
        possible = whitened_cell_interval(self.toy_parameters(), factor, 1, 0, [0.25] * 4, [0.75] * 4)
        self.assertNotEqual(possible["status"], "outside_ball")

    def test_zero_denominator_cell_produces_unbounded_union(self):
        covariance = [[float(row == column) for column in range(4)] for row in range(4)]
        parameters = self.toy_parameters()
        parameters["b4"] = 0.5
        grid = whitened_grid(parameters, covariance, 1, 0, 1)
        self.assertFalse(grid["union_bounded"])
        self.assertIsNone(grid["union_minimum"])
        self.assertIsNone(grid["union_maximum"])
        self.assertEqual(grid["unresolved_cell_count"], 1)
        self.assertEqual(grid["evaluated_cell_count"], 0)
        self.assertEqual(grid["cells"][0]["status"], "unresolved_denominator")
        self.assertIsNone(grid["cells"][0]["prediction_minimum"])

    def test_structure_counts_and_frozen_receipt(self):
        totals = self.summary["totals"]
        for key, value in self.protocol["expected_structure"].items():
            self.assertEqual(totals[key], value, key)
        self.assertTrue(self.summary["ratio_receipt_verified"])
        self.assertEqual(self.summary["primary_grid"], 4)
        self.assertIsNone(self.summary["exact_global_optimum"])
        for value in self.summary["decision"].values():
            self.assertFalse(value)
        self.assertEqual(totals["bounded_grid_count"] + totals["unbounded_grid_count"], 60)
        self.assertEqual(totals["native_cell_evaluation_count"] + totals["outside_cell_count"] + totals["unresolved_cell_count"], 5460)

    def test_cell_accounting_nested_bounds_and_unbounded_unions(self):
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                grids = envelope["grids"]
                for grid in grids:
                    self.assertEqual(grid["evaluated_cell_count"] + grid["outside_cell_count"] + grid["unresolved_cell_count"], grid["divisions"] ** 4)
                    self.assertTrue(grid["intersection_nonempty"])
                    if not grid["union_bounded"]:
                        self.assertIsNone(grid["union_minimum"])
                        self.assertIsNone(grid["union_maximum"])
                        self.assertEqual(grid["intersection_minimum"], envelope["ratio_minimum"])
                        self.assertEqual(grid["intersection_maximum"], envelope["ratio_maximum"])
                for finer, previous in [(grids[1], grids[0]), (grids[2], grids[1])]:
                    if previous["union_bounded"]:
                        self.assertTrue(finer["union_bounded"])
                        self.assertGreaterEqual(finer["union_minimum"], previous["union_minimum"] - 1e-10)
                        self.assertLessEqual(finer["union_maximum"], previous["union_maximum"] + 1e-10)
                    self.assertGreaterEqual(finer["intersection_minimum"], previous["intersection_minimum"] - 1e-10)
                    self.assertLessEqual(finer["intersection_maximum"], previous["intersection_maximum"] + 1e-10)

    def test_all_200_transform_witnesses_and_600_grid_checks(self):
        candidate_count = 0
        check_count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    self.assertTrue(candidate["transform_valid"])
                    self.assertTrue(candidate["feasible"])
                    self.assertLessEqual(candidate["whitened_norm"], 4 + 1e-9)
                    for check in candidate["grid_checks"]:
                        check_count += 1
                        self.assertTrue(check["inside_union"])
                        self.assertTrue(check["inside_intersection"])
                        if not check["union_bounded"]:
                            self.assertFalse(check["finite_union_check"])
        self.assertEqual(candidate_count, 200)
        self.assertEqual(check_count, 600)

    def test_primary_intersections_points_and_fold5_are_complete(self):
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                primary = envelope["grids"][2]
                self.assertGreaterEqual(primary["intersection_minimum"], envelope["ratio_minimum"])
                self.assertLessEqual(primary["intersection_maximum"], envelope["ratio_maximum"])
                self.assertLessEqual(primary["intersection_to_ratio_width_ratio"], 1 + 1e-12)
            for point in fold["points"]:
                self.assertTrue(point["covered"])
                self.assertEqual(len(point["grid_checks"]), 3)
                self.assertTrue(all(check["covered"] and check["center_prediction_inside"] for check in point["grid_checks"]))
        fold5 = self.summary["folds"][4]
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
        changed["totals"]["grid_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["crossing_cells_given_finite_native_intervals"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            protocol = copy.deepcopy(self.protocol)
            protocol["inputs"]["ratio_bounds"]["sha256"] = "0" * 64
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

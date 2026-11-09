import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_ellipsoid_cover_grid import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    coordinate_cover,
    grid_bounds,
    native_box_interval,
    render_figure,
    validate_summary,
)


class Roszman1EllipsoidCoverGridTests(unittest.TestCase):
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

    def test_known_answer_cover_and_native_interval(self):
        cover = coordinate_cover(self.toy_parameters(), self.toy_covariance(), 1)
        expected = [[0.0, 2.0], [-0.9, 1.1], [0.0, 2.0], [1.0, 3.0]]
        for index, (lower, upper) in enumerate(expected):
            self.assertLessEqual(cover["lower"][index], lower)
            self.assertGreaterEqual(cover["upper"][index], upper)
        result = native_box_interval(cover["lower"], cover["upper"], 0)
        self.assertLessEqual(result["prediction_minimum"], 0.0)
        self.assertGreaterEqual(result["prediction_maximum"], 2.25)
        self.assertLess(result["denominator_maximum"], 0)
        self.assertLessEqual(result["prediction_minimum"], 1 - math.atan(-0.5) / math.pi)
        self.assertGreaterEqual(result["prediction_maximum"], 1 - math.atan(-0.5) / math.pi)

    def test_known_answer_nested_grids_and_witness(self):
        coarse = grid_bounds(self.toy_parameters(), self.toy_covariance(), 1, 0, 1)
        middle = grid_bounds(self.toy_parameters(), self.toy_covariance(), 1, 0, 2)
        fine = grid_bounds(self.toy_parameters(), self.toy_covariance(), 1, 0, 4)
        self.assertEqual([len(item["cells"]) for item in [coarse, middle, fine]], [1, 16, 256])
        for finer, previous in [(middle, coarse), (fine, middle)]:
            self.assertGreaterEqual(finer["union_minimum"], previous["union_minimum"] - 1e-12)
            self.assertLessEqual(finer["union_maximum"], previous["union_maximum"] + 1e-12)
        prediction = 1 - math.atan(1.6 / -1.2) / math.pi
        for grid in [coarse, middle, fine]:
            self.assertLessEqual(grid["union_minimum"], prediction)
            self.assertLessEqual(prediction, grid["union_maximum"])

    def test_singular_cell_is_rejected(self):
        parameters = self.toy_parameters()
        parameters["b4"] = 0.5
        cover = coordinate_cover(parameters, self.toy_covariance(), 1)
        with self.assertRaisesRegex(ValueError, "negative denominator|nonzero sign"):
            native_box_interval(cover["lower"], cover["upper"], 0)

    def test_structure_receipt_and_all_grid_counts(self):
        totals = self.summary["totals"]
        for key, value in self.protocol["expected_structure"].items():
            self.assertEqual(totals[key], value, key)
        self.assertTrue(self.summary["ratio_receipt_verified"])
        self.assertEqual(self.summary["primary_grid"], 4)
        self.assertIsNone(self.summary["exact_global_optimum"])
        for value in self.summary["decision"].values():
            self.assertFalse(value)
        self.assertEqual([item["divisions"] for item in self.summary["grid_totals"]], [1, 2, 4])
        self.assertEqual([item["cell_evaluation_count"] for item in self.summary["grid_totals"]], [20, 320, 5120])

    def test_nested_cover_candidates_and_grid_intersections(self):
        candidate_count = 0
        check_count = 0
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                grids = envelope["grids"]
                self.assertEqual([item["divisions"] for item in grids], [1, 2, 4])
                for finer, previous in [(grids[1], grids[0]), (grids[2], grids[1])]:
                    self.assertGreaterEqual(finer["union_minimum"], previous["union_minimum"] - 1e-10)
                    self.assertLessEqual(finer["union_maximum"], previous["union_maximum"] + 1e-10)
                    self.assertGreaterEqual(finer["intersection_minimum"], previous["intersection_minimum"] - 1e-10)
                    self.assertLessEqual(finer["intersection_maximum"], previous["intersection_maximum"] + 1e-10)
                for candidate in envelope["candidate_evaluations"]:
                    candidate_count += 1
                    self.assertTrue(candidate["feasible"])
                    self.assertTrue(candidate["cover_box_inside"])
                    self.assertEqual(len(candidate["grid_checks"]), 3)
                    for check in candidate["grid_checks"]:
                        check_count += 1
                        self.assertTrue(check["inside_union"])
                        self.assertTrue(check["inside_intersection"])
        self.assertEqual(candidate_count, 200)
        self.assertEqual(check_count, 600)

    def test_primary_intersections_never_widen_and_points_are_complete(self):
        for fold in self.summary["folds"][:4]:
            for envelope in fold["envelopes"]:
                primary = envelope["grids"][2]
                self.assertGreaterEqual(primary["intersection_minimum"], envelope["ratio_minimum"])
                self.assertLessEqual(primary["intersection_maximum"], envelope["ratio_maximum"])
                self.assertLessEqual(primary["intersection_to_ratio_width_ratio"], 1 + 1e-12)
                self.assertGreaterEqual(primary["intersection_width_reduction"], -1e-12)
            for point in fold["points"]:
                self.assertTrue(point["covered"])
                self.assertTrue(point["center_prediction_inside"])
                self.assertEqual(len(point["grid_checks"]), 3)
                for check in point["grid_checks"]:
                    self.assertTrue(check["covered"])
                    self.assertTrue(check["center_prediction_inside"])

    def test_fold5_has_no_cells_grid_bounds_or_candidates(self):
        fold5 = self.summary["folds"][4]
        self.assertFalse(fold5["prediction_envelope_available"])
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(fold5["candidate_directions"], [])
        self.assertEqual(fold5["cell_evaluation_count"], 0)
        self.assertEqual(fold5["candidate_evaluation_count"], 0)
        self.assertEqual(len(fold5["points"]), 5)
        for point in fold5["points"]:
            self.assertIsNone(point["intersection_minimum"])
            self.assertIsNone(point["residual_upper_bound"])
            self.assertIsNone(point["covered"])

    def test_validator_rejects_scope_ratio_and_frozen_input_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["folds"][0]["envelopes"][0]["grids"][2]["intersection_to_ratio_width_ratio"] = 2
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["grid_candidate_violation_count"] = 1
        self.assertTrue(any("violation" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["exact_global_optimum_claimed"] = True
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

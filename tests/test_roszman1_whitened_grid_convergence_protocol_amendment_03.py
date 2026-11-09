import itertools
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "validation/roszman1-whitened-grid-convergence-protocol.json"
AMENDMENT = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-03.json"


class Roszman1WhitenedGridConvergenceProtocolAmendment03Tests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AMENDMENT.is_file(), "Grid-8 outside-count amendment must be frozen before results")
        self.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))

    def test_independent_combinatorial_count_is_1520_per_x(self):
        distances_squared = [9, 4, 1, 0, 0, 1, 4, 9]
        outside = sum(sum(distances_squared[index] for index in indices) > 16 for indices in itertools.product(range(8), repeat=4))
        self.assertEqual(outside, 1520)
        self.assertEqual(4096 - outside, 2576)
        self.assertEqual(outside * 20, 30400)
        self.assertEqual(self.amendment["correction"]["expected_outside_cell_count"], 30400)
        self.assertEqual(self.amendment["correction"]["expected_evaluated_cell_count"], 51520)
        self.assertEqual(self.amendment["correction"]["outside_per_available_x"], 1520)
        boundary_norm_squared = sum(value ** 2 for value in [2, 2, 2, 2])
        self.assertEqual(boundary_norm_squared, 16)
        self.assertLessEqual(boundary_norm_squared, 16)
        self.assertTrue(self.amendment["correction"]["boundary_cells_retained"])

    def test_previous_amendment_and_original_structure_are_preserved(self):
        self.assertEqual(self.amendment["status"], "frozen_before_roszman1_whitened_grid_convergence_results")
        self.assertEqual(self.amendment["previous_amendment"]["file"], "validation/roszman1-whitened-grid-convergence-protocol-amendment-02.json")
        self.assertEqual(self.amendment["previous_amendment"]["sha256"], "1486361e1e7121dab30bf7ca769a0eaba54374c0a2fb283ffea0404630c0b2d9")
        original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
        self.assertEqual(original["expected_structure"]["outside_cell_count"], 0)
        self.assertEqual(original["expected_structure"]["grid8_partition_cell_count"], 81920)
        self.assertTrue(self.amendment["historical_preservation"]["previous_amendment_unchanged"])
        self.assertTrue(self.amendment["historical_preservation"]["convergence_result_not_yet_written"])
        for key, value in self.amendment["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.amendment["decision"]["outside_cells_silently_dropped"])
        self.assertFalse(self.amendment["decision"]["denominator_gate_relaxed"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "validation/roszman1-whitened-cover-grid-protocol.json"
AMENDMENT = ROOT / "validation/roszman1-whitened-cover-grid-protocol-amendment-01.json"


class Roszman1WhitenedCoverGridProtocolAmendmentTests(unittest.TestCase):
    def test_boundary_tolerance_is_conservative_and_original_is_preserved(self):
        self.assertTrue(AMENDMENT.is_file(), "Boundary amendment must be frozen before implementation")
        amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        self.assertEqual(amendment["status"], "frozen_before_roszman1_whitened_cover_grid_results")
        self.assertEqual(amendment["original_protocol"]["file"], "validation/roszman1-whitened-cover-grid-protocol.json")
        self.assertEqual(amendment["original_protocol"]["sha256"], "1ad14ef93dbd9a4d531841cd7ff1475bb8b10b5b1be9b6a7b79426b15ab87184")
        self.assertEqual(amendment["correction"]["outside_distance_tolerance"], "1e-12*(1+r^2)")
        self.assertEqual(amendment["observed_before_correction"]["outside_cell_count"], 320)
        self.assertEqual(amendment["observed_before_correction"]["grid4_outside_cells_per_x"], 16)
        self.assertAlmostEqual(amendment["observed_before_correction"]["example_minimum_norm_squared"], 16.000000000000007)
        self.assertEqual(amendment["correction"]["expected_outside_cell_count"], 0)
        self.assertTrue(amendment["correction"]["boundary_uncertain_cells_retained"])
        self.assertTrue(amendment["correction"]["denominator_gate_unchanged"])
        self.assertTrue(amendment["historical_preservation"]["original_protocol_unchanged"])
        self.assertTrue(amendment["historical_preservation"]["no_result_files_rewritten"])

    def test_original_structure_and_denominator_prohibition_remain(self):
        original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
        amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        self.assertEqual(original["expected_structure"]["outside_cell_count"], 0)
        self.assertIn("strictly greater than r", original["whitening_rule"]["outside_rule"])
        self.assertIn("strictly greater than r", original["whitening_rule"]["outside_rule"])
        self.assertIn("never drop it", original["whitening_rule"]["crossing_rule"])
        self.assertFalse(original["decision"]["crossing_cells_given_finite_native_intervals"])
        self.assertFalse(amendment["decision"]["boundary_cells_given_finite_intervals"])
        self.assertFalse(amendment["decision"]["denominator_gate_relaxed"])


if __name__ == "__main__":
    unittest.main()

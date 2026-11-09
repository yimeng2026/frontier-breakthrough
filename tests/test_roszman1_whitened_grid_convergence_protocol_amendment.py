import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "validation/roszman1-whitened-grid-convergence-protocol.json"
AMENDMENT = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-01.json"


class Roszman1WhitenedGridConvergenceProtocolAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AMENDMENT.is_file(), "Convergence erratum alignment must be frozen before implementation")
        self.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        self.original = json.loads(ORIGINAL.read_text(encoding="utf-8"))

    def test_original_is_preserved_and_corrected_inputs_are_frozen(self):
        self.assertEqual(self.amendment["status"], "frozen_before_roszman1_whitened_grid_convergence_results")
        self.assertEqual(self.amendment["original_protocol"]["file"], "validation/roszman1-whitened-grid-convergence-protocol.json")
        self.assertEqual(self.amendment["original_protocol"]["sha256"], "c784136c0c75a4d069dff00b85b694c91549f5e8f2b48a17747f5f9b57dcd7b1")
        inputs = self.amendment["corrected_inputs"]
        self.assertEqual(inputs["whitened_bounds"]["file"], "validation/roszman1-whitened-cover-grid-corrected-01.json")
        self.assertEqual(inputs["whitened_bounds"]["sha256"], "526d18aa08a0538e85b21bfa512aafa3d314c626cdfa34629f977cd692d15629")
        self.assertEqual(inputs["whitened_receipt"]["file"], "validation/roszman1-whitened-cover-grid-erratum-check.json")
        self.assertEqual(inputs["whitened_runner"]["file"], "scripts/analyze_roszman1_whitened_cover_grid_erratum.py")
        self.assertEqual(inputs["whitened_runner"]["sha256"], "00dcea0311f1d4ddfc4a2d7c8f77caeb65e54ae85b934c26b5e4890eb4a5753b")
        self.assertEqual(self.original["inputs"]["whitened_bounds"]["sha256"], "76bcbec485dac10e2b73b2eb91426ff657c3c482a2610df6ed8cf145e8b1cd3c")
        self.assertTrue(self.amendment["historical_preservation"]["original_protocol_unchanged"])
        self.assertTrue(self.amendment["historical_preservation"]["original_whitened_runner_unchanged"])
        self.assertFalse(self.amendment["historical_preservation"]["original_results_used_as_valid_cover"])

    def test_corrected_receipt_and_denominator_rule_are_required(self):
        receipt = self.amendment["corrected_receipt_rule"]
        self.assertEqual(receipt["primary_grid"], 4)
        self.assertEqual(receipt["native_cell_evaluation_count"], 5460)
        self.assertEqual(receipt["unresolved_cell_count"], 0)
        self.assertEqual(receipt["vertex_interval_violation_count"], 0)
        self.assertEqual(receipt["transform_witness_count"], 200)
        self.assertEqual(receipt["original_proof_validity"], "invalid_for_conservative_proof")
        self.assertEqual(receipt["primary_intersection_tightened_count"], 17)
        self.assertEqual(receipt["primary_intersection_unchanged_count"], 3)
        self.assertEqual(self.amendment["correction_rule"]["denominator"], "d=d0-L_row4*u")
        self.assertFalse(self.amendment["historical_preservation"]["original_results_used_as_valid_cover"])
        self.assertTrue(self.amendment["historical_preservation"]["convergence_result_not_yet_written"])

    def test_original_structure_and_overclaim_prohibitions_remain(self):
        expected = self.original["expected_structure"]
        self.assertEqual(expected["grid8_partition_cell_count"], 81920)
        self.assertEqual(expected["outside_cell_count"], 0)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["candidate_grid8_containment_check_count"], 200)
        for key, value in self.amendment["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.amendment["decision"]["original_whitened_cover_used"])
        self.assertFalse(self.amendment["decision"]["plateau_called_convergence_proof"])


if __name__ == "__main__":
    unittest.main()

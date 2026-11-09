import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "validation/roszman1-whitened-grid-convergence-protocol-amendment-02.json"


class Roszman1WhitenedGridConvergenceProtocolAmendment02Tests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AMENDMENT.is_file(), "Direct stage-56 input amendment must be frozen before implementation")
        self.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))

    def test_direct_stage56_inputs_and_previous_amendment_are_frozen(self):
        self.assertEqual(self.amendment["status"], "frozen_before_roszman1_whitened_grid_convergence_results")
        self.assertEqual(self.amendment["previous_amendment"]["file"], "validation/roszman1-whitened-grid-convergence-protocol-amendment-01.json")
        self.assertEqual(self.amendment["previous_amendment"]["sha256"], "ed85e6979a0eedaab8c2cd6cddc37dc769351432bfa4c911c8c879761f56e81f")
        inputs = self.amendment["additional_inputs"]
        self.assertEqual(inputs["ratio_bounds"]["file"], "validation/roszman1-ratio-denominator-intersection.json")
        self.assertEqual(inputs["ratio_bounds"]["sha256"], "7e4a70116617e408ada047597e1ff2609224e64cb0c6e7cd230dd6d4c4b0c103")
        self.assertEqual(inputs["ratio_receipt"]["file"], "validation/roszman1-ratio-denominator-check.json")
        self.assertEqual(inputs["ratio_receipt"]["sha256"], "d43372719b626a3ccc233b493e42b806e316761c283b0d1c60eb2781a170dc65")
        self.assertTrue(self.amendment["historical_preservation"]["previous_amendment_unchanged"])
        self.assertTrue(self.amendment["historical_preservation"]["original_results_used_only_for_error_identity"])

    def test_reason_scope_and_prohibitions(self):
        self.assertIn("algebraic_extremizers", self.amendment["reason"])
        self.assertEqual(self.amendment["rule"]["algebraic_source"], "Use exact_parameters from the stage-56 algebraic_extremizers, not reconstructed floats from the corrected whitened candidate evaluations")
        self.assertEqual(self.amendment["rule"]["receipt"], "Require the stage-56 receipt to be passed and its summarySha256 to match the stage-56 bounds file")
        for key, value in self.amendment["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.amendment["decision"]["reconstructed_parameters_substituted_for_original"])
        self.assertFalse(self.amendment["decision"]["previous_amendment_rewritten"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-whitened-cover-grid-erratum-01.json"


class Roszman1WhitenedCoverGridErratumProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Whitened-cover erratum must be frozen before corrected computation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_original_counterexample_and_invalid_proof_scope_are_frozen(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_whitened_cover_grid_erratum_01")
        self.assertEqual(self.protocol["original_state"]["proof_validity"], "invalid_for_conservative_proof")
        case = self.protocol["original_state"]["counterexample"]
        self.assertEqual(case["fold"], 1)
        self.assertEqual(case["x"], -4868.68)
        self.assertEqual(case["indices"], [7, 1, 2, 2])
        self.assertEqual(case["u"], [4.0, -3.0, -2.0, -1.0])
        self.assertEqual(case["original_denominator_interval"], [-4427.651068045582, -4269.936142895595])
        self.assertEqual(case["actual_denominator"], -5245.427923332379)
        self.assertLess(case["actual_denominator"], case["original_denominator_interval"][0])
        self.assertEqual(case["original_prediction_minimum"], 0.1681522813722415)
        self.assertEqual(case["actual_prediction"], 0.1630709253053592)
        self.assertLess(case["actual_prediction"], case["original_prediction_minimum"])
        self.assertEqual(self.protocol["correction_rule"]["denominator"], "d=d0-L_row4*u; the coefficients of the affine denominator form are -L_row4, not +L_row4")
        self.assertEqual(self.protocol["original_state"]["original_runner_sha256"], "abd9b89610398953386e86cf2676081056d14737f9ae1870687d9c7e3dde64a9")
        self.assertTrue(self.protocol["original_state"]["all_original_whitened_tightening_claims_suspended"])

    def test_inputs_and_corrected_structure_are_complete(self):
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 8)
        self.assertEqual(inputs["original_protocol"]["sha256"], "1ad14ef93dbd9a4d531841cd7ff1475bb8b10b5b1be9b6a7b79426b15ab87184")
        self.assertEqual(inputs["boundary_amendment"]["sha256"], "61ddfa16e592b2ecf4c4864ad4ea75d8ea6bd4b03309fdf63686b792e128b00d")
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["original_whitened_bounds"]["sha256"], "76bcbec485dac10e2b73b2eb91426ff657c3c482a2610df6ed8cf145e8b1cd3c")
        self.assertEqual(inputs["original_receipt"]["sha256"], "4809ab4f01712094814b58e3ead4728b9bdcb105d5fe6a7e3c2cc88750c97e9a")
        self.assertEqual(inputs["original_runner"]["sha256"], "abd9b89610398953386e86cf2676081056d14737f9ae1870687d9c7e3dde64a9")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["interval_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["grid_cover_count"], 60)
        self.assertEqual(expected["partition_cell_count"], 5460)
        self.assertEqual(expected["outside_cell_count"], 0)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["candidate_grid_containment_check_count"], 600)
        self.assertEqual(expected["transform_witness_count"], 200)
        self.assertEqual(expected["transform_violation_count"], 0)
        self.assertEqual(expected["grid_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertFalse(self.protocol["output_rule"]["overwrite_original_results"])

    def test_history_and_scope_are_preserved_without_reusing_old_cover(self):
        self.assertTrue(self.protocol["historical_preservation"]["original_files_unchanged"])
        self.assertTrue(self.protocol["historical_preservation"]["original_runner_unchanged"])
        self.assertTrue(self.protocol["historical_preservation"]["new_result_and_report_paths"])
        self.assertEqual(self.protocol["baseline_rule"]["source"], "Only the stage-56 ratio_minimum, ratio_maximum and ratio_width fields stored in the original stage-58 envelopes; no original whitened grid bounds or tightening claims are trusted")
        self.assertEqual(self.protocol["comparison_rule"]["vertex_gate"], "Recompute denominator and prediction intervals at every witness and reject any interval that excludes the corresponding actual value")
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["original_results_used_as_valid_cover"])
        self.assertFalse(self.protocol["decision"]["original_history_rewritten"])
        self.assertFalse(self.protocol["decision"]["sign_error_hidden"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-conditional-period-slice-protocol.json"
AMENDMENT = ROOT / "validation/enso-conditional-period-slice-protocol-amendment-01.json"


class EnsoConditionalPeriodSliceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Conditional-period slice protocol must be frozen before implementation")
        self.assertTrue(AMENDMENT.is_file(), "Support-direction correction must be frozen before feasible candidates are used")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        self.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))

    def test_frozen_inputs_cover_data_baseline_and_native_evaluators(self):
        self.assertEqual(self.protocol["status"], "frozen_before_enso_conditional_period_slice_bounds")
        inputs = self.protocol["inputs"]
        self.assertEqual(inputs["native_identifiability"]["sha256"], "19656ed9f5930bed7e9bbdcd1072f50b5e68a8836c1975ab550dc1d828011d7e")
        self.assertEqual(inputs["baseline_bounds"]["sha256"], "d6eab927eaafc9dc8d469fa42e830660b0e673bde52031b1cd2bd78f795f61ea")
        self.assertEqual(inputs["baseline_receipt"]["sha256"], "e1b0b71432fab1d071682bb5646828edbf83d5137f5ba7db1942ec37f30cab73")
        self.assertEqual(inputs["baseline_runner"]["sha256"], "614a419ce8388ab644b9665023600ebfb475c82577b550e74ee632b4f9c438e1")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "1b0b195170bf98c542c74544850db8c0a76d05698bbcbdb6063ae24ba6061a92")
        self.assertEqual(inputs["support_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")

    def test_slice_and_candidate_structure_are_frozen_before_outcomes(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 168)
        self.assertEqual(expected["slice_envelope_count"], 168)
        self.assertEqual(expected["coefficient_count"], 7)
        self.assertEqual(expected["period_count"], 2)
        self.assertEqual(expected["candidate_directions_per_fold"], 4)
        self.assertEqual(expected["candidate_direction_count"], 20)
        self.assertEqual(expected["candidate_evaluation_count"], 672)
        self.assertEqual(expected["full_independent_violation_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertEqual(self.protocol["candidate_rule"]["directions"], ["b4_minus", "b4_plus", "b7_minus", "b7_plus"])
        self.assertFalse(self.protocol["candidate_rule"]["directions_selected_after_evaluation"])

    def test_support_direction_correction_preserves_original_and_covariance(self):
        self.assertEqual(self.amendment["original_protocol"]["sha256"], "74db1ce1ffa965aefb77fc804c94ddac9f3fa5e1e4c27051d4d038a29a58edca")
        correction = self.amendment["correction"]
        self.assertIn("C*e_p", correction["direction_formula"])
        self.assertIn("all parameters may move", correction["direction_formula"])
        self.assertTrue(correction["off_diagonal_covariance_preserved"])
        self.assertTrue(correction["coordinate_only_formula_rejected_for_correlated_ellipsoid"])
        self.assertTrue(self.amendment["preservation_rule"]["original_protocol_file_unchanged"])
        self.assertTrue(self.amendment["preservation_rule"]["no_result_file_generated_before_correction"])
        self.assertEqual(self.protocol["expected_structure"]["candidate_evaluation_count"], 672)

    def test_slice_is_not_full_ellipsoid_or_global_optimum(self):
        self.assertTrue(self.protocol["analysis_scope"]["conditional_slice_not_full_ellipsoid"])
        self.assertFalse(self.protocol["analysis_scope"]["candidate_directions_are_global_optimizers"])
        self.assertTrue(self.protocol["analysis_scope"]["zero_witness_would_not_prove_full_safety"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["slice_bound_called_full_ellipsoid_bound"])
        self.assertFalse(self.protocol["decision"]["joint_full_nonlinear_optimum_claimed"])
        self.assertFalse(self.protocol["decision"]["candidate_violations_hidden"])


if __name__ == "__main__":
    unittest.main()

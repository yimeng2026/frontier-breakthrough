import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-full-ellipsoid-lipschitz-protocol.json"


class EnsoFullEllipsoidLipschitzProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Full-ellipsoid Lipschitz protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_cover_baseline_candidates_and_evaluators(self):
        self.assertEqual(self.protocol["status"], "frozen_before_enso_full_ellipsoid_lipschitz_intersection")
        inputs = self.protocol["inputs"]
        self.assertEqual(inputs["native_identifiability"]["sha256"], "19656ed9f5930bed7e9bbdcd1072f50b5e68a8836c1975ab550dc1d828011d7e")
        self.assertEqual(inputs["independent_bounds"]["sha256"], "d6eab927eaafc9dc8d469fa42e830660b0e673bde52031b1cd2bd78f795f61ea")
        self.assertEqual(inputs["independent_receipt"]["sha256"], "e1b0b71432fab1d071682bb5646828edbf83d5137f5ba7db1942ec37f30cab73")
        self.assertEqual(inputs["slice_witnesses"]["sha256"], "db09ed73e33b554f9386962252be45153739c9600d0b0bb8b4298e87793ceda3")
        self.assertEqual(inputs["slice_receipt"]["sha256"], "829e76b9def8fe4fe7bac4050c555980f303c8bbcdbed88a960b1f6339b487af")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "1b0b195170bf98c542c74544850db8c0a76d05698bbcbdb6063ae24ba6061a92")
        self.assertEqual(inputs["support_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")

    def test_structure_and_intersection_gates_are_frozen(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 168)
        self.assertEqual(expected["alternative_bound_count"], 168)
        self.assertEqual(expected["intersection_bound_count"], 168)
        self.assertEqual(expected["candidate_evaluation_count"], 672)
        self.assertEqual(expected["nonempty_intersection_count"], 168)
        self.assertEqual(expected["alternative_candidate_violation_count"], 0)
        self.assertEqual(expected["intersection_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertFalse(self.protocol["comparison_rule"]["alternative_assumed_tighter_everywhere"])
        self.assertTrue(self.protocol["comparison_rule"]["intersection_may_be_unchanged"])

    def test_scope_preserves_conservative_proof_not_global_optimality(self):
        self.assertTrue(self.protocol["analysis_scope"]["full_ellipsoid_triangle_inequality_not_joint_optimum"])
        self.assertTrue(self.protocol["analysis_scope"]["candidate_checks_are_consistency_not_proof"])
        self.assertTrue(self.protocol["analysis_scope"]["intersection_preserves_both_valid_bounds"])
        self.assertTrue(self.protocol["analysis_scope"]["marginal_linear_support_not_conditional_slice"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["intersection_is_global_optimum"])
        self.assertFalse(self.protocol["decision"]["candidate_checks_replace_analytic_proof"])
        self.assertFalse(self.protocol["decision"]["alternative_always_tighter_claimed"])


if __name__ == "__main__":
    unittest.main()

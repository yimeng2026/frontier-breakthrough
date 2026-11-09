import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-joint-linear-arctan-protocol.json"


class Roszman1JointLinearArctanProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Roszman1 joint-linear arctan protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_cover_native_baseline_and_receipt(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_joint_linear_arctan_intersection")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 5)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["independent_bounds"]["sha256"], "50c672fc3022b34465557daf98a12ce1f975b358e6ba5c9590202a2bdc4660a9")
        self.assertEqual(inputs["independent_receipt"]["sha256"], "e711e4f452234dd816334709cdf73901c8131bafdf72fcd524a94be2f209f3e3")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["baseline_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")

    def test_structure_and_unavailable_fold_are_frozen(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["joint_alternative_bound_count"], 20)
        self.assertEqual(expected["intersection_bound_count"], 20)
        self.assertEqual(expected["candidate_direction_count"], 32)
        self.assertEqual(expected["candidate_evaluation_count"], 160)
        self.assertEqual(expected["nonempty_intersection_count"], 20)
        self.assertEqual(expected["alternative_candidate_violation_count"], 0)
        self.assertEqual(expected["intersection_candidate_violation_count"], 0)
        self.assertEqual(expected["independent_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["candidate_feasibility_failure_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertEqual(self.protocol["candidate_rule"]["directions"], ["b1_minus", "b1_plus", "b2_minus", "b2_plus", "b3_minus", "b3_plus", "b4_minus", "b4_plus"])

    def test_joint_linear_support_is_not_full_nonlinear_optimum(self):
        self.assertTrue(self.protocol["analysis_scope"]["joint_linear_not_full_nonlinear_optimum"])
        self.assertTrue(self.protocol["analysis_scope"]["candidate_checks_are_consistency_not_proof"])
        self.assertTrue(self.protocol["analysis_scope"]["crossing_fold_receives_no_bound"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["joint_alternative_is_global_optimum"])
        self.assertFalse(self.protocol["decision"]["fold5_given_finite_bound"])
        self.assertFalse(self.protocol["decision"]["candidate_checks_replace_support_proof"])


if __name__ == "__main__":
    unittest.main()

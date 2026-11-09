import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/chwirut1-log-support-protocol.json"


class Chwirut1LogSupportProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Chwirut1 log-support protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_cover_model_baseline_and_receipt(self):
        self.assertEqual(self.protocol["status"], "frozen_before_chwirut1_log_support_intersection")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 5)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "e8e76516b05e8fd83f60df0ad93215ce41984ca562cc9e5140291f5f6ba72cc8")
        self.assertEqual(inputs["independent_bounds"]["sha256"], "5795bb98f399366f8b7f35ebd754683742e6dc61e38bc6f1bccb4fcf6ccb91d2")
        self.assertEqual(inputs["independent_receipt"]["sha256"], "33d4d3a4fb88cd6270e19d4eafef697dc4967c0345e1f05c7d36644a6ed3047d")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "c3419658e1eb51acea67dee86518dd46ff7af25182a19bd407d5cb90a346b1ab")
        self.assertEqual(inputs["baseline_runner"]["sha256"], "4ad6f6e2d5877efaef45e23fc588521a920ad2a91c597d551f79d7d0769ea5e8")

    def test_structure_and_candidate_directions_are_frozen(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 214)
        self.assertEqual(expected["unique_distance_count"], 22)
        self.assertEqual(expected["log_alternative_bound_count"], 22)
        self.assertEqual(expected["intersection_bound_count"], 22)
        self.assertEqual(expected["candidate_direction_count"], 30)
        self.assertEqual(expected["candidate_evaluation_count"], 132)
        self.assertEqual(expected["nonempty_intersection_count"], 22)
        self.assertEqual(expected["alternative_candidate_violation_count"], 0)
        self.assertEqual(expected["intersection_candidate_violation_count"], 0)
        self.assertEqual(expected["independent_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["candidate_feasibility_failure_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertEqual(self.protocol["candidate_rule"]["directions"], ["b1_minus", "b1_plus", "b2_minus", "b2_plus", "b3_minus", "b3_plus"])

    def test_log_support_is_not_model_replacement_or_global_optimum(self):
        self.assertTrue(self.protocol["analysis_scope"]["log_tangent_secant_not_model_replacement"])
        self.assertTrue(self.protocol["analysis_scope"]["finite_tangent_set_not_global_optimizer"])
        self.assertTrue(self.protocol["analysis_scope"]["candidate_checks_are_consistency_not_proof"])
        self.assertFalse(self.protocol["analysis_scope"]["independent_model_family_replication"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["log_alternative_is_global_optimum"])
        self.assertFalse(self.protocol["decision"]["candidate_checks_replace_log_proof"])
        self.assertFalse(self.protocol["decision"]["nonpositive_denominator_ignored"])


if __name__ == "__main__":
    unittest.main()

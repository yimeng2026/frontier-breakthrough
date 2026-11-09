import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-conservative-support-synthesis-protocol.json"


class NativeConservativeSupportSynthesisProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Native conservative-support synthesis protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_all_latest_results_and_receipts_are_frozen(self):
        self.assertEqual(self.protocol["status"], "frozen_before_native_conservative_support_synthesis")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 6)
        self.assertEqual(inputs["chwirut1_bounds"]["sha256"], "5ec99a6a2ed22d87e72a0e49c715630e0c214bd0f91ec5742a41ec8176dd8788")
        self.assertEqual(inputs["chwirut1_receipt"]["sha256"], "057e5e2055695cc27cdba636175e9513c54acdc2146c15301f10dd128529aaa3")
        self.assertEqual(inputs["roszman1_bounds"]["sha256"], "45852e2534f51098ae390e62092d1b8df04c609d37aba5211121f637599c3b35")
        self.assertEqual(inputs["roszman1_receipt"]["sha256"], "5f0eb06cc99161eaaabbdc033ffa49998f97a9c8bb795b8cf09edf888d9e4ff5")
        self.assertEqual(inputs["enso_bounds"]["sha256"], "26e116c94f476a8f75cbbb5af1e0f377f959fe99b82c9cc551e485bc1a87f263")
        self.assertEqual(inputs["enso_receipt"]["sha256"], "473a271f6dbbeabab0647d69511c95acc55f367356c9533b75394ff38877d1e5")

    def test_structure_counts_and_unavailable_fold_are_frozen(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["dataset_count"], 3)
        self.assertEqual(expected["held_out_point_count"], 407)
        self.assertEqual(expected["available_point_count"], 402)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], ["roszman1:5"])
        self.assertEqual(expected["unique_envelope_count"], 210)
        self.assertEqual(expected["tightened_envelope_count"], 79)
        self.assertEqual(expected["unchanged_envelope_count"], 131)
        self.assertEqual(expected["nonempty_intersection_count"], 210)
        self.assertEqual(expected["candidate_evaluation_count"], 964)
        self.assertEqual(expected["candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)

    def test_scope_prohibits_cross_unit_pooling_and_global_optimum_claims(self):
        self.assertTrue(self.protocol["analysis_scope"]["model_specific_baselines_only"])
        self.assertTrue(self.protocol["analysis_scope"]["candidate_checks_are_consistency_not_proof"])
        self.assertFalse(self.protocol["analysis_scope"]["cross_dataset_raw_width_pooling"])
        self.assertFalse(self.protocol["analysis_scope"]["unified_stability_score"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["global_optimum_claimed"])
        self.assertFalse(self.protocol["decision"]["unavailable_points_dropped"])


if __name__ == "__main__":
    unittest.main()

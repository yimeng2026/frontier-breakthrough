import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/native-ellipsoid-cross-model-synthesis-protocol.json"


class NativeEllipsoidCrossModelProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Cross-model native ellipsoid protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_all_six_frozen_inputs_have_explicit_hashes(self):
        self.assertEqual(self.protocol["status"], "frozen_before_native_ellipsoid_cross_model_synthesis")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 6)
        expected = {
            "chwirut1_bounds": "5795bb98f399366f8b7f35ebd754683742e6dc61e38bc6f1bccb4fcf6ccb91d2",
            "chwirut1_receipt": "33d4d3a4fb88cd6270e19d4eafef697dc4967c0345e1f05c7d36644a6ed3047d",
            "roszman1_bounds": "50c672fc3022b34465557daf98a12ce1f975b358e6ba5c9590202a2bdc4660a9",
            "roszman1_receipt": "e711e4f452234dd816334709cdf73901c8131bafdf72fcd524a94be2f209f3e3",
            "enso_bounds": "d6eab927eaafc9dc8d469fa42e830660b0e673bde52031b1cd2bd78f795f61ea",
            "enso_receipt": "e1b0b71432fab1d071682bb5646828edbf83d5137f5ba7db1942ec37f30cab73",
        }
        for key, digest in expected.items():
            self.assertEqual(inputs[key]["sha256"], digest, key)
            self.assertTrue((ROOT / inputs[key]["file"]).is_file(), key)

    def test_structure_preserves_all_folds_points_and_unavailable_cases(self):
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["dataset_count"], 3)
        self.assertEqual(expected["fold_count"], 15)
        self.assertEqual(expected["held_out_point_count"], 407)
        self.assertEqual(expected["certified_fold_count"], 14)
        self.assertEqual(expected["available_point_count"], 402)
        self.assertEqual(expected["covered_point_count"], 402)
        self.assertEqual(expected["violation_point_count"], 0)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unique_envelope_count"], 210)
        self.assertEqual(expected["center_prediction_envelope_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)
        self.assertEqual(expected["baseline_radius"], 4)
        self.assertEqual(expected["per_dataset"]["chwirut1"], {"folds": 5, "points": 214, "available": 214, "unavailable": 0, "envelopes": 22})
        self.assertEqual(expected["per_dataset"]["roszman1"], {"folds": 5, "points": 25, "available": 20, "unavailable": 5, "envelopes": 20})
        self.assertEqual(expected["per_dataset"]["enso"], {"folds": 5, "points": 168, "available": 168, "unavailable": 0, "envelopes": 168})

    def test_scope_prohibits_cross_unit_pooling_and_unified_scores(self):
        self.assertTrue(self.protocol["analysis_scope"]["within_dataset_normalization_only"])
        self.assertFalse(self.protocol["analysis_scope"]["cross_dataset_raw_width_pooling"])
        self.assertFalse(self.protocol["analysis_scope"]["new_model_evaluation"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["universal_stability_score_claimed"])
        self.assertFalse(self.protocol["decision"]["cross_dataset_pooled_error_metrics_claimed"])
        self.assertFalse(self.protocol["decision"]["unavailable_points_dropped"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path


class Chwirut1NativeHoldoutProtocolTests(unittest.TestCase):
    def test_chwirut1_protocol_freezes_unique_distance_groups(self):
        root = Path(__file__).resolve().parents[1]
        protocol = json.loads((root / "validation/chwirut1-native-holdout-protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen_before_chwirut1_native_holdout")
        self.assertEqual(protocol["fold_rule"]["unique_x"], {
            "1": [0.5, 0.625, 0.75, 0.875, 1.0],
            "2": [1.25, 1.5, 1.75, 2.0, 2.25],
            "3": [2.5, 2.75, 3.0, 3.25],
            "4": [3.75, 4.0, 4.25, 4.75],
            "5": [5.0, 5.25, 5.75, 6.0],
        })
        amendment = json.loads((root / "validation/chwirut1-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
        self.assertEqual(amendment["original_protocol"]["sha256"], "735228da3c0eb4729b922d8e312b59844030a63ba360d502068bca28da695237")
        self.assertEqual(amendment["correction"]["corrected_observation_counts"], [57, 54, 51, 23, 29])
        self.assertFalse(amendment["decision"]["fold_assignments_changed"])
        self.assertTrue(protocol["dataset_scope"]["related_prior_dataset"]["same_native_model_family"])
        self.assertFalse(protocol["decision"]["independent_model_family_claimed"])


if __name__ == "__main__":
    unittest.main()

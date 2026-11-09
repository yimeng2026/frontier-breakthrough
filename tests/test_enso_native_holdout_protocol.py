import json
import unittest
from pathlib import Path


class EnsoNativeHoldoutProtocolTests(unittest.TestCase):
    def test_enso_native_protocol_freezes_model_and_folds(self):
        root = Path(__file__).resolve().parents[1]
        protocol = json.loads((root / "validation/enso-native-holdout-protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen_before_enso_native_holdout")
        self.assertEqual(protocol["native_rule"]["parameters"], ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"])
        self.assertEqual(protocol["fold_rule"]["ranges"], {"1": [1, 34], "2": [35, 68], "3": [69, 102], "4": [103, 135], "5": [136, 168]})
        self.assertFalse(protocol["decision"]["certified_full_fit_used_as_holdout"])
        self.assertFalse(protocol["decision"]["rational_bounds_transferred_to_native"])


if __name__ == "__main__":
    unittest.main()

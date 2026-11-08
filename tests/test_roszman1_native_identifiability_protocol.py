import json
import unittest
from pathlib import Path


class Roszman1NativeIdentifiabilityProtocolTests(unittest.TestCase):
    def test_native_identifiability_protocol_is_frozen(self):
        root = Path(__file__).resolve().parents[1]
        protocol = json.loads((root / "validation/roszman1-native-identifiability-protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen_before_roszman1_native_identifiability")
        self.assertEqual(protocol["inputs"]["native_holdout"]["sha256"], "c8678e4635a23a9bf7a59233259c48c4307911df4dd50cf6e102cc8cb975e90e")
        self.assertEqual(protocol["jacobian_rule"]["parameter_order"], ["b1", "b2", "b3", "b4"])
        self.assertEqual(protocol["jacobian_rule"]["train_points_per_fold"], 20)
        self.assertFalse(protocol["decision"]["refit"])
        self.assertFalse(protocol["decision"]["global_structural_identifiability_proved"])


if __name__ == "__main__":
    unittest.main()

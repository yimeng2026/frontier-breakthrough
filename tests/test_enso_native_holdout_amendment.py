import json
import unittest
from pathlib import Path


class EnsoNativeHoldoutAmendmentTests(unittest.TestCase):
    def test_amendment_preserves_original_optimizer_mismatch(self):
        root = Path(__file__).resolve().parents[1]
        amendment = json.loads((root / "validation/enso-native-holdout-protocol-amendment-01.json").read_text(encoding="utf-8"))
        self.assertEqual(amendment["original_protocol"]["sha256"], "94d91a09b48ecc2c8904ce51e0507a4ad0d85e4f330d5b78374734c3b4eb8cc4")
        self.assertFalse(amendment["trigger"]["original_tolerances_relaxed"])
        self.assertFalse(amendment["decision"]["optimizer_mismatch_hidden"])
        self.assertEqual(amendment["certified_forward_rule"]["evidence_class"], "known_answer_forward_evaluation_not_optimizer_or_holdout")


if __name__ == "__main__":
    unittest.main()

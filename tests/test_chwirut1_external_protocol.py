import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PROTOCOL = ROOT / "validation/chwirut1-ellipsoid-coverage-protocol.json"

from external_coverage import load_observations


class Chwirut1ExternalProtocolTests(unittest.TestCase):
    def load_protocol(self):
        self.assertTrue(PROTOCOL.is_file(), f"Missing frozen Chwirut1 protocol: {PROTOCOL}")
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_raw_data_is_frozen(self):
        protocol = self.load_protocol()
        raw = ROOT / "data/Chwirut1.dat"
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), protocol["dataset_scope"]["sha256"])
        x, y = load_observations(raw, 214, protocol["dataset_scope"]["sha256"])
        self.assertEqual((len(x), len(y)), (214, 214))
        self.assertEqual((x[0], y[0], x[-1], y[-1]), (0.5, 92.9, 1.75, 28.95))
        self.assertEqual(len(set(x)), 22)

    def test_protocol_freezes_related_but_untouched_external_scope(self):
        protocol = self.load_protocol()
        scope = protocol["dataset_scope"]
        self.assertEqual(protocol["status"], "frozen_before_any_chwirut1_rational_fit")
        self.assertEqual(protocol["analysis_id"], "chwirut1")
        self.assertEqual(scope["observations"], 214)
        self.assertTrue(scope["observed_data"])
        self.assertFalse(scope["generated_data"])
        self.assertFalse(scope["dataset_used_to_design_previous_regions"])
        self.assertEqual(scope["native_equation"], "y = exp(-b1*x)/(b2+b3*x) + e")
        self.assertEqual(scope["related_prior_dataset"]["name"], "Chwirut2")
        self.assertTrue(scope["related_prior_dataset"]["same_study"])
        self.assertTrue(scope["related_prior_dataset"]["same_native_model_family"])
        self.assertFalse(protocol["decision"]["independent_model_family_claimed"])
        self.assertFalse(protocol["decision"]["independent_physical_experiment_claimed"])

    def test_protocol_freezes_existing_driver_and_new_wrapper(self):
        protocol = self.load_protocol()
        implementation = protocol["implementation_rule"]
        for key in ["driver", "wrapper"]:
            path = ROOT / implementation[key]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), implementation[f"{key}_sha256"])
        self.assertEqual(protocol["fold_rule"]["count"], 5)
        self.assertEqual(protocol["ellipsoid_rule"]["radius"], 1)
        self.assertEqual(protocol["candidate_rule"]["starts_source"], "validation/hahn1-high-temperature-protocol.json")
        self.assertTrue(protocol["output_rule"]["refuse_overwrite"])
        self.assertIn("No model, start, radius, fold or threshold changes after seeing outcomes", protocol["candidate_rule"]["retuning"])


if __name__ == "__main__":
    unittest.main()

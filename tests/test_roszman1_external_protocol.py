import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PROTOCOL = ROOT / "validation/roszman1-ellipsoid-coverage-protocol.json"

from external_coverage import load_observations


class Roszman1ExternalProtocolTests(unittest.TestCase):
    def load_protocol(self):
        self.assertTrue(PROTOCOL.is_file(), f"Missing frozen Roszman1 protocol: {PROTOCOL}")
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_raw_data_is_frozen(self):
        protocol = self.load_protocol()
        raw = ROOT / "data/Roszman1.dat"
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), protocol["dataset_scope"]["sha256"])
        x, y = load_observations(raw, 25, protocol["dataset_scope"]["sha256"])
        self.assertEqual((len(x), len(y)), (25, 25))
        self.assertEqual((x[0], y[0], x[-1], y[-1]), (-4868.68, 0.252429, -464.17, 0.624169))
        self.assertEqual(len(set(x)), 25)

    def test_protocol_freezes_new_arctangent_model_scope(self):
        protocol = self.load_protocol()
        scope = protocol["dataset_scope"]
        self.assertEqual(protocol["status"], "frozen_before_any_roszman1_rational_fit")
        self.assertEqual(protocol["analysis_id"], "roszman1")
        self.assertEqual(scope["observations"], 25)
        self.assertTrue(scope["observed_data"])
        self.assertFalse(scope["generated_data"])
        self.assertFalse(scope["dataset_used_to_design_previous_regions"])
        self.assertIn("Four-parameter arctangent class", scope["native_model"])
        self.assertEqual(scope["native_equation"], "y = b1 - b2*x - arctan(b3/(x-b4))/pi + e")
        self.assertIn("Roszman1 four-parameter arctangent", protocol["candidate_rule"]["scope_limitation"])
        self.assertFalse(protocol["decision"]["independent_model_family_claimed"])
        self.assertFalse(protocol["decision"]["independent_physical_experiment_claimed"])

    def test_protocol_freezes_driver_adapter_and_wrapper(self):
        protocol = self.load_protocol()
        implementation = protocol["implementation_rule"]
        for key in ["driver", "scope_adapter", "wrapper"]:
            path = ROOT / implementation[key]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), implementation[f"{key}_sha256"])
        self.assertEqual(protocol["fold_rule"]["count"], 5)
        self.assertEqual(protocol["ellipsoid_rule"]["radius"], 1)
        self.assertEqual(protocol["candidate_rule"]["starts_source"], "validation/hahn1-high-temperature-protocol.json")
        self.assertTrue(protocol["output_rule"]["refuse_overwrite"])


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from external_coverage import load_observations


class Gauss1ExternalProtocolTests(unittest.TestCase):
    def test_raw_data_is_frozen(self):
        protocol = json.loads((ROOT / "validation/gauss1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
        raw = ROOT / "data/Gauss1.dat"
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), protocol["dataset_scope"]["sha256"])
        x, y = load_observations(raw, 250, protocol["dataset_scope"]["sha256"])
        self.assertEqual((len(x), len(y)), (250, 250))
        self.assertEqual((x[0], y[0], x[-1], y[-1]), (1.0, 97.62227, 250.0, 4.875359))

    def test_protocol_freezes_external_stress_test(self):
        protocol = json.loads((ROOT / "validation/gauss1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen_before_any_gauss1_rational_fit")
        self.assertEqual(protocol["analysis_id"], "gauss1")
        self.assertEqual(protocol["dataset_scope"]["observations"], 250)
        self.assertFalse(protocol["dataset_scope"]["dataset_used_to_design_previous_regions"])
        self.assertTrue(protocol["dataset_scope"]["generated_data"])
        self.assertIn("two well-separated Gaussians", protocol["dataset_scope"]["native_model"])
        self.assertEqual(protocol["fold_rule"]["count"], 5)
        self.assertEqual(protocol["ellipsoid_rule"]["radius"], 1)
        self.assertEqual(protocol["candidate_rule"]["starts_source"], "validation/hahn1-high-temperature-protocol.json")
        self.assertIn("No model, start, radius, fold or threshold changes after seeing outcomes", protocol["candidate_rule"]["retuning"])
        self.assertFalse(protocol["decision"]["native_physical_model_claimed"])
        self.assertFalse(protocol["decision"]["probability_calibration_claimed"])
        self.assertFalse(protocol["decision"]["independent_physical_experiment_claimed"])


if __name__ == "__main__":
    unittest.main()

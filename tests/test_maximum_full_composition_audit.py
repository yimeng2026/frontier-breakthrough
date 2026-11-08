import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_maximum_full_composition_audit.py"


class MaximumFullCompositionAuditTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing maximum/full composition audit builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_maximum_full_composition_audit", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_nine_dataset_maximum_and_majority_classes_are_distinguished(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["dataset_count"], 9)
        self.assertEqual(totals["maximum_matches_majority_count"], 8)
        self.assertEqual(totals["maximum_majority_mismatch_dataset_ids"], ["gauss1"])
        self.assertEqual(totals["maximum_prediction_shift_dominant_count"], 8)
        self.assertEqual(totals["maximum_snapshot_residual_dominant_count"], 1)
        self.assertEqual(totals["maximum_snapshot_residual_dominant_dataset_ids"], ["enso"])
        self.assertFalse(summary["decision"]["unified_mechanism_claimed"])
        self.assertFalse(summary["decision"]["probability_representativeness_claimed"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_maximum_share_median_gap_and_bound_ratio_are_not_collapsed(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["maximum_share_below_median_count"], 6)
        self.assertEqual(totals["maximum_share_below_median_dataset_ids"], ["hahn1", "thurber", "kirby2", "misra1a", "chwirut1", "enso"])
        self.assertEqual(totals["maximum_share_above_median_dataset_ids"], ["filip", "mgh17", "gauss1"])
        self.assertEqual(totals["largest_bound_to_median_ratio_dataset_id"], "gauss1")
        self.assertAlmostEqual(totals["largest_bound_to_median_ratio"], 82.99437100729904, places=10)
        datasets = {item["id"]: item for item in summary["datasets"]}
        gauss1 = datasets["gauss1"]
        self.assertFalse(gauss1["maximum_matches_majority"])
        self.assertAlmostEqual(gauss1["maximum_share_minus_median"], 0.8061359540880043, places=12)
        self.assertAlmostEqual(gauss1["maximum_share_descriptive_percentile"], 0.9947368421052631, places=12)
        enso = datasets["enso"]
        self.assertTrue(enso["maximum_matches_majority"])
        self.assertAlmostEqual(enso["maximum_share_minus_median"], -0.1700867457401684, places=12)
        self.assertAlmostEqual(enso["maximum_share_descriptive_percentile"], 2 / 15, places=12)
        self.assertAlmostEqual(enso["bound_max_to_median_ratio"], 3.7092984382603453, places=12)
        for item in summary["datasets"]:
            self.assertTrue(math.isclose(item["maximum_share_descriptive_percentile"], item["share_less_than_or_equal_maximum_count"] / item["available_point_count"], rel_tol=1e-12))
            self.assertTrue(math.isclose(item["bound_max_to_median_ratio"], item["maximum_residual_upper_bound"] / item["median_residual_upper_bound"], rel_tol=1e-12))

    def test_final_outputs_are_real_and_current(self):
        module = self.load_module()
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(module.analyze(), stored)
        self.assertEqual(module.validate_summary(stored), [])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

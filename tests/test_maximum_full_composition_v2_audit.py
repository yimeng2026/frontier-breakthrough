import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_maximum_full_composition_audit_v2.py"


class MaximumFullCompositionV2AuditTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing ten-dataset audit builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_maximum_full_composition_audit_v2", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_ten_dataset_maximum_and_majority_classes_are_distinguished(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["dataset_count"], 10)
        self.assertEqual(totals["maximum_matches_majority_count"], 9)
        self.assertEqual(totals["maximum_majority_mismatch_dataset_ids"], ["gauss1"])
        self.assertEqual(totals["maximum_prediction_shift_dominant_count"], 9)
        self.assertEqual(totals["maximum_snapshot_residual_dominant_dataset_ids"], ["enso"])
        self.assertEqual(totals["maximum_share_below_median_count"], 6)
        self.assertEqual(totals["maximum_share_above_median_dataset_ids"], ["filip", "mgh17", "gauss1", "roszman1"])
        self.assertEqual(totals["largest_bound_to_median_ratio_dataset_id"], "gauss1")
        self.assertAlmostEqual(totals["largest_bound_to_median_ratio"], 82.99437100729904, places=10)
        self.assertFalse(summary["analysis_scope"]["roszman1_native_arctangent_model_claimed"])
        self.assertFalse(summary["analysis_scope"]["roszman1_independent_physical_experiment"])
        self.assertFalse(summary["decision"]["maximum_point_used_as_typical_claimed"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_roszman1_small_sample_extreme_metrics_are_explicit(self):
        module = self.load_module()
        summary = module.analyze()
        item = next(item for item in summary["datasets"] if item["id"] == "roszman1")
        self.assertEqual(item["available_point_count"], 5)
        self.assertTrue(item["maximum_matches_majority"])
        self.assertAlmostEqual(item["median_shift_share"], 0.9933691737124666, places=15)
        self.assertAlmostEqual(item["maximum_shift_share"], 0.9978338090532987, places=15)
        self.assertAlmostEqual(item["maximum_share_minus_median"], 0.004464635340832079, places=15)
        self.assertEqual(item["share_less_than_or_equal_maximum_count"], 5)
        self.assertEqual(item["maximum_share_descriptive_percentile"], 1.0)
        self.assertAlmostEqual(item["bound_max_to_median_ratio"], 1.2203221902706693, places=12)
        self.assertIn("only in fold 2", " ".join(summary["limitations"]))

    def test_ten_dataset_figure_titles_are_dynamic(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.FIGURE = Path(directory) / "figure.png"
            module.render_figure(module.analyze())
            self.assertIn("9/10 match", plt.gcf().axes[0].get_title())
            self.assertIn("6 below", plt.gcf().axes[1].get_title())
        plt.close("all")

    def test_final_outputs_are_real_and_current(self):
        module = self.load_module()
        stored = json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(module.analyze(), stored)
        self.assertEqual(module.validate_summary(stored), [])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

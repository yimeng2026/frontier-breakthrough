import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_internal_external_bound_comparison.py"


class InternalExternalBoundComparisonTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing internal/external comparison builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_internal_external_bound_comparison", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_combined_counts_preserve_all_available_points(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["ellipsoid_available_point_count"], 674)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 482)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 192)
        self.assertEqual(totals["external_unavailable_point_count"], 60)
        self.assertEqual(totals["internal_unavailable_rooted_fold_count"], 2)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual(totals["undefined_zero_bound_count"], 0)
        self.assertEqual(module.validate_summary(summary), [])

    def test_six_distributions_and_scope_boundaries_remain_separate(self):
        module = self.load_module()
        summary = module.analyze()
        self.assertEqual([item["id"] for item in summary["datasets"]], ["hahn1", "thurber", "kirby2", "filip", "mgh17", "gauss1"])
        self.assertEqual(summary["analysis_scope"]["external_total_point_count"], 365)
        self.assertFalse(summary["decision"]["combined_success_rate_claimed"])
        self.assertFalse(summary["decision"]["universal_internal_external_ranking_claimed"])
        self.assertFalse(summary["decision"]["scope_difference_erased"])

    def test_final_outputs_are_real(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

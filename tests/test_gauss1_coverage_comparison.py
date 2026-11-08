import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_gauss1_coverage_comparison.py"


class Gauss1CoverageComparisonTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing three-dataset comparison builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_gauss1_coverage_comparison", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_three_dataset_comparison_retains_unavailable_points(self):
        module = self.load_builder()
        summary = module.analyze()
        self.assertEqual(module.validate_summary(summary), [])
        totals = summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["point_count"], 365)
        self.assertEqual(totals["ellipsoid_available_point_count"], 305)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 60)
        self.assertEqual(totals["covered_point_count"], 305)
        self.assertNotEqual(totals["covered_point_count"], totals["point_count"])
        self.assertEqual(totals["coverage_violation_count"], 0)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["continuous_safe_fold_count"], 13)
        self.assertEqual(totals["independent_box_continuous_safe_fold_count"], 7)
        self.assertEqual(totals["optimizer_failure_count"], 0)
        gauss1 = next(item for item in summary["datasets"] if item["id"] == "gauss1")
        self.assertEqual(gauss1["totals"]["ellipsoid_available_point_count"], 190)
        self.assertEqual(gauss1["totals"]["continuous_safe_fold_count"], 3)
        self.assertEqual(gauss1["totals"]["independent_box_continuous_safe_fold_count"], 2)

    def test_comparison_is_posthoc_and_not_a_success_rate(self):
        module = self.load_builder()
        summary = module.analyze()
        self.assertFalse(summary["analysis_scope"]["refit"])
        self.assertFalse(summary["analysis_scope"]["independent_physical_experiment"])
        self.assertFalse(summary["decision"]["universal_external_success_rate_claimed"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertIn("60 points without an available ellipsoid bound", " ".join(summary["limitations"]))


if __name__ == "__main__":
    unittest.main()

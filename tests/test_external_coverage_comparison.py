import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_external_coverage_comparison import OUT, analyze, validate_summary


class ExternalCoverageComparisonTests(unittest.TestCase):
    def test_comparison_retains_dataset_specific_evidence(self):
        summary = analyze()
        self.assertEqual(validate_summary(summary), [])
        self.assertEqual(summary["totals"]["dataset_count"], 2)
        self.assertEqual(summary["totals"]["point_count"], 115)
        self.assertEqual(summary["totals"]["covered_point_count"], 115)
        self.assertEqual(summary["totals"]["continuous_safe_fold_count"], 10)
        filip = next(item for item in summary["datasets"] if item["id"] == "filip")
        mgh17 = next(item for item in summary["datasets"] if item["id"] == "mgh17")
        self.assertEqual(filip["totals"]["independent_box_continuous_safe_fold_count"], 0)
        self.assertEqual(mgh17["totals"]["independent_box_continuous_safe_fold_count"], 5)
        self.assertEqual(mgh17["totals"]["tighter_point_count"], 32)

    def test_comparison_does_not_create_universal_external_success_rate(self):
        summary = analyze()
        self.assertFalse(summary["decision"]["universal_external_success_rate_claimed"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertTrue(summary["analysis_scope"]["candidate_models_not_native"])


if __name__ == "__main__":
    unittest.main()

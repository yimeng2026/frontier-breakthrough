import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_filip_ellipsoid_coverage import OUT, analyze, load_filip_data, validate_summary


class FilipEllipsoidCoverageTests(unittest.TestCase):
    def test_raw_data_has_82_observations(self):
        x, y = load_filip_data(ROOT / "data/Filip.dat", "403b34689e401d915cb28bd69311d3ca5c3007d88d3b670b00e3203042315072")
        self.assertEqual((len(x), len(y)), (82, 82))
        self.assertEqual((x[0], y[0]), (-6.860120914, 0.8116))

    def test_every_available_residual_bound_covers_actual_residual(self):
        summary = analyze()
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual(summary["totals"]["point_count"], 82)
        self.assertEqual(summary["totals"]["ellipsoid_available_point_count"], 82)
        self.assertEqual(summary["totals"]["covered_point_count"], 82)
        self.assertIsNotNone(summary["totals"]["max_ellipsoid_absolute_residual_upper_bound_float"])
        for case in summary["folds"]:
            for point in case["point_results"]:
                if point["ellipsoid_available"]:
                    self.assertGreaterEqual(point["ellipsoid_absolute_residual_upper_bound_float"] + 1.0e-9, point["actual_absolute_residual"])
                if point["coverage_violation"] is not None:
                    self.assertLessEqual(point["coverage_violation"], 1)

    def test_final_report_preserves_candidate_and_coverage_boundaries(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertTrue(summary["analysis_scope"]["candidate_model_not_native"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["native_physical_model_claimed"])


if __name__ == "__main__":
    unittest.main()

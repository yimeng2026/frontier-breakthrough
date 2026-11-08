import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_mgh17_ellipsoid_coverage import OUT, analyze, load_mgh17_data, validate_summary


class MGH17EllipsoidCoverageTests(unittest.TestCase):
    def test_raw_data_has_33_observations(self):
        x, y = load_mgh17_data(ROOT / "data/MGH17.dat", "75edb5522ee639794ae1f0d0f4a1e3638e963c6854888b853e1f45cea3c2f4d7")
        self.assertEqual((len(x), len(y)), (33, 33))
        self.assertEqual((x[0], y[0]), (0.0, 0.844))

    def test_every_available_residual_bound_covers_actual_residual(self):
        summary = analyze()
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual(summary["totals"]["point_count"], 33)
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

    def test_final_report_labels_ellipsoid_over_box_ratio_correctly(self):
        report = (ROOT / "docs/EXTERNAL_COVERAGE_2026-11-09.md").read_text(encoding="utf-8")
        self.assertIn("| 椭球／盒中位比值 | 不可比 | 0.613908 |", report)
        self.assertNotIn("| 盒／椭球中位比值 |", report)


if __name__ == "__main__":
    unittest.main()

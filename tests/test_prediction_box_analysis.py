import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_prediction_box_bounds import OUT, analyze, validate_summary


class PredictionBoxAnalysisTests(unittest.TestCase):
    def test_all_certified_cases_have_pointwise_exact_bounds(self):
        summary = analyze()
        self.assertEqual(len(summary["cases"]), 15)
        self.assertEqual(summary["totals"]["bounded_fold_count"], 13)
        self.assertEqual(summary["totals"]["unbounded_rooted_fold_count"], 2)
        self.assertEqual(summary["totals"]["bounded_point_count"], 369)
        for case in summary["cases"]:
            if not case["bounds_available"]:
                continue
            previous = None
            for point in case["point_bounds"]:
                self.assertGreater(point["denominator_lower_bound_float"], 0)
                self.assertGreaterEqual(point["prediction_shift_upper_bound_float"], 0)
                self.assertGreaterEqual(point["absolute_residual_upper_bound_float"], 0)
                if previous is not None:
                    self.assertGreaterEqual(point["x"], previous)
                previous = point["x"]

    def test_final_report_preserves_conservative_bound_scope(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertFalse(summary["decision"]["probabilistic_interval_claimed"])
        self.assertFalse(summary["decision"]["continuous_x_bound_claimed"])
        self.assertFalse(summary["decision"]["rooted_cases_silently_bounded"])


if __name__ == "__main__":
    unittest.main()

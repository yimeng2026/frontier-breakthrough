import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_ellipsoid_box_comparison import OUT, analyze, validate_summary


class EllipsoidBoxComparisonTests(unittest.TestCase):
    def test_every_point_is_compared_or_explicitly_unavailable(self):
        summary = analyze()
        totals = summary["totals"]
        self.assertEqual(len(summary["cases"]), 15)
        self.assertEqual(totals["comparison_point_count"] + totals["unavailable_point_count"], 369)
        self.assertEqual(totals["unavailable_rooted_fold_count"], 2)
        self.assertGreater(totals["comparison_point_count"], 0)
        for case in summary["cases"]:
            for point in case["point_comparisons"]:
                if point["ellipsoid_available"]:
                    self.assertGreater(point["denominator_lower_bound_float"], 0)
                    if point["shift_ratio_ellipsoid_over_box"] is not None:
                        self.assertGreater(point["shift_ratio_ellipsoid_over_box"], 0)

    def test_final_report_preserves_all_comparison_directions(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertFalse(summary["decision"]["confidence_ellipsoid_claimed"])
        self.assertFalse(summary["decision"]["ellipsoid_always_tighter_claimed"])
        self.assertFalse(summary["decision"]["continuous_x_root_free_claimed"])


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from external_coverage import load_observations, run_external_analysis


class ExternalCoverageTests(unittest.TestCase):
    def test_generic_driver_preserves_filip_results(self):
        x, y = load_observations(ROOT / "data/Filip.dat", 82, "403b34689e401d915cb28bd69311d3ca5c3007d88d3b670b00e3203042315072")
        self.assertEqual((len(x), len(y)), (82, 82))
        summary = run_external_analysis(ROOT / "validation/filip-ellipsoid-coverage-protocol.json", ROOT / "scripts/analyze_filip_ellipsoid_coverage.py")
        self.assertEqual(summary["status"], "computed_external_filip_ellipsoid_coverage")
        self.assertEqual(summary["totals"]["point_count"], 82)
        self.assertEqual(summary["totals"]["ellipsoid_available_point_count"], 82)
        self.assertEqual(summary["totals"]["covered_point_count"], 82)
        self.assertEqual(summary["totals"]["continuous_safe_fold_count"], 5)
        self.assertEqual(summary["totals"]["independent_box_continuous_safe_fold_count"], 0)


if __name__ == "__main__":
    unittest.main()

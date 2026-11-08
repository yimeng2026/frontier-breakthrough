import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_ellipsoid_interval_safety import OUT, analyze, validate_summary


class EllipsoidIntervalAnalysisTests(unittest.TestCase):
    def test_every_safe_case_recomputes_the_squared_certificate(self):
        summary = analyze()
        self.assertEqual(len(summary["cases"]), 15)
        self.assertEqual(summary["totals"]["rooted_snapshot_fold_count"], 2)
        for case in summary["cases"]:
            if case["continuous_ellipsoid_safe"]:
                self.assertTrue(case["snapshot_safe"])
                self.assertEqual(case["support_polynomial_root_count"], 0)
            if not case["snapshot_safe"]:
                self.assertFalse(case["continuous_ellipsoid_safe"])

    def test_final_report_does_not_call_non_certification_unsafe(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertFalse(summary["decision"]["non_certification_called_unsafe"])
        self.assertFalse(summary["decision"]["confidence_or_probability_claimed"])
        self.assertFalse(summary["decision"]["pointwise_check_substituted_for_interval"])


if __name__ == "__main__":
    unittest.main()

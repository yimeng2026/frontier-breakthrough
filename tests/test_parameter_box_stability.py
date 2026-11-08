import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_parameter_box_stability import OUT, analyze, validate_summary
from box_stability import certified_box_safe


class ParameterBoxStabilityTests(unittest.TestCase):
    def test_every_reported_radius_has_an_exact_certificate(self):
        summary = analyze()
        json.dumps(summary, ensure_ascii=False)
        self.assertEqual(len(summary["cases"]), 15)
        self.assertEqual(summary["totals"]["snapshot_safe_fold_count"], 13)
        self.assertEqual(summary["totals"]["rooted_snapshot_fold_count"], 2)
        for case in summary["cases"]:
            coefficients = case["denominator_coefficients"]
            scales = case["local_standard_error_scales"]
            lower, upper = case["closed_interval"]
            if case["snapshot_safe"]:
                radius = case["certified_radius_lower_bound_float"]
                self.assertTrue(certified_box_safe(coefficients, scales, lower, upper, radius))
                if case["uncertified_radius_upper_bound_float"] is not None:
                    self.assertFalse(certified_box_safe(coefficients, scales, lower, upper, case["uncertified_radius_upper_bound_float"]))
            else:
                self.assertFalse(case["certified_region_safe"])

    def test_final_report_preserves_conservative_interpretation(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertFalse(summary["decision"]["probability_or_confidence_region_claimed"])
        self.assertFalse(summary["decision"]["uncertified_upper_bound_called_unsafe"])
        self.assertFalse(summary["decision"]["global_root_free_claimed"])


if __name__ == "__main__":
    unittest.main()

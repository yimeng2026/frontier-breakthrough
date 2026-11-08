import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_extreme_reporting.py"
AUDIT = ROOT / "exports/maximum-full-composition-audit.json"
RULES = ROOT / "contracts/extreme-reporting.rules.json"
CHECK = ROOT / "validation/extreme-reporting-check.json"


class ExtremeReportingTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing extreme reporting validator: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("validate_extreme_reporting", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def valid_summary(self):
        return json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_frozen_audit_passes_mechanism_interpretation_level(self):
        module = self.load_module()
        self.assertEqual(module.validate_report(self.valid_summary(), "mechanism_interpretation"), [])

    def test_maximum_only_level_does_not_require_distribution_metrics(self):
        module = self.load_module()
        summary = self.valid_summary()
        summary["totals"] = {"dataset_count": 1}
        summary["datasets"] = [{key: summary["datasets"][0][key] for key in ["id", "available_point_count", "maximum_dominant", "maximum_shift_share", "maximum_residual_upper_bound"]}]
        self.assertEqual(module.validate_report(summary, "maximum_only"), [])

    def test_distribution_summary_requires_median(self):
        module = self.load_module()
        summary = copy.deepcopy(self.valid_summary())
        del summary["datasets"][0]["median_shift_share"]
        errors = module.validate_report(summary, "distribution_summary")
        self.assertTrue(any("median_shift_share" in error for error in errors))

    def test_mechanism_interpretation_requires_valid_percentile(self):
        module = self.load_module()
        summary = copy.deepcopy(self.valid_summary())
        del summary["datasets"][-1]["maximum_share_descriptive_percentile"]
        errors = module.validate_report(summary, "mechanism_interpretation")
        self.assertTrue(any("maximum_share_descriptive_percentile" in error for error in errors))
        summary = self.valid_summary()
        summary["datasets"][-1]["maximum_share_descriptive_percentile"] = 0
        errors = module.validate_report(summary, "mechanism_interpretation")
        self.assertTrue(any("maximum_share_descriptive_percentile" in error for error in errors))

    def test_typical_and_probability_claims_are_rejected(self):
        module = self.load_module()
        summary = self.valid_summary()
        summary["decision"]["maximum_point_used_as_typical_claimed"] = True
        summary["decision"]["probability_representativeness_claimed"] = True
        errors = module.validate_report(summary, "mechanism_interpretation")
        self.assertTrue(any("maximum_point_used_as_typical_claimed" in error for error in errors))
        self.assertTrue(any("probability_representativeness_claimed" in error for error in errors))

    def test_ratio_and_majority_mismatches_are_rejected(self):
        module = self.load_module()
        summary = self.valid_summary()
        gauss1 = next(item for item in summary["datasets"] if item["id"] == "gauss1")
        gauss1["bound_max_to_median_ratio"] = 0.5
        gauss1["maximum_matches_majority"] = True
        errors = module.validate_report(summary, "distribution_summary")
        self.assertTrue(any("bound_max_to_median_ratio" in error for error in errors))
        self.assertTrue(any("maximum_matches_majority" in error for error in errors))

    def test_final_check_file_is_current(self):
        module = self.load_module()
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "passed")
        self.assertEqual(stored["claim_level"], "mechanism_interpretation")
        self.assertEqual(stored["dataset_count"], 9)
        self.assertEqual(stored["error_count"], 0)
        self.assertEqual(stored["report_sha256"], hashlib.sha256(AUDIT.read_bytes()).hexdigest())
        self.assertEqual(stored["rules_sha256"], hashlib.sha256(RULES.read_bytes()).hexdigest())
        self.assertEqual(stored["validator_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertFalse(stored["decision"]["maximum_point_used_as_typical_claimed"])


if __name__ == "__main__":
    unittest.main()

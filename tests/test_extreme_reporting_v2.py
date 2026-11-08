import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/validate_extreme_reporting_v2.py"
BASE_SCRIPT = ROOT / "scripts/validate_extreme_reporting.py"
AUDIT = ROOT / "exports/maximum-full-composition-audit-v2.json"
RULES = ROOT / "contracts/extreme-reporting.rules.json"
CHECK = ROOT / "validation/extreme-reporting-v2-check.json"


class ExtremeReportingV2Tests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 extreme reporting validator: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("validate_extreme_reporting_v2", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def valid_summary(self):
        return json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_v2_passes_all_three_claim_levels(self):
        module = self.load_module()
        summary = self.valid_summary()
        self.assertEqual(module.validate_v2_report(summary, "mechanism_interpretation"), [])
        reduced = copy.deepcopy(summary)
        reduced["totals"] = {"dataset_count": 1}
        reduced["datasets"] = [{key: summary["datasets"][0][key] for key in ["id", "available_point_count", "maximum_dominant", "maximum_shift_share", "maximum_residual_upper_bound"]}]
        self.assertEqual(module.validate_v2_report(reduced, "maximum_only"), [])
        self.assertEqual(module.validate_v2_report(summary, "distribution_summary"), [])

    def test_v2_rejects_bad_percentile_and_typicality_claims(self):
        module = self.load_module()
        summary = self.valid_summary()
        summary["datasets"][-1]["maximum_share_descriptive_percentile"] = 0
        summary["decision"]["maximum_point_used_as_typical_claimed"] = True
        summary["decision"]["probability_representativeness_claimed"] = True
        errors = module.validate_v2_report(summary, "mechanism_interpretation")
        self.assertTrue(any("maximum_share_descriptive_percentile" in error for error in errors))
        self.assertTrue(any("maximum_point_used_as_typical_claimed" in error for error in errors))
        self.assertTrue(any("probability_representativeness_claimed" in error for error in errors))

    def test_v2_distribution_level_requires_median(self):
        module = self.load_module()
        summary = self.valid_summary()
        del summary["datasets"][0]["median_shift_share"]
        errors = module.validate_v2_report(summary, "distribution_summary")
        self.assertTrue(any("median_shift_share" in error for error in errors))

    def test_final_v2_check_is_current_and_preserves_old_receipt(self):
        module = self.load_module()
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        self.assertEqual(module.build_check(), stored)
        self.assertEqual(stored["status"], "passed")
        self.assertEqual(stored["claim_level"], "mechanism_interpretation")
        self.assertEqual(stored["dataset_count"], 10)
        self.assertEqual(stored["error_count"], 0)
        self.assertEqual(stored["report_sha256"], hashlib.sha256(AUDIT.read_bytes()).hexdigest())
        self.assertEqual(stored["rules_sha256"], hashlib.sha256(RULES.read_bytes()).hexdigest())
        self.assertEqual(stored["validator_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(stored["base_validator_sha256"], hashlib.sha256(BASE_SCRIPT.read_bytes()).hexdigest())
        old = json.loads((ROOT / "validation/extreme-reporting-check.json").read_text(encoding="utf-8"))
        self.assertEqual(old["dataset_count"], 9)


if __name__ == "__main__":
    unittest.main()

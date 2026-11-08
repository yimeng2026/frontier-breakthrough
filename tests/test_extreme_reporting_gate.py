import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class ExtremeReportingGateTests(unittest.TestCase):
    def setUp(self):
        import build_frontier_word as base
        self.assertTrue(hasattr(base, "enforce_extreme_reporting_gate"), "Missing pre-build extreme reporting gate")
        self.base = base
        self.previous_mode = base.REPORT_MODE

    def tearDown(self):
        self.base.REPORT_MODE = self.previous_mode

    def test_gate_accepts_all_three_extreme_modes(self):
        self.assertTrue(hasattr(self.base, "enforce_extreme_reporting_gate"), "Missing pre-build extreme reporting gate")
        for mode in ["maximum_full_composition", "extreme_reporting", "extreme_corpus"]:
            self.base.REPORT_MODE = mode
            self.assertIsNone(self.base.enforce_extreme_reporting_gate())

    def test_gate_rejects_invalid_extreme_summary_before_build(self):
        self.base.REPORT_MODE = "extreme_reporting"
        summary = json.loads((ROOT / "exports/maximum-full-composition-audit.json").read_text(encoding="utf-8"))
        summary = copy.deepcopy(summary)
        summary["decision"]["maximum_point_used_as_typical_claimed"] = True
        with self.assertRaisesRegex(ValueError, "maximum_point_used_as_typical_claimed"):
            self.base.enforce_extreme_reporting_gate(summary=summary)

    def test_gate_rejects_incomplete_corpus_before_build(self):
        self.base.REPORT_MODE = "extreme_corpus"
        with self.assertRaises(ValueError):
            self.base.enforce_extreme_reporting_gate(corpus_text="")

    def test_non_extreme_mode_is_unchanged(self):
        self.base.REPORT_MODE = "enso_coverage"
        self.assertIsNone(self.base.enforce_extreme_reporting_gate())


if __name__ == "__main__":
    unittest.main()

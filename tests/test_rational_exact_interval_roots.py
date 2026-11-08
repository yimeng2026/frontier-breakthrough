import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prove_rational_interval_roots import OUT, analyze_exact, validate_summary


class RationalExactIntervalRootTests(unittest.TestCase):
    def test_exact_counts_match_all_frozen_numerical_counts(self):
        cases = analyze_exact()
        self.assertEqual(len(cases), 15)
        self.assertEqual(sum(case["exact"]["root_count"] for case in cases), 3)
        self.assertEqual(sum(case["exact"]["root_count"] == 0 for case in cases), 13)
        for case in cases:
            self.assertTrue(case["exact"]["matches_numerical_count"])
            for interval in case["exact"]["isolating_intervals"]:
                self.assertGreaterEqual(interval["lower_float"], case["closed_interval"][0])
                self.assertLessEqual(interval["upper_float"], case["closed_interval"][1])
        hahn = next(case for case in cases if case["dataset"] == "hahn1" and case["fold"] == 1)
        thurber = next(case for case in cases if case["dataset"] == "thurber" and case["fold"] == 1)
        self.assertEqual(hahn["exact"]["root_count"], 2)
        self.assertEqual(thurber["exact"]["root_count"], 1)

    def test_solver_logs_have_exactly_one_terminal_newline(self):
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        for case in summary["cases"]:
            for key in ["z3_log", "cvc5_log"]:
                path = ROOT / case["solver_checks"][key]
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"), path)
                self.assertFalse(content.endswith(b"\n\n"), path)

    def test_final_report_has_dual_solver_logs_for_every_fold(self):
        self.assertTrue(OUT.is_file(), OUT)
        summary = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(validate_summary(summary), [])
        self.assertEqual(len(summary["cases"]), 15)
        self.assertEqual(summary["totals"]["z3_unsat_count"], 13)
        self.assertEqual(summary["totals"]["cvc5_unsat_count"], 13)
        self.assertEqual(summary["totals"]["z3_sat_count"], 2)
        self.assertEqual(summary["totals"]["cvc5_sat_count"], 2)
        self.assertFalse(summary["decision"]["unresolved_or_disagreement_present"])


if __name__ == "__main__":
    unittest.main()

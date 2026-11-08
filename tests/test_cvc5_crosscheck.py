import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Cvc5CrosscheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completed = subprocess.run(
            ["python", ROOT / "scripts/analyze_cvc5_crosscheck.py"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout)
        cls.result = json.loads((ROOT / "validation/cvc5-crosscheck.json").read_text(encoding="utf-8"))
        cls.checks = {item["id"]: item for item in cls.result["checks"]}

    def test_cvc5_matches_z3_on_all_three_checks(self):
        self.assertEqual(self.result["status"], "verified")
        self.assertTrue(self.result["all_results_match_z3"])
        self.assertEqual(self.checks["positive_denominator_by_contradiction"]["cvc5"], "unsat")
        self.assertEqual(self.checks["nonpositive_denominator_counterexample"]["cvc5"], "sat")
        self.assertEqual(self.checks["x_zero_parameter_nonidentifiability"]["cvc5"], "sat")

    def test_cvc5_model_preserves_two_different_parameter_triples(self):
        model_text = self.checks["x_zero_parameter_nonidentifiability"]["raw_output"]
        self.assertIn("(/ 1 10)", model_text)
        self.assertIn("(/ 1 5)", model_text)
        self.assertIn("(/ 1 50)", model_text)
        self.assertIn("(/ 3 100)", model_text)
        self.assertFalse(self.result["universal_identifiability_claimed"])

    def test_official_binary_and_logs_are_frozen(self):
        self.assertIn("cvc5 1.4.2", self.result["solver_version"])
        self.assertEqual(len(self.result["binary_sha256"]), 64)
        for check in self.result["checks"]:
            self.assertTrue((ROOT / check["log_file"]).is_file())
            self.assertTrue((ROOT / check["input_file"]).is_file())


if __name__ == "__main__":
    unittest.main()

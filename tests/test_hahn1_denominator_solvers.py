import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Hahn1DenominatorSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for python, script in [
            ("D:/research-engines/z3-env/Scripts/python.exe", ROOT / "scripts/analyze_z3_hahn1_denominator.py"),
            ("python", ROOT / "scripts/analyze_cvc5_hahn1_denominator.py"),
        ]:
            completed = subprocess.run(
                [python, script], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", timeout=120,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stdout)

    def read(self, name):
        return json.loads((ROOT / "validation" / name).read_text(encoding="utf-8"))

    def test_both_solvers_reject_positive_denominator_root(self):
        z3 = self.read("z3-hahn1-denominator.json")
        cvc5 = self.read("cvc5-hahn1-denominator.json")
        self.assertEqual(z3["result"], "unsat")
        self.assertEqual(cvc5["result"], "unsat")
        self.assertTrue(cvc5["matches_z3"])
        self.assertTrue(cvc5["denominator_positive_within_0_to_900"])
        self.assertTrue(z3["unbounded_root_exists"])

    def test_denominator_audit_has_no_real_root_in_experimental_domain(self):
        summary = self.read("hahn1-high-temperature.json")
        self.assertFalse(summary["denominator_audit"]["full_model"]["has_real_singularity_within_experimental_range"])
        self.assertEqual(summary["denominator_audit"]["full_model"]["real_roots_within_0_to_900"], [])


if __name__ == "__main__":
    unittest.main()

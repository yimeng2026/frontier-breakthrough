import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Z3_PYTHON = Path("D:/research-engines/z3-env/Scripts/python.exe")
RDKIT_PYTHON = Path("D:/research-engines/rdkit-env/Scripts/python.exe")


class NewCrosscheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for python, script in [
            (Z3_PYTHON, ROOT / "scripts/analyze_z3_identifiability.py"),
            (RDKIT_PYTHON, ROOT / "scripts/analyze_aspirin_crosscheck.py"),
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

    def test_z3_domain_and_counterexamples(self):
        result = self.read("z3-identifiability.json")
        self.assertEqual(result["status"], "verified")
        checks = {item["id"]: item for item in result["checks"]}
        self.assertEqual(checks["positive_denominator_by_contradiction"]["result"], "unsat")
        self.assertEqual(checks["nonpositive_denominator_counterexample"]["result"], "sat")
        self.assertEqual(checks["x_zero_parameter_nonidentifiability"]["result"], "sat")
        self.assertNotEqual(
            checks["x_zero_parameter_nonidentifiability"]["model"]["b1"],
            checks["x_zero_parameter_nonidentifiability"]["model"]["a1"],
        )
        self.assertFalse(result["universal_identifiability_claimed"])

    def test_aspirin_identity_and_recomputed_properties(self):
        result = self.read("aspirin-crosscheck.json")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["pubchem_cid"], 2244)
        self.assertEqual(result["chembl_id"], "CHEMBL25")
        self.assertTrue(result["canonical_structure_identical"])
        self.assertTrue(result["inchikey_identical"])
        self.assertEqual(result["rdkit"]["formula"], "C9H8O4")
        self.assertAlmostEqual(result["rdkit"]["exact_mass"], float(result["pubchem"]["ExactMass"]), places=6)
        self.assertAlmostEqual(result["rdkit"]["tpsa"], float(result["pubchem"]["TPSA"]), places=6)
        self.assertEqual(result["rdkit"]["heavy_atoms"], 13)

    def test_aspirin_algorithm_differences_are_not_mislabeled(self):
        result = self.read("aspirin-crosscheck.json")
        self.assertNotEqual(result["pubchem"]["XLogP"], result["chembl_properties"]["alogp"])
        self.assertNotEqual(result["pubchem"]["RotatableBondCount"], result["chembl_properties"]["rtb"])
        self.assertIn("not fraud evidence", result["difference_interpretation"]["status"])
        self.assertFalse(result["independent_wet_experiment"])
        self.assertIn("hba", result["difference_interpretation"]["fields_not_forced_equal"])
        self.assertIn("rtb", result["difference_interpretation"]["fields_not_forced_equal"])


if __name__ == "__main__":
    unittest.main()

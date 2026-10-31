import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LocalValidationTests(unittest.TestCase):
    def read(self, name):
        return json.loads((ROOT / "validation" / f"{name}.json").read_text(encoding="utf-8"))

    def test_pysindy_known_answer(self):
        result = self.read("pysindy")
        self.assertEqual(result["status"], "verified")
        self.assertLess(result["max_abs_error"], 1e-4)
        self.assertAlmostEqual(result["coefficients"][0][0], -2.0, places=4)
        self.assertAlmostEqual(result["coefficients"][1][1], 1.0, places=4)

    def test_z3_known_answers(self):
        result = self.read("z3")
        self.assertEqual(result["status"], "verified")
        self.assertTrue(all(v == "unsat" for v in result["checks"].values()))

    def test_rdkit_external_snapshot_is_not_misrepresented(self):
        result = self.read("rdkit")
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["canonical_structure_matches_pubchem"])
        self.assertEqual(result["formula"], "C4H6N4O3S2")
        self.assertEqual(round(result["tpsa_include_S_P_A2"]), result["pubchem_tpsa_A2"])
        self.assertNotEqual(result["rdkit_crippen_mollogp"], result["pubchem_xlogp"])
        self.assertIn("算法不同", result["xlogp_algorithm_note"])

    def test_verified_registry_entries_have_result_files(self):
        payload = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
        result_files = {p.stem for p in (ROOT / "validation").glob("*.json")} - {"pubchem-acetazolamide"}
        for project in payload["projects"]:
            if project["localStatus"] == "verified":
                self.assertIn(project["id"], result_files, project["id"])


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("D:/research-engines/pymatgen-env/Scripts/python.exe")


class MaterialCrosscheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completed = subprocess.run(
            [PYTHON, ROOT / "scripts/analyze_material_crosscheck.py"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout)
        cls.result = json.loads((ROOT / "validation/material-crosscheck.json").read_text(encoding="utf-8"))
        cls.materials = {item["key"]: item for item in cls.result["materials"]}

    def test_three_structure_identities_hold(self):
        self.assertEqual(self.result["status"], "verified")
        self.assertTrue(self.result["structure_identity_confirmed"])
        self.assertEqual(set(self.materials), {"si", "gaas", "sio2"})
        self.assertEqual(self.materials["si"]["local"]["space_group_symbol"], "Fd-3m")
        self.assertEqual(self.materials["gaas"]["local"]["space_group_symbol"], "F-43m")
        self.assertEqual(self.materials["sio2"]["local"]["space_group_symbol"], "P3_121")
        for item in self.materials.values():
            self.assertGreater(item["local"]["density_g_cm3"], 0)
            self.assertEqual(item["local"]["nsites"], item["mp"]["nsites"])

    def test_dft_differences_are_quantified_not_hidden(self):
        self.assertAlmostEqual(self.materials["si"]["band_gap_difference_oqmd_minus_mp"], 0.773 - 0.6103, places=6)
        self.assertAlmostEqual(self.materials["gaas"]["band_gap_difference_oqmd_minus_mp"], 0.574 - 0.1839, places=6)
        self.assertAlmostEqual(self.materials["sio2"]["band_gap_difference_oqmd_minus_mp"], 6.054 - 5.678, places=6)
        self.assertTrue(self.result["differences_not_called_fraud"])
        self.assertFalse(self.result["global_dft_benchmark_claimed"])

    def test_id_spaces_and_experimental_boundaries_remain_separate(self):
        for item in self.materials.values():
            self.assertNotEqual(str(item["mp"]["material_id"]), str(item["oqmd"]["entry_id"]))
            self.assertNotEqual(str(item["oqmd"]["entry_id"]), item["oqmd_structure_id"])
            self.assertGreaterEqual(item["density_relative_difference_abs"], 0)
        self.assertFalse(self.result["independent_experiment"])
        self.assertTrue((ROOT / "papers/05_材料跨库复核/fig05_material_crosscheck.png").is_file())


if __name__ == "__main__":
    unittest.main()

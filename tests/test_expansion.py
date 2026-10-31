import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExpansionTests(unittest.TestCase):
    def read(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_material_structure_recomputation(self):
        result = self.read("validation/pymatgen.json")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["space_group_local"], "Fd-3m")
        self.assertEqual(result["space_group_number_local"], 227)
        self.assertLess(result["density_abs_error"], 1e-6)
        self.assertIn("未在本机重算", result["scope"])

    def test_pdb_uniprot_exact_sequence_bridge(self):
        result = self.read("validation/pdb-uniprot.json")
        pdb = self.read("validation/pdb-4hhb.json")
        uniprot = self.read("validation/uniprot-hbb.json")
        self.assertEqual(uniprot["sequence"][1:], pdb["sequence"])
        self.assertEqual(result["uniprot_accession"], "P68871")
        self.assertEqual(result["resolution_A"], 1.74)
        self.assertIn("不是蛋白功能", result["scope"])

    def test_ca2_full_length_sequence_bridge(self):
        result = self.read("validation/ca2-sequence.json")
        pdb = self.read("validation/pdb-3hs4-ca2.json")
        uniprot = self.read("validation/uniprot-ca2.json")
        self.assertEqual(result["uniprot_accession"], "P00918")
        self.assertEqual(result["pdb_entity"], 1)
        self.assertEqual(result["pdb_chain"], "A")
        self.assertEqual(result["sequence_length"], 260)
        self.assertTrue(result["exact_sequence_match"])
        self.assertEqual(pdb["sequence"], uniprot["sequence"])
        self.assertEqual(result["sequence_md5_recomputed"], "94EB709966E01FBC15DC1C46A0D03AC5")

    def test_drug_target_structure_chain(self):
        result = self.read("validation/drug-target-structure.json")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["target_chembl_id"], "CHEMBL205")
        self.assertEqual(result["target_uniprot"], "P00918")
        self.assertEqual(result["target_pdb_entity"], 1)
        self.assertTrue(result["target_sequence_exact_match"])
        self.assertEqual(result["target_sequence_length"], 260)
        self.assertEqual(result["pdb_id"], "3HS4")
        self.assertEqual(result["pdb_ligand_comp_id"], "AZM")
        self.assertEqual(result["ki_nM"], 12.0)
        self.assertAlmostEqual(result["pchembl_recomputed"], 7.92, places=2)
        self.assertEqual(result["potential_duplicate"], 1)
        self.assertIn("不外推临床效力", result["scope"])

    def test_evidence_packet_is_current_and_bounded(self):
        packet = self.read("exports/frontier-evidence.json")
        self.assertEqual(len(packet["items"]), 6)
        self.assertEqual(len({i["id"] for i in packet["items"]}), 6)
        for item in packet["items"]:
            self.assertEqual(item["status"], "verified")
            self.assertTrue(item["limitations"])
            self.assertTrue(item["upstreamContribution"])
            for snapshot in item["snapshotFiles"]:
                self.assertTrue((ROOT / snapshot).is_file())

    def test_new_agent_projects_have_primary_sources(self):
        projects = self.read("data/projects.json")["projects"]
        by_id = {p["id"]: p for p in projects}
        for pid in ("google-co-scientist", "futurehouse-robin", "kosmos", "materials-project", "rcsb-pdb", "uniprot", "chembl"):
            self.assertIn(pid, by_id)
            self.assertTrue(by_id[pid]["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()

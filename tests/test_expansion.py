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

    def test_evidence_packet_is_current_and_bounded(self):
        packet = self.read("exports/frontier-evidence.json")
        self.assertEqual(len(packet["items"]), 5)
        self.assertEqual(len({i["id"] for i in packet["items"]}), 5)
        for item in packet["items"]:
            self.assertEqual(item["status"], "verified")
            self.assertTrue(item["limitations"])
            self.assertTrue(item["upstreamContribution"])
            for snapshot in item["snapshotFiles"]:
                self.assertTrue((ROOT / snapshot).is_file())

    def test_new_agent_projects_have_primary_sources(self):
        projects = self.read("data/projects.json")["projects"]
        by_id = {p["id"]: p for p in projects}
        for pid in ("google-co-scientist", "futurehouse-robin", "kosmos", "materials-project", "rcsb-pdb", "uniprot"):
            self.assertIn(pid, by_id)
            self.assertTrue(by_id[pid]["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()

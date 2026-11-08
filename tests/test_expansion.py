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

    def test_method_aware_selectivity_analysis(self):
        result = self.read("validation/ca-selectivity.json")
        self.assertEqual(result["ca_i"]["ki_nM"], 250.0)
        self.assertEqual(result["ca_ii"]["ki_nM"], 12.0)
        self.assertEqual(result["ca_ix"]["ki_nM"], 25.0)
        self.assertAlmostEqual(result["ca_i_ii_ki_ratio"], 250.0 / 12.0)
        self.assertAlmostEqual(result["ca_ii_minus_ca_i_pchembl_delta"], 1.3187587626, places=8)
        self.assertFalse(result["ca_ix_ratio_computed"])
        self.assertIn("不是独立重复实验", result["independence"])
        self.assertIn("提示而非证明普遍选择性", result["scope"])

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

    def test_cross_document_stability_is_not_a_constant(self):
        result = self.read("validation/ca-document-stability.json")
        self.assertEqual(result["document_count"], 6)
        self.assertEqual(result["strict_method_matched_count"], 1)
        self.assertEqual(result["method_incomplete_count"], 5)
        self.assertAlmostEqual(result["ratio_min"], 250.0 / 12.0)
        self.assertEqual(result["ratio_max"], 75.0)
        self.assertEqual(result["max_min_fold"], 3.6)
        self.assertFalse(result["meta_analysis_performed"])
        self.assertEqual(result["stability_conclusion"], "not_supported_as_stable_point_estimate")

    def test_document_method_audit_does_not_promote_snippets_or_same_origin_records(self):
        result = self.read("validation/ca-document-methods.json")
        self.assertEqual(result["documentCount"], 6)
        self.assertEqual(result["strictMethodMatchedCount"], 1)
        self.assertEqual(result["methodIncompleteCount"], 5)
        self.assertEqual(result["publisherSnippetCheckedCount"], 3)
        self.assertEqual(result["abstractCheckedCount"], 3)
        self.assertEqual(result["fullTextObtainedCount"], 0)
        self.assertEqual(result["completeProtocolObtainedCount"], 0)
        self.assertEqual(result["independentWetExperimentCount"], 0)
        expected_titles = {
            "CHEMBL1146805": "isozyme XIII",
            "CHEMBL1133556": "Water-Soluble 4-Sulfamoylphenylthioureas",
            "CHEMBL1146697": "with EMATE",
            "CHEMBL1136178": "3- and 4-carboxybenzolamide",
            "CHEMBL1146695": "E7070",
            "CHEMBL1134204": "dtpa tails",
        }
        for doc in result["documents"]:
            self.assertIn(expected_titles[doc["documentChemblId"]], doc["title"])
            self.assertFalse(doc["protocolVerified"])
            self.assertTrue(doc["bindingDb"]["curatedByChembl"])
            self.assertFalse(doc["bindingDb"]["independentExperiment"])
            self.assertIn(doc["primaryEvidence"]["readingLevel"], {"abstract_checked", "partial_text_checked"})

    def test_structural_control_is_not_wildtype_replication(self):
        result = self.read("validation/structural-control.json")
        self.assertFalse(result["exact_wildtype_replication"])
        self.assertEqual(result["comparison_type"], "different_construct_structural_control")
        self.assertEqual(result["alignment_difference_event_count"], 3)
        self.assertTrue(result["length_metadata_discrepancy"])
        self.assertEqual(result["metadata_sample_sequence_length"], 259)
        self.assertEqual(result["sequence_string_length"], 260)
        self.assertEqual(len(result["excluded_candidates"]), 3)

    def test_evidence_packet_is_current_and_bounded(self):
        packet = self.read("exports/frontier-evidence.json")
        self.assertEqual(len(packet["items"]), 21)
        self.assertEqual(len({i["id"] for i in packet["items"]}), 21)
        for item in packet["items"]:
            self.assertEqual(item["status"], "verified")
            self.assertTrue(item["limitations"])
            self.assertTrue(item["upstreamContribution"])
            for snapshot in item["snapshotFiles"]:
                self.assertTrue((ROOT / snapshot).is_file())

    def test_new_agent_projects_have_primary_sources(self):
        projects = self.read("data/projects.json")["projects"]
        by_id = {p["id"]: p for p in projects}
        for pid in ("google-co-scientist", "futurehouse-robin", "kosmos", "materials-project", "rcsb-pdb", "uniprot", "chembl", "oqmd", "nist-strd-chwirut", "nist-strd-eckerle", "cvc5", "nist-strd-hahn1"):
            self.assertIn(pid, by_id)
            self.assertTrue(by_id[pid]["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()

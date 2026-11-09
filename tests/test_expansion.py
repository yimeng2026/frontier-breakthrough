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
        self.assertEqual(len(packet["items"]), 57)
        self.assertEqual(len({i["id"] for i in packet["items"]}), 57)
        for item in packet["items"]:
            self.assertEqual(item["status"], "verified")
            self.assertTrue(item["limitations"])
            self.assertTrue(item["upstreamContribution"])
            for snapshot in item["snapshotFiles"]:
                self.assertTrue((ROOT / snapshot).is_file())
        gauss1 = next(item for item in packet["items"] if item["id"] == "gauss1-external-coverage-counterexample")
        self.assertEqual(gauss1["metrics"]["comparisonTotals"]["point_count"], 365)
        self.assertEqual(gauss1["metrics"]["comparisonTotals"]["ellipsoid_available_point_count"], 305)
        self.assertEqual(gauss1["metrics"]["comparisonTotals"]["ellipsoid_unavailable_point_count"], 60)
        self.assertEqual(gauss1["metrics"]["gauss1"]["continuous_safe_fold_count"], 3)
        self.assertIn("不是概率覆盖率或普适外部成功率", gauss1["limitations"])
        mechanism = next(item for item in packet["items"] if item["id"] == "gauss1-bound-mechanism-decomposition")
        self.assertEqual(mechanism["metrics"]["totals"]["stored_bound_agreement_count"], 190)
        self.assertEqual(mechanism["metrics"]["totals"]["stored_bound_mismatch_count"], 0)
        self.assertGreater(mechanism["metrics"]["samePointMaxima"][1]["shift_share"], 0.95)
        self.assertLess(mechanism["metrics"]["samePointMaxima"][0]["shift_share"], 0.05)
        self.assertFalse(mechanism["metrics"]["analysisScope"]["refit"])
        heterogeneity = next(item for item in packet["items"] if item["id"] == "external-bound-composition-heterogeneity")
        self.assertEqual(heterogeneity["metrics"]["totals"]["prediction_shift_dominant_point_count"], 138)
        self.assertEqual(heterogeneity["metrics"]["totals"]["snapshot_residual_dominant_point_count"], 167)
        datasets = {item["id"]: item for item in heterogeneity["metrics"]["datasets"]}
        self.assertEqual(datasets["filip"]["prediction_shift_dominant_point_count"], 82)
        self.assertEqual(datasets["gauss1"]["snapshot_residual_dominant_point_count"], 166)
        self.assertGreater(datasets["filip"]["median_shift_share"], 0.99)
        self.assertLess(datasets["gauss1"]["median_shift_share"], 0.2)
        self.assertEqual(heterogeneity["metrics"]["gauss1Regression"]["mismatch_count"], 0)
        combined = next(item for item in packet["items"] if item["id"] == "internal-external-bound-scope-comparison")
        self.assertEqual(combined["metrics"]["totals"]["ellipsoid_available_point_count"], 674)
        self.assertEqual(combined["metrics"]["totals"]["prediction_shift_dominant_point_count"], 482)
        self.assertEqual(combined["metrics"]["totals"]["snapshot_residual_dominant_point_count"], 192)
        self.assertEqual(combined["metrics"]["totals"]["external_unavailable_point_count"], 60)
        self.assertEqual(combined["metrics"]["totals"]["internal_unavailable_rooted_fold_count"], 2)
        self.assertEqual(len(combined["metrics"]["datasets"]), 6)
        self.assertFalse(combined["metrics"]["decision"]["combined_success_rate_claimed"])
        misra1a = next(item for item in packet["items"] if item["id"] == "misra1a-prediction-proof-dissociation")
        self.assertEqual(misra1a["metrics"]["totals"]["point_count"], 14)
        self.assertEqual(misra1a["metrics"]["totals"]["ellipsoid_available_point_count"], 4)
        self.assertEqual(misra1a["metrics"]["totals"]["continuous_safe_fold_count"], 1)
        self.assertEqual(misra1a["metrics"]["totals"]["independent_box_continuous_safe_fold_count"], 0)
        self.assertGreater(misra1a["metrics"]["totals"]["max_ellipsoid_absolute_residual_upper_bound_float"], 400)
        self.assertEqual(len(misra1a["metrics"]["availablePoints"]), 4)
        self.assertTrue(all(point["shift_share"] > 0.999 for point in misra1a["metrics"]["availablePoints"]))
        self.assertFalse(misra1a["metrics"]["decision"]["independent_physical_experiment_claimed"])
        v2 = next(item for item in packet["items"] if item["id"] == "bound-comparison-v2-scope-expansion")
        self.assertEqual(v2["metrics"]["externalV2Totals"]["point_count"], 379)
        self.assertEqual(v2["metrics"]["externalV2Totals"]["ellipsoid_available_point_count"], 309)
        self.assertEqual(v2["metrics"]["externalV2Totals"]["ellipsoid_unavailable_point_count"], 70)
        self.assertEqual(v2["metrics"]["combinedV2Totals"]["ellipsoid_available_point_count"], 678)
        self.assertEqual(v2["metrics"]["combinedV2Totals"]["prediction_shift_dominant_point_count"], 486)
        self.assertEqual(v2["metrics"]["combinedV2Totals"]["snapshot_residual_dominant_point_count"], 192)
        self.assertEqual(len(v2["metrics"]["datasets"]), 7)
        self.assertTrue(v2["metrics"]["historicalPreservation"]["previousFilesPreserved"])

    def test_chwirut1_prediction_proof_dissociation_and_related_scope(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-prediction-proof-dissociation", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-prediction-proof-dissociation")
        self.assertEqual(item["metrics"]["totals"]["point_count"], 214)
        self.assertEqual(item["metrics"]["totals"]["ellipsoid_available_point_count"], 83)
        self.assertEqual(item["metrics"]["totals"]["continuous_safe_fold_count"], 2)
        self.assertEqual(item["metrics"]["bestPredictionWithoutBounds"]["fold"], 4)
        self.assertEqual(item["metrics"]["bestPredictionWithoutBounds"]["availablePointCount"], 0)
        self.assertEqual(item["metrics"]["relatedDataset"]["name"], "Chwirut2")
        self.assertFalse(item["metrics"]["decision"]["independent_model_family_claimed"])
        self.assertIn("同族", item["limitations"])

    def test_v3_scope_expansion_preserves_related_data_and_history(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("bound-comparison-v3-scope-expansion", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "bound-comparison-v3-scope-expansion")
        self.assertEqual(item["metrics"]["externalV3Totals"]["point_count"], 593)
        self.assertEqual(item["metrics"]["externalV3Totals"]["ellipsoid_available_point_count"], 392)
        self.assertEqual(item["metrics"]["externalV3Totals"]["ellipsoid_unavailable_point_count"], 201)
        self.assertEqual(item["metrics"]["combinedV3Totals"]["ellipsoid_available_point_count"], 761)
        self.assertEqual(item["metrics"]["combinedV3Totals"]["prediction_shift_dominant_point_count"], 561)
        self.assertEqual(item["metrics"]["combinedV3Totals"]["snapshot_residual_dominant_point_count"], 200)
        self.assertEqual(len(item["metrics"]["datasets"]), 8)
        self.assertEqual(item["metrics"]["chwirut1Increment"]["unavailable"], 131)
        self.assertEqual(item["metrics"]["chwirut1Increment"]["predictionShiftDominant"], 75)
        self.assertEqual(item["metrics"]["relatedDataset"]["name"], "Chwirut2")
        self.assertTrue(item["metrics"]["historicalPreservation"]["previousFilesPreserved"])

    def test_external_scope_amendment_stops_wrong_native_model_text(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("external-scope-limitations-amendment", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "external-scope-limitations-amendment")
        self.assertEqual(item["metrics"]["correctionCount"], 3)
        self.assertEqual(item["metrics"]["datasetIds"], ["mgh17", "gauss1", "misra1a"])
        self.assertTrue(item["metrics"]["originalFilesPreserved"])
        self.assertFalse(item["metrics"]["numericResultsModified"])
        self.assertEqual(item["metrics"]["changedJsonPointer"], "/limitations/0")
        for identifier in ["external-coverage-framework-mgh17", "gauss1-external-coverage-counterexample", "misra1a-prediction-proof-dissociation"]:
            existing = next(entry for entry in packet["items"] if entry["id"] == identifier)
            self.assertNotIn("native Filip", existing["limitations"])

    def test_enso_prediction_proof_dissociation_and_adapter_scope(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-prediction-proof-dissociation", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "enso-prediction-proof-dissociation")
        self.assertEqual(item["metrics"]["totals"]["point_count"], 168)
        self.assertEqual(item["metrics"]["totals"]["ellipsoid_available_point_count"], 135)
        self.assertEqual(item["metrics"]["totals"]["continuous_safe_fold_count"], 4)
        self.assertEqual(item["metrics"]["fold5PredictionWithoutBounds"]["availablePointCount"], 0)
        self.assertLess(item["metrics"]["fold5PredictionWithoutBounds"]["modelRmse"], item["metrics"]["fold5PredictionWithoutBounds"]["baselineRmse"])
        self.assertEqual(item["metrics"]["boxComparison"]["availablePairCount"], 131)
        self.assertEqual(item["metrics"]["boxComparison"]["tighterPointCount"], 131)
        self.assertEqual(item["metrics"]["implementation"]["scopeAdapter"], "scripts/external_coverage_scoped.py")
        self.assertIn("ENSO", item["limitations"])
        self.assertNotIn("native Filip", item["limitations"])

    def test_v4_scope_expansion_adds_enso_and_max_bound_counterexample(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("bound-comparison-v4-scope-expansion", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "bound-comparison-v4-scope-expansion")
        self.assertEqual(item["metrics"]["externalV4Totals"]["point_count"], 761)
        self.assertEqual(item["metrics"]["externalV4Totals"]["ellipsoid_available_point_count"], 527)
        self.assertEqual(item["metrics"]["externalV4Totals"]["ellipsoid_unavailable_point_count"], 234)
        self.assertEqual(item["metrics"]["combinedV4Totals"]["ellipsoid_available_point_count"], 896)
        self.assertEqual(item["metrics"]["combinedV4Totals"]["prediction_shift_dominant_point_count"], 594)
        self.assertEqual(item["metrics"]["combinedV4Totals"]["snapshot_residual_dominant_point_count"], 302)
        self.assertEqual(len(item["metrics"]["datasets"]), 9)
        self.assertEqual(item["metrics"]["ensoIncrement"]["unavailable"], 33)
        self.assertEqual(item["metrics"]["ensoIncrement"]["snapshotResidualDominant"], 102)
        self.assertEqual(item["metrics"]["ensoMaximumBound"]["dominant"], "snapshot_residual_dominant")
        self.assertLess(item["metrics"]["ensoMaximumBound"]["shift_share"], 0.5)
        self.assertEqual(item["metrics"]["relatedDataset"]["name"], "Chwirut2")
        self.assertTrue(item["metrics"]["historicalPreservation"]["previousFilesPreserved"])

    def test_maximum_full_composition_audit_preserves_three_evidence_axes(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("maximum-full-composition-audit", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "maximum-full-composition-audit")
        self.assertEqual(item["metrics"]["totals"]["maximum_matches_majority_count"], 8)
        self.assertEqual(item["metrics"]["totals"]["maximum_majority_mismatch_dataset_ids"], ["gauss1"])
        self.assertEqual(item["metrics"]["totals"]["maximum_share_below_median_count"], 6)
        self.assertEqual(item["metrics"]["totals"]["largest_bound_to_median_ratio_dataset_id"], "gauss1")
        self.assertAlmostEqual(item["metrics"]["totals"]["largest_bound_to_median_ratio"], 82.99437100729904, places=10)
        self.assertEqual(len(item["metrics"]["datasets"]), 9)
        self.assertFalse(item["metrics"]["decision"]["maximum_point_used_as_typical_claimed"])
        enso = next(entry for entry in item["metrics"]["datasets"] if entry["id"] == "enso")
        self.assertAlmostEqual(enso["maximum_share_descriptive_percentile"], 2 / 15, places=12)

    def test_extreme_reporting_contract_is_executable_and_current(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("extreme-reporting-contract", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "extreme-reporting-contract")
        self.assertEqual(item["metrics"]["claimLevel"], "mechanism_interpretation")
        self.assertEqual(item["metrics"]["datasetCount"], 9)
        self.assertEqual(item["metrics"]["errorCount"], 0)
        self.assertEqual(item["metrics"]["levelNames"], ["maximum_only", "distribution_summary", "mechanism_interpretation"])
        self.assertFalse(item["metrics"]["decision"]["maximum_point_used_as_typical_claimed"])

    def test_extreme_corpus_classification_preserves_originals(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("extreme-corpus-classification", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "extreme-corpus-classification")
        self.assertEqual(item["metrics"]["documentCount"], 16)
        self.assertEqual(item["metrics"]["companionRequiredCount"], 10)
        self.assertEqual(item["metrics"]["unchangedOriginalCount"], 10)
        self.assertEqual(item["metrics"]["errorCount"], 0)
        self.assertEqual(item["metrics"]["completeCount"], 2)
        self.assertEqual(item["metrics"]["descriptiveOnlyCount"], 4)

    def test_roszman1_small_sample_and_shift_dominant_scope(self):
        packet = self.read("exports/frontier-evidence.json")
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-prediction-proof-dissociation", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-prediction-proof-dissociation")
        self.assertEqual(item["metrics"]["totals"]["point_count"], 25)
        self.assertEqual(item["metrics"]["totals"]["ellipsoid_available_point_count"], 5)
        self.assertEqual(item["metrics"]["totals"]["continuous_safe_fold_count"], 1)
        self.assertEqual(item["metrics"]["totals"]["independent_box_continuous_safe_fold_count"], 0)
        self.assertEqual(item["metrics"]["boxComparison"]["availablePairCount"], 4)
        self.assertEqual(item["metrics"]["boxComparison"]["tighterPointCount"], 4)
        self.assertEqual(item["metrics"]["boxComparison"]["ellipsoidOnlyPointCount"], 1)
        self.assertGreater(item["metrics"]["minimumAvailableShiftShare"], 0.98)
        self.assertEqual(len(item["metrics"]["betterBaselineWithoutBounds"]), 2)
        self.assertEqual(item["metrics"]["fold5Failure"]["availablePointCount"], 0)
        self.assertEqual(item["metrics"]["implementation"]["scopeAdapter"], "scripts/external_coverage_scoped.py")

    def test_new_agent_projects_have_primary_sources(self):
        projects = self.read("data/projects.json")["projects"]
        by_id = {p["id"]: p for p in projects}
        for pid in ("google-co-scientist", "futurehouse-robin", "kosmos", "materials-project", "rcsb-pdb", "uniprot", "chembl", "oqmd", "nist-strd-chwirut", "nist-strd-eckerle", "cvc5", "nist-strd-hahn1"):
            self.assertIn(pid, by_id)
            self.assertTrue(by_id[pid]["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()

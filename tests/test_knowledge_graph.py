import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_knowledge_graph import build_graph, validate_graph


class KnowledgeGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = build_graph(ROOT)
        cls.nodes = {node["id"]: node for node in cls.graph["nodes"]}

    def test_all_five_research_tracks_are_present(self):
        expected = {"track-holdout", "track-formal", "track-chemistry", "track-materials", "track-knowledge"}
        self.assertTrue(expected.issubset(self.nodes))

    def test_support_and_counterexamples_coexist(self):
        self.assertEqual(self.nodes["claim-chwirut-extrapolation"]["status"], "limited_support")
        self.assertEqual(self.nodes["claim-universal-identifiability"]["status"], "falsified")
        self.assertEqual(self.nodes["claim-descriptor-fraud"]["status"], "falsified")
        self.assertEqual(self.nodes["claim-universal-bandgap"]["status"], "falsified")
        self.assertEqual(self.nodes["claim-material-identity"]["status"], "supported")

    def test_second_dataset_and_cross_solver_are_linked(self):
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        self.assertEqual(self.nodes["claim-eckerle4-two-tail"]["status"], "limited_support")
        self.assertEqual(self.nodes["claim-solver-agreement"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-two-datasets"]["status"], "active")
        self.assertEqual(self.nodes["claim-hahn1-high-temperature"]["status"], "limited_support")
        self.assertEqual(self.nodes["claim-unbounded-denominator-safety"]["status"], "falsified")
        self.assertEqual(self.nodes["limitation-three-datasets"]["status"], "active")
        self.assertEqual(self.nodes["claim-universal-robustness"]["status"], "falsified")
        self.assertEqual(self.nodes["limitation-grouped-stress"]["status"], "active")
        self.assertEqual(self.nodes["claim-fold1-heldout-pole-free"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-hahn1-frozen-denominator-roots"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-post-hoc-mechanism"]["status"], "active")
        self.assertEqual(self.nodes["claim-thurber-all-folds-gated"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-thurber-prospective-gate"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-thurber-prospective"]["status"], "active")
        self.assertEqual(self.nodes["claim-kirby2-all-folds-gated"]["status"], "supported")
        self.assertEqual(self.nodes["evidence-kirby2-prospective-gate"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-kirby2-prospective"]["status"], "active")
        self.assertEqual(self.nodes["claim-rational-gate-always-passes"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-rational-cross-dataset"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-rational-cross-dataset"]["status"], "active")
        self.assertEqual(self.nodes["claim-exact-snapshot-all-folds-root-free"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-exact-sturm-intervals"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-exact-snapshot-scope"]["status"], "active")
        self.assertEqual(self.nodes["claim-no-positive-rootfree-box"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-parameter-box-stability"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-parameter-box-scope"]["status"], "active")
        self.assertEqual(self.nodes["claim-rootfree-box-useful-prediction-bound"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-prediction-box-bounds"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-prediction-box-bounds"]["status"], "active")
        self.assertEqual(self.nodes["claim-ellipsoid-all-369-tighter"]["status"], "supported")
        self.assertEqual(self.nodes["evidence-ellipsoid-box-comparison"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-ellipsoid-box-scope"]["status"], "active")
        self.assertEqual(self.nodes["claim-ellipsoid-continuous-gap"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-ellipsoid-continuous-interval"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-ellipsoid-continuous-scope"]["status"], "active")
        self.assertEqual(self.nodes["claim-filip-ellipsoid-covered"]["status"], "supported")
        self.assertEqual(self.nodes["evidence-filip-ellipsoid-coverage"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-filip-candidate-scope"]["status"], "active")
        self.assertEqual(self.nodes["claim-external-coverage-framework"]["status"], "supported")
        self.assertEqual(self.nodes["evidence-external-coverage-framework"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-external-coverage-framework"]["status"], "active")

    def test_gauss1_counterexample_is_linked_to_reusable_driver_claim(self):
        for identifier in ["claim-reusable-driver-guarantees-coverage", "evidence-gauss1-external-coverage", "counterexample-gauss1-fold2-fold5", "experiment-gauss1-coverage-protocol", "limitation-gauss1-generated-candidate-scope"]:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-reusable-driver-guarantees-coverage"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-gauss1-external-coverage"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-gauss1-fold2-fold5"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-gauss1-coverage-protocol"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-gauss1-generated-candidate-scope"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-gauss1-external-coverage", "claim-reusable-driver-guarantees-coverage", "contradicts"), edges)
        self.assertIn(("counterexample-gauss1-fold2-fold5", "claim-reusable-driver-guarantees-coverage", "contradicts"), edges)
        self.assertIn(("experiment-gauss1-coverage-protocol", "claim-reusable-driver-guarantees-coverage", "tests"), edges)

    def test_gauss1_bound_mechanism_distinguishes_wide_bound_causes(self):
        identifiers = ["claim-wide-bounds-parameter-uncertainty", "evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold1-wide-bound", "experiment-gauss1-bound-mechanism", "limitation-gauss1-bound-mechanism-posthoc"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-wide-bounds-parameter-uncertainty"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-gauss1-bound-decomposition"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-gauss1-fold1-wide-bound"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-gauss1-bound-mechanism"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-gauss1-bound-mechanism-posthoc"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-gauss1-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"), edges)
        self.assertIn(("counterexample-gauss1-fold1-wide-bound", "claim-wide-bounds-parameter-uncertainty", "contradicts"), edges)
        self.assertIn(("evidence-gauss1-bound-decomposition", "counterexample-gauss1-fold2-fold5", "supports"), edges)

    def test_external_bound_composition_heterogeneity_is_linked(self):
        identifiers = ["claim-uniform-external-bound-mechanism", "evidence-external-bound-decomposition", "counterexample-filip-gauss1-composition", "experiment-external-bound-decomposition-protocol", "limitation-external-bound-decomposition-posthoc"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-uniform-external-bound-mechanism"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-external-bound-decomposition"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-filip-gauss1-composition"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-external-bound-decomposition-protocol"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-external-bound-decomposition-posthoc"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-external-bound-decomposition", "claim-uniform-external-bound-mechanism", "contradicts"), edges)
        self.assertIn(("counterexample-filip-gauss1-composition", "claim-uniform-external-bound-mechanism", "contradicts"), edges)
        self.assertIn(("evidence-external-bound-decomposition", "claim-wide-bounds-parameter-uncertainty", "contradicts"), edges)
        self.assertIn(("experiment-external-bound-decomposition-protocol", "claim-uniform-external-bound-mechanism", "tests"), edges)

    def test_internal_external_scope_and_six_distributions_are_linked(self):
        identifiers = ["claim-combined-internal-external-success-rate", "evidence-internal-external-bound-comparison", "counterexample-six-dataset-bound-composition", "experiment-internal-external-bound-protocol", "limitation-internal-external-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-combined-internal-external-success-rate"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-internal-external-bound-comparison"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-six-dataset-bound-composition"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-internal-external-bound-protocol"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-internal-external-scope"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-internal-external-bound-comparison", "claim-combined-internal-external-success-rate", "contradicts"), edges)
        self.assertIn(("counterexample-six-dataset-bound-composition", "claim-combined-internal-external-success-rate", "contradicts"), edges)
        self.assertIn(("evidence-internal-external-bound-comparison", "counterexample-filip-gauss1-composition", "supports"), edges)
        self.assertIn(("experiment-internal-external-bound-protocol", "claim-combined-internal-external-success-rate", "tests"), edges)

    def test_misra1a_prediction_proof_dissociation_is_linked(self):
        identifiers = ["claim-small-rmse-useful-proof", "evidence-misra1a-prediction-proof-dissociation", "counterexample-misra1a-four-of-fourteen", "experiment-misra1a-prospective-protocol", "limitation-misra1a-small-sample-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-small-rmse-useful-proof"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-misra1a-prediction-proof-dissociation"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-misra1a-four-of-fourteen"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-misra1a-prospective-protocol"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-misra1a-small-sample-scope"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-misra1a-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("counterexample-misra1a-four-of-fourteen", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("evidence-misra1a-prediction-proof-dissociation", "claim-wide-bounds-parameter-uncertainty", "supports"), edges)
        self.assertIn(("experiment-misra1a-prospective-protocol", "claim-small-rmse-useful-proof", "tests"), edges)

    def test_v2_scope_expansion_preserves_history_and_links_misra1a(self):
        identifiers = ["claim-new-data-overwrite-history", "evidence-bound-comparison-v2", "counterexample-misra1a-v2-increment", "experiment-bound-comparison-v2-protocol", "limitation-bound-comparison-v2-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(self.nodes["claim-new-data-overwrite-history"]["status"], "falsified")
        self.assertEqual(self.nodes["evidence-bound-comparison-v2"]["status"], "supported")
        self.assertEqual(self.nodes["counterexample-misra1a-v2-increment"]["status"], "supported")
        self.assertEqual(self.nodes["experiment-bound-comparison-v2-protocol"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-bound-comparison-v2-scope"]["status"], "active")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-bound-comparison-v2", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("counterexample-misra1a-v2-increment", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("evidence-bound-comparison-v2", "evidence-misra1a-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("experiment-bound-comparison-v2-protocol", "claim-new-data-overwrite-history", "tests"), edges)

    def test_chwirut1_fold4_counterexample_and_related_scope_are_linked(self):
        identifiers = ["claim-untouched-data-independent-model-family", "evidence-chwirut1-prediction-proof-dissociation", "counterexample-chwirut1-fold4-no-bounds", "experiment-chwirut1-prospective-protocol", "limitation-chwirut1-related-dataset-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        self.assertEqual(self.nodes["claim-untouched-data-independent-model-family"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-chwirut1-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-fold4-no-bounds", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("evidence-chwirut1-prediction-proof-dissociation", "claim-untouched-data-independent-model-family", "contradicts"), edges)
        self.assertIn(("experiment-chwirut1-prospective-protocol", "claim-small-rmse-useful-proof", "tests"), edges)
        self.assertIn(("limitation-chwirut1-related-dataset-scope", "claim-untouched-data-independent-model-family", "limits"), edges)

    def test_v3_scope_expansion_links_chwirut1_and_preserves_history(self):
        identifiers = ["evidence-bound-comparison-v3", "counterexample-chwirut1-v3-increment", "experiment-bound-comparison-v3-protocol", "limitation-bound-comparison-v3-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-bound-comparison-v3", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-v3-increment", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("evidence-bound-comparison-v3", "evidence-chwirut1-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("experiment-bound-comparison-v3-protocol", "claim-new-data-overwrite-history", "tests"), edges)
        self.assertIn(("limitation-bound-comparison-v3-scope", "claim-untouched-data-independent-model-family", "limits"), edges)

    def test_external_scope_amendment_is_linked_to_knowledge_integrity(self):
        identifier = "experiment-external-scope-limitations-amendment"
        self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("track-knowledge", identifier, "contains"), edges)
        self.assertIn((identifier, "claim-knowledge-graph", "tests"), edges)

    def test_enso_fold5_counterexample_and_scoped_protocol_are_linked(self):
        identifiers = ["evidence-enso-prediction-proof-dissociation", "counterexample-enso-fold5-no-bounds", "experiment-enso-scoped-prospective-protocol", "limitation-enso-periodic-candidate-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-enso-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("counterexample-enso-fold5-no-bounds", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("experiment-enso-scoped-prospective-protocol", "claim-small-rmse-useful-proof", "tests"), edges)
        self.assertIn(("limitation-enso-periodic-candidate-scope", "evidence-enso-prediction-proof-dissociation", "limits"), edges)
        self.assertIn(("evidence-enso-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"), edges)

    def test_v4_scope_expansion_links_enso_and_max_bound_counterexample(self):
        identifiers = ["evidence-bound-comparison-v4", "counterexample-enso-v4-increment", "counterexample-enso-v4-maximum-composition", "experiment-bound-comparison-v4-protocol", "limitation-bound-comparison-v4-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-bound-comparison-v4", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("counterexample-enso-v4-increment", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("counterexample-enso-v4-maximum-composition", "claim-wide-bounds-parameter-uncertainty", "contradicts"), edges)
        self.assertIn(("evidence-bound-comparison-v4", "counterexample-enso-v4-maximum-composition", "supports"), edges)
        self.assertIn(("evidence-bound-comparison-v4", "evidence-enso-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("limitation-bound-comparison-v4-scope", "claim-untouched-data-independent-model-family", "limits"), edges)

    def test_maximum_full_composition_audit_links_three_evidence_axes(self):
        identifiers = ["evidence-maximum-full-composition-audit", "counterexample-gauss1-maximum-majority-mismatch", "counterexample-enso-maximum-low-share-percentile", "experiment-maximum-full-composition-protocol", "limitation-maximum-not-typical"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-maximum-full-composition-audit", "counterexample-gauss1-maximum-majority-mismatch", "supports"), edges)
        self.assertIn(("evidence-maximum-full-composition-audit", "counterexample-enso-maximum-low-share-percentile", "supports"), edges)
        self.assertIn(("counterexample-gauss1-maximum-majority-mismatch", "claim-uniform-external-bound-mechanism", "contradicts"), edges)
        self.assertIn(("counterexample-enso-maximum-low-share-percentile", "claim-uniform-external-bound-mechanism", "contradicts"), edges)
        self.assertIn(("limitation-maximum-not-typical", "evidence-maximum-full-composition-audit", "limits"), edges)
        self.assertIn(("evidence-maximum-full-composition-audit", "evidence-bound-comparison-v4", "supports"), edges)

    def test_extreme_reporting_contract_is_linked_to_knowledge_integrity(self):
        identifier = "experiment-extreme-reporting-contract"
        self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("track-knowledge", identifier, "contains"), edges)
        self.assertIn((identifier, "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("experiment-maximum-full-composition-protocol", identifier, "supports"), edges)

    def test_extreme_corpus_classification_is_linked_to_contract(self):
        identifier = "experiment-extreme-corpus-classification"
        self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("track-knowledge", identifier, "contains"), edges)
        self.assertIn((identifier, "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("experiment-extreme-reporting-contract", identifier, "supports"), edges)

    def test_roszman1_fold_specific_dissociation_is_linked(self):
        identifiers = ["evidence-roszman1-prediction-proof-dissociation", "counterexample-roszman1-fold1-fold4-no-bounds", "experiment-roszman1-scoped-prospective-protocol", "limitation-roszman1-small-sample-shift-scope"]
        for identifier in identifiers:
            self.assertIn(identifier, self.nodes)
        self.assertEqual(len(self.graph["nodes"]), 240)
        self.assertEqual(len(self.graph["edges"]), 617)
        edges = {(item["from"], item["to"], item["relation"]) for item in self.graph["edges"]}
        self.assertIn(("evidence-roszman1-prediction-proof-dissociation", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold1-fold4-no-bounds", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-scoped-prospective-protocol", "claim-small-rmse-useful-proof", "tests"), edges)
        self.assertIn(("limitation-roszman1-small-sample-shift-scope", "evidence-roszman1-prediction-proof-dissociation", "limits"), edges)
        self.assertIn(("evidence-roszman1-prediction-proof-dissociation", "claim-reusable-driver-guarantees-coverage", "contradicts"), edges)

    def test_schema_edges_and_source_files_are_valid(self):
        self.assertEqual(validate_graph(self.graph, ROOT), [])
        identifiers = set(self.nodes)
        for edge in self.graph["edges"]:
            self.assertIn(edge["from"], identifiers)
            self.assertIn(edge["to"], identifiers)
        for node in self.graph["nodes"]:
            for source in node["sourceFiles"]:
                self.assertTrue((ROOT / source).is_file(), source)


if __name__ == "__main__":
    unittest.main()

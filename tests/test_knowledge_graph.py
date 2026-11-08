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
        self.assertEqual(len(self.graph["nodes"]), 103)
        self.assertEqual(len(self.graph["edges"]), 180)
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

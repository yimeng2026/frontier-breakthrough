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
        self.assertEqual(len(self.graph["nodes"]), 64)
        self.assertEqual(len(self.graph["edges"]), 106)
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

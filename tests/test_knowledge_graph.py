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
        self.assertEqual(len(self.graph["nodes"]), 44)
        self.assertEqual(len(self.graph["edges"]), 70)
        self.assertEqual(self.nodes["claim-eckerle4-two-tail"]["status"], "limited_support")
        self.assertEqual(self.nodes["claim-solver-agreement"]["status"], "supported")
        self.assertEqual(self.nodes["limitation-two-datasets"]["status"], "active")
        self.assertEqual(self.nodes["claim-hahn1-high-temperature"]["status"], "limited_support")
        self.assertEqual(self.nodes["claim-unbounded-denominator-safety"]["status"], "falsified")
        self.assertEqual(self.nodes["limitation-three-datasets"]["status"], "active")
        self.assertEqual(self.nodes["claim-universal-robustness"]["status"], "falsified")
        self.assertEqual(self.nodes["limitation-grouped-stress"]["status"], "active")

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

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class RepositoryIntegrityIntegrationTests(unittest.TestCase):
    def test_repository_audit_evidence_preserves_counts_and_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("repository-integrity-audit", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "repository-integrity-audit")
        metrics = item["metrics"]
        self.assertEqual(metrics["errorCount"], 0)
        self.assertGreaterEqual(metrics["groups"]["readme_local_links"]["count"], 84)
        self.assertEqual(metrics["groups"]["document_figure_links"]["count"], 45)
        self.assertEqual(metrics["groups"]["word_manifests"]["count"], 37)
        self.assertEqual(metrics["groups"]["protocol_inputs"]["count"], 10)
        self.assertEqual(metrics["groups"]["corpus_v2"]["documents"], 23)
        self.assertTrue(metrics["groups"]["dynamic_counts"]["readme_consistent"])
        self.assertFalse(metrics["decision"]["external_web_checked"])
        self.assertFalse(metrics["decision"]["visual_qa_claimed"])
        self.assertFalse(metrics["decision"]["scientific_truth_claimed"])

    def test_repository_audit_experiment_is_linked_to_previous_corpus(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifier = "experiment-repository-integrity-audit"
        self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 185)
        self.assertEqual(len(graph["edges"]), 410)
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("track-knowledge", identifier, "contains"), edges)
        self.assertIn((identifier, "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("experiment-extreme-corpus-v2-classification", identifier, "supports"), edges)


if __name__ == "__main__":
    unittest.main()

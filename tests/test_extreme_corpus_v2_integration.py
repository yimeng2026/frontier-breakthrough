import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class ExtremeCorpusV2IntegrationTests(unittest.TestCase):
    def test_v2_evidence_covers_all_documents_and_preserves_history(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("extreme-corpus-v2-classification", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "extreme-corpus-v2-classification")
        metrics = item["metrics"]
        self.assertEqual(metrics["documentCount"], 23)
        self.assertEqual(metrics["companionRequiredCount"], 12)
        self.assertEqual(metrics["descriptiveOnlyCount"], 7)
        self.assertEqual(metrics["completeCount"], 4)
        self.assertEqual(metrics["hashMatchedDocumentCount"], 22)
        self.assertEqual(metrics["unchangedOriginalCount"], 10)
        self.assertEqual(metrics["errorCount"], 0)
        self.assertTrue(metrics["previousFilesPreserved"])
        self.assertEqual(metrics["newDocumentStatuses"], ["companion_required", "companion_required", "complete", "descriptive_only", "complete", "descriptive_only", "descriptive_only"])

    def test_v2_experiment_is_linked_to_previous_corpus_and_knowledge_integrity(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifier = "experiment-extreme-corpus-v2-classification"
        self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 232)
        self.assertEqual(len(graph["edges"]), 590)
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("track-knowledge", identifier, "contains"), edges)
        self.assertIn((identifier, "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("experiment-extreme-corpus-classification", identifier, "supports"), edges)


if __name__ == "__main__":
    unittest.main()

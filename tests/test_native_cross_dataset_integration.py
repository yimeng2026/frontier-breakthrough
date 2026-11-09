import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class NativeCrossDatasetIntegrationTests(unittest.TestCase):
    def test_evidence_packet_contains_complete_synthesis_and_boundaries(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("native-cross-dataset-synthesis", identifiers)
        self.assertEqual(len(packet["items"]), 54)
        item = next(item for item in packet["items"] if item["id"] == "native-cross-dataset-synthesis")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 15)
        self.assertEqual(metrics["totals"]["point_count"], 407)
        self.assertEqual(metrics["totals"]["native_better_than_rational_fold_count"], 11)
        self.assertEqual(metrics["totals"]["overall_best_model_fold_counts"], {"native": 10, "rational": 3, "cubic": 2, "tie": 0})
        self.assertEqual(metrics["totals"]["point_outcomes"], {"native": 256, "rational": 151, "tie": 0})
        self.assertEqual(metrics["totals"]["metric_direction_disagreement_fold_ids"], ["roszman1:4"])
        self.assertEqual(metrics["totals"]["point_fold_disagreement_fold_ids"], [])
        self.assertIsNone(metrics["crossDatasetPooledErrorMetrics"])
        self.assertFalse(metrics["decision"]["universal_model_ranking_claimed"])
        self.assertFalse(metrics["decision"]["cross_dataset_pooled_metric_claimed"])
        receipt = json.loads((ROOT / "validation/native-cross-dataset-synthesis-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["errorCount"], 0)
        summary_hash = hashlib.sha256((ROOT / "exports/native-cross-dataset-synthesis.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], summary_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], summary_hash)

    def test_graph_links_metric_and_point_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-single-error-metric-sufficient",
            "evidence-native-cross-dataset-synthesis",
            "counterexample-roszman1-native-fold4-metric-direction",
            "counterexample-roszman1-native-point-majority-rmse",
            "experiment-native-cross-dataset-synthesis-protocol",
            "limitation-native-cross-dataset-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 225)
        self.assertEqual(len(graph["edges"]), 565)
        self.assertEqual(nodes["claim-single-error-metric-sufficient"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-native-cross-dataset-synthesis", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-native-fold4-metric-direction", "claim-single-error-metric-sufficient", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-native-point-majority-rmse", "claim-single-error-metric-sufficient", "contradicts"), edges)
        self.assertIn(("experiment-native-cross-dataset-synthesis-protocol", "claim-single-error-metric-sufficient", "tests"), edges)
        self.assertIn(("limitation-native-cross-dataset-scope", "evidence-native-cross-dataset-synthesis", "limits"), edges)
        for prior in ["roszman1", "enso", "chwirut1"]:
            self.assertIn(("evidence-native-cross-dataset-synthesis", f"evidence-{prior}-native-holdout", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

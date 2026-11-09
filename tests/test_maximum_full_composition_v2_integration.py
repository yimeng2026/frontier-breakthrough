import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class MaximumFullCompositionV2IntegrationTests(unittest.TestCase):
    def test_v2_evidence_separates_descriptive_percentile_from_probability(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("maximum-full-composition-v2-audit", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "maximum-full-composition-v2-audit")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["dataset_count"], 10)
        self.assertEqual(metrics["totals"]["maximum_matches_majority_count"], 9)
        self.assertEqual(metrics["totals"]["maximum_majority_mismatch_dataset_ids"], ["gauss1"])
        self.assertEqual(metrics["totals"]["maximum_snapshot_residual_dominant_dataset_ids"], ["enso"])
        self.assertEqual(metrics["totals"]["maximum_share_below_median_count"], 6)
        self.assertEqual(metrics["roszman1"]["available_point_count"], 5)
        self.assertEqual(metrics["roszman1"]["maximum_share_descriptive_percentile"], 1.0)
        self.assertEqual(metrics["roszman1AvailableFolds"], [2])
        self.assertEqual(metrics["excludedRoszman1PointCount"], 20)
        self.assertEqual(metrics["reportingReceipt"]["claimLevel"], "mechanism_interpretation")
        self.assertEqual(metrics["reportingReceipt"]["errorCount"], 0)
        self.assertEqual(metrics["historicalPreservation"]["nineDatasetAudit"], "exports/maximum-full-composition-audit.json")
        self.assertFalse(metrics["decision"]["probability_representativeness_claimed"])

    def test_v2_graph_links_percentile_counterexample_and_history(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-descriptive-percentile-probability-coverage",
            "evidence-maximum-full-composition-v2",
            "counterexample-roszman1-v2-percentile-not-coverage",
            "experiment-maximum-full-composition-v2-protocol",
            "limitation-maximum-v2-small-sample-not-probability",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 225)
        self.assertEqual(len(graph["edges"]), 565)
        self.assertEqual(nodes["claim-descriptive-percentile-probability-coverage"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-maximum-full-composition-v2", "claim-descriptive-percentile-probability-coverage", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-v2-percentile-not-coverage", "claim-descriptive-percentile-probability-coverage", "contradicts"), edges)
        self.assertIn(("experiment-maximum-full-composition-v2-protocol", "claim-descriptive-percentile-probability-coverage", "tests"), edges)
        self.assertIn(("limitation-maximum-v2-small-sample-not-probability", "evidence-maximum-full-composition-v2", "limits"), edges)
        self.assertIn(("evidence-maximum-full-composition-v2", "evidence-bound-comparison-v5", "supports"), edges)
        self.assertIn(("evidence-maximum-full-composition-v2", "evidence-maximum-full-composition-audit", "supports"), edges)
        self.assertIn(("evidence-maximum-full-composition-v2", "counterexample-gauss1-maximum-majority-mismatch", "supports"), edges)
        self.assertIn(("evidence-maximum-full-composition-v2", "counterexample-enso-maximum-low-share-percentile", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

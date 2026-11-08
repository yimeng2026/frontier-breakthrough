import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class BoundComparisonV5IntegrationTests(unittest.TestCase):
    def test_v5_evidence_preserves_increment_and_scopes(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("bound-comparison-v5-scope-expansion", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "bound-comparison-v5-scope-expansion")
        metrics = item["metrics"]
        self.assertEqual(metrics["externalV5Totals"]["point_count"], 786)
        self.assertEqual(metrics["externalV5Totals"]["ellipsoid_available_point_count"], 532)
        self.assertEqual(metrics["externalV5Totals"]["ellipsoid_unavailable_point_count"], 254)
        self.assertEqual(metrics["combinedV5Totals"]["ellipsoid_available_point_count"], 901)
        self.assertEqual(metrics["combinedV5Totals"]["prediction_shift_dominant_point_count"], 599)
        self.assertEqual(metrics["combinedV5Totals"]["snapshot_residual_dominant_point_count"], 302)
        self.assertEqual(metrics["roszman1Increment"], {"pointCount": 25, "available": 5, "unavailable": 20, "predictionShiftDominant": 5, "snapshotResidualDominant": 0})
        self.assertEqual(metrics["datasetCount"], 10)
        self.assertEqual(metrics["roszman1AvailableFolds"], [2])
        self.assertEqual(metrics["historicalPreservation"]["sixExternal"], "exports/external-bound-decomposition-v4.json")
        self.assertEqual(metrics["historicalPreservation"]["nineDatasets"], "exports/internal-external-bound-comparison-v4.json")
        self.assertFalse(metrics["decision"]["native_arctangent_model_claimed"])
        self.assertFalse(metrics["decision"]["independent_physical_experiment_claimed"])

    def test_v5_graph_links_small_sample_and_history(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "evidence-bound-comparison-v5",
            "counterexample-roszman1-v5-increment",
            "counterexample-roszman1-v5-small-sample-scope",
            "experiment-bound-comparison-v5-protocol",
            "limitation-bound-comparison-v5-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 154)
        self.assertEqual(len(graph["edges"]), 311)
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-bound-comparison-v5", "claim-new-data-overwrite-history", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-v5-small-sample-scope", "claim-small-rmse-useful-proof", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-v5-small-sample-scope", "claim-reusable-driver-guarantees-coverage", "contradicts"), edges)
        self.assertIn(("experiment-bound-comparison-v5-protocol", "claim-new-data-overwrite-history", "tests"), edges)
        self.assertIn(("limitation-bound-comparison-v5-scope", "evidence-bound-comparison-v5", "limits"), edges)
        self.assertIn(("evidence-bound-comparison-v5", "evidence-roszman1-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("evidence-bound-comparison-v5", "evidence-bound-comparison-v4", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

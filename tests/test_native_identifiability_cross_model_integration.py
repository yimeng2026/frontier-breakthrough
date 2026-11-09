import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class NativeIdentifiabilityCrossModelIntegrationTests(unittest.TestCase):
    def test_evidence_contains_all_ratio_and_scope_counterexamples(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("native-identifiability-cross-model-synthesis", identifiers)
        self.assertEqual(len(packet["items"]), 65)
        item = next(item for item in packet["items"] if item["id"] == "native-identifiability-cross-model-synthesis")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["dataset_count"], 3)
        self.assertEqual(metrics["totals"]["fold_count"], 15)
        self.assertEqual(metrics["totals"]["held_out_point_count"], 407)
        self.assertEqual(metrics["totals"]["full_numerical_rank_fold_count"], 15)
        self.assertEqual(metrics["totals"]["local_diagnostic_failure_count"], 0)
        self.assertEqual(metrics["totals"]["sensitivity_exceeds_rmse_fold_ids"], ["roszman1:1", "roszman1:5", "chwirut1:1"])
        self.assertEqual(metrics["totals"]["sensitivity_equals_rmse_fold_ids"], [])
        self.assertAlmostEqual(metrics["totals"]["max_sensitivity_to_rmse_ratio"], 2.6972635478072906)
        self.assertIsNone(metrics["crossModelPooledErrorMetrics"])
        self.assertIsNone(metrics["crossModelStabilityScore"])
        self.assertFalse(metrics["decision"]["universal_stability_score_claimed"])
        self.assertFalse(metrics["decision"]["calibrated_coverage_claimed"])
        receipt = json.loads((ROOT / "validation/native-identifiability-cross-model-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "exports/native-identifiability-cross-model-synthesis.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_three_sensitivity_counterexamples_and_no_score_limit(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-sensitivity-rmse-ratio-calibrated-coverage",
            "evidence-native-identifiability-cross-model",
            "counterexample-roszman1-fold5-sensitivity-rmse",
            "counterexample-chwirut1-fold1-sensitivity-rmse",
            "counterexample-enso-fold4-ratio-not-period-safety",
            "experiment-native-identifiability-cross-model-protocol",
            "limitation-native-identifiability-cross-model-no-score",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 313)
        self.assertEqual(len(graph["edges"]), 898)
        self.assertEqual(nodes["claim-sensitivity-rmse-ratio-calibrated-coverage"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-roszman1-fold5-sensitivity-rmse", "claim-sensitivity-rmse-ratio-calibrated-coverage", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-fold1-sensitivity-rmse", "claim-sensitivity-rmse-ratio-calibrated-coverage", "contradicts"), edges)
        self.assertIn(("counterexample-enso-fold4-ratio-not-period-safety", "claim-period-rmse-period-uniqueness", "contradicts"), edges)
        self.assertIn(("experiment-native-identifiability-cross-model-protocol", "claim-local-rank-global-identifiability", "tests"), edges)
        self.assertIn(("limitation-native-identifiability-cross-model-no-score", "evidence-native-identifiability-cross-model", "limits"), edges)
        for prior in ["roszman1", "chwirut1", "enso"]:
            self.assertIn(("evidence-native-identifiability-cross-model", f"evidence-{prior}-native-identifiability", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

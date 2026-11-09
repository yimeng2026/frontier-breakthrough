import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1NativeIdentifiabilityIntegrationTests(unittest.TestCase):
    def test_identifiability_evidence_preserves_local_scope_and_parameter_ranges(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-native-identifiability", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-native-identifiability")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 5)
        self.assertEqual(metrics["totals"]["full_numerical_rank_fold_count"], 5)
        self.assertEqual(metrics["totals"]["local_diagnostic_failure_count"], 0)
        self.assertAlmostEqual(metrics["totals"]["max_scaled_condition_number"], 90.74335888809009)
        self.assertAlmostEqual(metrics["totals"]["max_absolute_off_diagonal_parameter_correlation"], 0.9875352588520016)
        self.assertAlmostEqual(metrics["parameterStability"]["b2"]["range"], 1.0411858782379334e-05)
        self.assertAlmostEqual(metrics["parameterStability"]["b4"]["range"], 112.23614139349083)
        self.assertFalse(metrics["analysisScope"]["refit"])
        self.assertFalse(metrics["analysisScope"]["global_identifiability"])
        self.assertFalse(metrics["decision"]["global_structural_identifiability_proved"])
        self.assertFalse(metrics["decision"]["prediction_stability_equals_parameter_uniqueness"])
        self.assertFalse(metrics["decision"]["calibrated_prediction_intervals_produced"])

    def test_identifiability_graph_links_local_rank_and_uniqueness_boundaries(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-local-rank-global-identifiability",
            "claim-prediction-stability-parameter-uniqueness",
            "evidence-roszman1-native-identifiability",
            "counterexample-roszman1-native-parameter-variation",
            "experiment-roszman1-native-identifiability-protocol",
            "limitation-roszman1-native-local-linearization",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 281)
        self.assertEqual(len(graph["edges"]), 770)
        self.assertEqual(nodes["claim-local-rank-global-identifiability"]["status"], "falsified")
        self.assertEqual(nodes["claim-prediction-stability-parameter-uniqueness"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-roszman1-native-identifiability", "claim-local-rank-global-identifiability", "contradicts"), edges)
        self.assertIn(("evidence-roszman1-native-identifiability", "claim-prediction-stability-parameter-uniqueness", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-native-parameter-variation", "claim-prediction-stability-parameter-uniqueness", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-native-identifiability-protocol", "claim-local-rank-global-identifiability", "tests"), edges)
        self.assertIn(("experiment-roszman1-native-identifiability-protocol", "claim-prediction-stability-parameter-uniqueness", "tests"), edges)
        self.assertIn(("limitation-roszman1-native-local-linearization", "evidence-roszman1-native-identifiability", "limits"), edges)
        self.assertIn(("evidence-roszman1-native-identifiability", "evidence-roszman1-native-holdout", "supports"), edges)
        self.assertIn(("evidence-roszman1-native-identifiability", "claim-rational-bounds-transfer-native", "contradicts"), edges)


if __name__ == "__main__":
    unittest.main()

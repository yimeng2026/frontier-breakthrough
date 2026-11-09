import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoNativeIntegrationTests(unittest.TestCase):
    def test_enso_evidence_preserves_optimizer_mismatch_and_fold_specific_results(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-native-holdout-comparison", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "enso-native-holdout-comparison")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["point_count"], 168)
        self.assertEqual(metrics["totals"]["native_optimizer_failure_count"], 0)
        self.assertEqual(metrics["totals"]["native_better_than_rational_fold_count"], 4)
        self.assertEqual(metrics["totals"]["rational_better_than_native_fold_count"], 1)
        self.assertEqual(metrics["totals"]["native_better_than_cubic_baseline_fold_count"], 5)
        self.assertAlmostEqual(metrics["pooled"]["native"]["rmse"], 2.7462953205805767)
        self.assertAlmostEqual(metrics["pooled"]["rational_candidate"]["rmse"], 3.4337372699481605)
        self.assertIsNone(metrics["pooled"]["cubic_baseline"])
        self.assertFalse(metrics["knownAnswer"]["optimizerWithinOriginalTolerances"])
        self.assertTrue(metrics["knownAnswer"]["certifiedForwardRssCheckPassed"])
        self.assertFalse(metrics["knownAnswer"]["originalTolerancesRelaxed"])
        self.assertFalse(metrics["knownAnswer"]["optimizerMismatchHidden"])
        self.assertAlmostEqual(metrics["periodStability"]["b4"]["range"], 3.1263085397655743)
        self.assertAlmostEqual(metrics["periodStability"]["b7"]["range"], 1.9460668828939873)
        self.assertFalse(metrics["decision"]["rational_bounds_transferred_to_native"])

    def test_enso_graph_links_fold_loss_optimizer_mismatch_and_cross_model_scope(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-certified-forward-equals-optimizer-reproduction",
            "evidence-enso-native-holdout",
            "counterexample-enso-native-fold1-rational-better",
            "counterexample-enso-optimizer-mismatch",
            "experiment-enso-native-holdout-protocol",
            "limitation-enso-native-period-and-bounds",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 329)
        self.assertEqual(len(graph["edges"]), 962)
        self.assertEqual(nodes["claim-certified-forward-equals-optimizer-reproduction"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-enso-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("counterexample-enso-native-fold1-rational-better", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("evidence-enso-native-holdout", "claim-certified-forward-equals-optimizer-reproduction", "contradicts"), edges)
        self.assertIn(("counterexample-enso-optimizer-mismatch", "claim-certified-forward-equals-optimizer-reproduction", "contradicts"), edges)
        self.assertIn(("experiment-enso-native-holdout-protocol", "claim-certified-forward-equals-optimizer-reproduction", "tests"), edges)
        self.assertIn(("limitation-enso-native-period-and-bounds", "evidence-enso-native-holdout", "limits"), edges)
        self.assertIn(("evidence-enso-native-holdout", "evidence-enso-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("evidence-enso-native-holdout", "evidence-roszman1-native-holdout", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

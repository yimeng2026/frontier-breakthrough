import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1NativeIntegrationTests(unittest.TestCase):
    def test_native_evidence_preserves_fold_specific_winners_and_boundaries(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-native-holdout-comparison", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-native-holdout-comparison")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["native_optimizer_failure_count"], 0)
        self.assertEqual(metrics["totals"]["native_better_than_rational_fold_count"], 3)
        self.assertEqual(metrics["totals"]["rational_better_than_native_fold_count"], 2)
        self.assertEqual(metrics["totals"]["native_better_than_cubic_baseline_fold_count"], 3)
        self.assertEqual(metrics["totals"]["cubic_baseline_better_than_native_fold_count"], 2)
        self.assertAlmostEqual(metrics["pooled"]["native"]["rmse"], 0.00756825483191744)
        self.assertAlmostEqual(metrics["pooled"]["rational_candidate"]["rmse"], 0.2193269622679899)
        self.assertIsNone(metrics["pooled"]["cubic_baseline"])
        self.assertTrue(metrics["knownAnswer"]["withinCertifiedTolerances"])
        self.assertEqual(metrics["knownAnswer"]["evidenceClass"], "known_answer_reproduction_not_holdout")
        self.assertFalse(metrics["decision"]["rational_bounds_transferred_to_native"])
        self.assertFalse(metrics["decision"]["certified_full_fit_used_as_holdout"])

    def test_native_graph_links_fold_counterexample_and_proof_separation(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-model-family-fold-independent-winner",
            "claim-rational-bounds-transfer-native",
            "evidence-roszman1-native-holdout",
            "counterexample-roszman1-native-fold-dependent-ranking",
            "experiment-roszman1-native-holdout-protocol",
            "limitation-roszman1-native-no-bounds",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 177)
        self.assertEqual(len(graph["edges"]), 383)
        self.assertEqual(nodes["claim-model-family-fold-independent-winner"]["status"], "falsified")
        self.assertEqual(nodes["claim-rational-bounds-transfer-native"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-roszman1-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-native-fold-dependent-ranking", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-native-holdout-protocol", "claim-model-family-fold-independent-winner", "tests"), edges)
        self.assertIn(("evidence-roszman1-native-holdout", "claim-rational-bounds-transfer-native", "contradicts"), edges)
        self.assertIn(("limitation-roszman1-native-no-bounds", "evidence-roszman1-native-holdout", "limits"), edges)
        self.assertIn(("evidence-roszman1-native-holdout", "evidence-roszman1-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("evidence-roszman1-native-holdout", "claim-nist-reproduction", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

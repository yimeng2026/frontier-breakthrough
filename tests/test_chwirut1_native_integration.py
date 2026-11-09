import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Chwirut1NativeIntegrationTests(unittest.TestCase):
    def test_chwirut1_evidence_preserves_related_scope_counts_and_fold_results(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-native-holdout-comparison", identifiers)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-native-holdout-comparison")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["point_count"], 214)
        self.assertEqual(metrics["totals"]["unique_distance_count"], 22)
        self.assertEqual(metrics["foldObservationCounts"], [57, 54, 51, 23, 29])
        self.assertEqual(metrics["totals"]["native_optimizer_failure_count"], 0)
        self.assertEqual(metrics["totals"]["native_better_than_rational_fold_count"], 4)
        self.assertEqual(metrics["totals"]["rational_better_than_native_fold_count"], 1)
        self.assertAlmostEqual(metrics["pooled"]["native"]["rmse"], 7.778996285751361)
        self.assertAlmostEqual(metrics["pooled"]["rational_candidate"]["rmse"], 9.456157887519154)
        self.assertIsNone(metrics["pooled"]["cubic_baseline"])
        self.assertTrue(metrics["knownAnswer"]["withinCertifiedTolerances"])
        self.assertEqual(metrics["knownAnswer"]["evidenceClass"], "known_answer_reproduction_not_holdout")
        self.assertAlmostEqual(metrics["parameterStability"]["b2"]["range"], 0.005195445174092934)
        self.assertTrue(metrics["analysisScope"]["related_prior_dataset"]["same_native_model_family"])
        self.assertFalse(metrics["decision"]["independent_model_family_claimed"])
        self.assertFalse(metrics["decision"]["rational_bounds_transferred_to_native"])
        self.assertTrue(metrics["implementation"]["metadataAmendmentSha256"])

    def test_chwirut1_graph_links_fold_loss_related_scope_and_cross_model_evidence(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-low-rmse-independent-replication",
            "evidence-chwirut1-native-holdout",
            "counterexample-chwirut1-native-fold2-rational-better",
            "counterexample-chwirut1-native-fold1-error-and-parameters",
            "experiment-chwirut1-native-holdout-protocol",
            "limitation-chwirut1-native-related-study-and-bounds",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 321)
        self.assertEqual(len(graph["edges"]), 930)
        self.assertEqual(nodes["claim-low-rmse-independent-replication"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-chwirut1-native-holdout", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-native-fold2-rational-better", "claim-model-family-fold-independent-winner", "contradicts"), edges)
        self.assertIn(("evidence-chwirut1-native-holdout", "claim-low-rmse-independent-replication", "contradicts"), edges)
        self.assertIn(("experiment-chwirut1-native-holdout-protocol", "claim-low-rmse-independent-replication", "tests"), edges)
        self.assertIn(("limitation-chwirut1-native-related-study-and-bounds", "claim-untouched-data-independent-model-family", "limits"), edges)
        self.assertIn(("evidence-chwirut1-native-holdout", "evidence-chwirut1-prediction-proof-dissociation", "supports"), edges)
        self.assertIn(("evidence-chwirut1-native-holdout", "evidence-roszman1-native-holdout", "supports"), edges)
        self.assertIn(("evidence-chwirut1-native-holdout", "evidence-enso-native-holdout", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

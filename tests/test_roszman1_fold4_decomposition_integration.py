import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1Fold4DecompositionIntegrationTests(unittest.TestCase):
    def test_evidence_contains_point_contributions_and_leave_one_out_boundaries(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-fold4-error-decomposition", identifiers)
        self.assertEqual(len(packet["items"]), 63)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-fold4-error-decomposition")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["point_count"], 5)
        self.assertEqual(metrics["totals"]["native_absolute_winner_count"], 3)
        self.assertEqual(metrics["totals"]["rational_absolute_winner_count"], 2)
        self.assertEqual(metrics["totals"]["leave_one_out_reverses_rational_mae_count"], 2)
        self.assertEqual(metrics["totals"]["leave_one_out_reverses_native_rmse_count"], 0)
        self.assertEqual(metrics["totals"]["per_point_absolute_squared_direction_disagreement_count"], 0)
        self.assertGreater(metrics["aggregate"]["absolute_delta_sum"], 0)
        self.assertLess(metrics["aggregate"]["squared_delta_sum"], 0)
        self.assertEqual(metrics["aggregate"]["weight_identity_mismatch_count"], 0)
        self.assertEqual(metrics["aggregate"]["frozen_metric_mismatch_count"], 0)
        self.assertEqual(metrics["groups"]["native"]["point_indices"], [1, 2, 3])
        self.assertEqual(metrics["groups"]["rational"]["point_indices"], [4, 5])
        self.assertFalse(metrics["decision"]["leave_one_out_refitting_performed"])
        self.assertFalse(metrics["decision"]["statistical_significance_claimed"])
        receipt = json.loads((ROOT / "validation/roszman1-native-fold4-error-decomposition-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["errorCount"], 0)
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-native-fold4-error-decomposition.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_weight_identity_and_asymmetric_leave_one_out(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-aggregate-loss-direction-implies-per-point",
            "evidence-roszman1-fold4-error-decomposition",
            "counterexample-roszman1-fold4-weighted-reversal",
            "counterexample-roszman1-fold4-leave-one-out-asymmetry",
            "experiment-roszman1-fold4-error-decomposition-protocol",
            "limitation-roszman1-fold4-five-point-arithmetic",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 297)
        self.assertEqual(len(graph["edges"]), 834)
        self.assertEqual(nodes["claim-aggregate-loss-direction-implies-per-point"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-roszman1-fold4-error-decomposition", "claim-single-error-metric-sufficient", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold4-weighted-reversal", "claim-aggregate-loss-direction-implies-per-point", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold4-leave-one-out-asymmetry", "claim-single-error-metric-sufficient", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-fold4-error-decomposition-protocol", "claim-aggregate-loss-direction-implies-per-point", "tests"), edges)
        self.assertIn(("limitation-roszman1-fold4-five-point-arithmetic", "evidence-roszman1-fold4-error-decomposition", "limits"), edges)
        self.assertIn(("evidence-roszman1-fold4-error-decomposition", "evidence-native-cross-dataset-synthesis", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

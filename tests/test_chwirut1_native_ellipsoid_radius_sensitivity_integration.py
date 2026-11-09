import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Chwirut1NativeEllipsoidRadiusSensitivityIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_critical_radius_failure_width_and_count_history(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-native-ellipsoid-radius-sensitivity", identifiers)
        self.assertEqual(len(packet["items"]), 69)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-native-ellipsoid-radius-sensitivity")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["case_count"], 25)
        self.assertEqual(metrics["totals"]["maximum_point_evaluations"], 1070)
        self.assertEqual(metrics["totals"]["maximum_envelope_evaluations"], 110)
        self.assertEqual(metrics["totals"]["actual_envelope_evaluation_count"], 105)
        self.assertEqual(metrics["totals"]["unavailable_case_ids"], ["chwirut1:1:r8"])
        self.assertAlmostEqual(metrics["totals"]["minimum_critical_radius"], 7.415973756136996)
        self.assertEqual(metrics["totals"]["minimum_critical_radius_fold"], 1)
        self.assertEqual(metrics["totals"]["center_prediction_envelope_mismatch_count"], 0)
        self.assertTrue(metrics["baseline"]["matches_frozen_baseline"])
        self.assertEqual(metrics["baseline"]["certified_fold_count"], 5)
        self.assertAlmostEqual(metrics["baseline"]["max_envelope_width"], 170.14630922307612)
        self.assertAlmostEqual(metrics["baseline"]["median_envelope_width"], 19.222110234669167)
        self.assertEqual(metrics["countHistory"]["finalMaximumPointEvaluations"], 1070)
        self.assertEqual(metrics["countHistory"]["supersededIncorrectValue"], 5350)
        self.assertTrue(metrics["countHistory"]["amendment01PreservedNotUsed"])
        self.assertFalse(metrics["decision"]["optimal_radius_selected"])
        self.assertFalse(metrics["decision"]["grid_maximum_called_exact_safe_maximum"])
        receipt = json.loads((ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/chwirut1-native-ellipsoid-radius-sensitivity.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_grid_scope_radius_failure_and_amendment(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-grid-max-exact-safe-max",
            "claim-critical-radius-probability-optimum",
            "evidence-chwirut1-native-radius-sensitivity",
            "counterexample-chwirut1-fold1-radius8-unavailable",
            "counterexample-chwirut1-radius-width-tradeoff",
            "experiment-chwirut1-native-radius-sensitivity-protocol",
            "experiment-chwirut1-radius-count-amendment-v2",
            "limitation-chwirut1-native-radius-grid-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 345)
        self.assertEqual(len(graph["edges"]), 1026)
        self.assertEqual(nodes["claim-grid-max-exact-safe-max"]["status"], "falsified")
        self.assertEqual(nodes["claim-critical-radius-probability-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-chwirut1-fold1-radius8-unavailable", "claim-grid-max-exact-safe-max", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-radius-width-tradeoff", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("experiment-chwirut1-radius-count-amendment-v2", "experiment-chwirut1-native-radius-sensitivity-protocol", "supports"), edges)
        self.assertIn(("limitation-chwirut1-native-radius-grid-scope", "evidence-chwirut1-native-radius-sensitivity", "limits"), edges)
        self.assertIn(("evidence-chwirut1-native-radius-sensitivity", "evidence-chwirut1-native-ellipsoid-continuous", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

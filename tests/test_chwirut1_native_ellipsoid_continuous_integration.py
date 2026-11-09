import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Chwirut1NativeEllipsoidContinuousIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_continuous_certificate_width_and_center_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-native-ellipsoid-continuous-bounds", identifiers)
        self.assertEqual(len(packet["items"]), 57)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-native-ellipsoid-continuous-bounds")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 5)
        self.assertEqual(metrics["totals"]["held_out_point_count"], 214)
        self.assertEqual(metrics["totals"]["unique_distance_count"], 22)
        self.assertEqual(metrics["totals"]["certified_fold_count"], 5)
        self.assertEqual(metrics["totals"]["unavailable_fold_ids"], [])
        self.assertEqual(metrics["totals"]["available_point_count"], 214)
        self.assertEqual(metrics["totals"]["covered_point_count"], 214)
        self.assertEqual(metrics["totals"]["violation_point_count"], 0)
        self.assertEqual(metrics["totals"]["center_prediction_envelope_mismatch_count"], 0)
        self.assertAlmostEqual(metrics["totals"]["max_envelope_width"], 170.14630922307612)
        self.assertAlmostEqual(metrics["totals"]["median_envelope_width"], 19.222110234669167)
        self.assertAlmostEqual(metrics["totals"]["max_residual_upper_bound"], 165.679601537622)
        self.assertAlmostEqual(metrics["totals"]["median_residual_upper_bound"], 15.050994997990879)
        fold1 = metrics["folds"][0]
        self.assertAlmostEqual(fold1["continuousDenominator"]["minimum"], 0.004322621973785059)
        self.assertAlmostEqual(fold1["envelopes"][0]["prediction_minimum"], 62.233292314545906)
        self.assertAlmostEqual(fold1["envelopes"][0]["prediction_maximum"], 232.379601537622)
        self.assertFalse(metrics["analysisScope"]["probability_region"])
        self.assertFalse(metrics["analysisScope"]["taylor_prediction_approximation"])
        self.assertFalse(metrics["decision"]["center_consistency_used_as_external_validation"])
        receipt = json.loads((ROOT / "validation/chwirut1-native-ellipsoid-continuous-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/chwirut1-native-ellipsoid-continuous-bounds.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_continuous_scope_width_and_center_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-center-coverage-external-validation",
            "claim-finite-bound-high-information",
            "evidence-chwirut1-native-ellipsoid-continuous",
            "counterexample-chwirut1-fold1-wide-native-envelope",
            "counterexample-chwirut1-center-consistency-not-probability",
            "experiment-chwirut1-native-ellipsoid-continuous-protocol",
            "limitation-chwirut1-native-ellipsoid-region-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 248)
        self.assertEqual(len(graph["edges"]), 645)
        self.assertEqual(nodes["claim-center-coverage-external-validation"]["status"], "falsified")
        self.assertEqual(nodes["claim-finite-bound-high-information"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-chwirut1-fold1-wide-native-envelope", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-center-consistency-not-probability", "claim-center-coverage-external-validation", "contradicts"), edges)
        self.assertIn(("experiment-chwirut1-native-ellipsoid-continuous-protocol", "claim-native-pole-free-observations-global-safety", "tests"), edges)
        self.assertIn(("limitation-chwirut1-native-ellipsoid-region-scope", "evidence-chwirut1-native-ellipsoid-continuous", "limits"), edges)
        self.assertIn(("evidence-chwirut1-native-ellipsoid-continuous", "evidence-chwirut1-native-identifiability", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

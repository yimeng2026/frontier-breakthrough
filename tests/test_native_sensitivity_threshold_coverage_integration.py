import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class NativeSensitivityThresholdCoverageIntegrationTests(unittest.TestCase):
    def test_evidence_contains_counts_and_aggregation_counterexamples(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("native-sensitivity-threshold-coverage", identifiers)
        self.assertEqual(len(packet["items"]), 61)
        item = next(item for item in packet["items"] if item["id"] == "native-sensitivity-threshold-coverage")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["point_count"], 407)
        self.assertEqual(metrics["totals"]["evaluation_count"], 1221)
        self.assertEqual(metrics["totals"]["thresholds"]["1"]["covered_count"], 85)
        self.assertEqual(metrics["totals"]["thresholds"]["1"]["violation_count"], 322)
        self.assertEqual(metrics["totals"]["thresholds"]["2"]["covered_count"], 181)
        self.assertEqual(metrics["totals"]["thresholds"]["2"]["violation_count"], 226)
        self.assertEqual(metrics["totals"]["thresholds"]["4"]["covered_count"], 283)
        self.assertEqual(metrics["totals"]["thresholds"]["4"]["violation_count"], 124)
        self.assertAlmostEqual(metrics["totals"]["max_residual_to_sensitivity_ratio"], 25.724483321809334)
        self.assertEqual(metrics["totals"]["max_ratio_point_id"], "chwirut1:3:30")
        self.assertEqual(metrics["totals"]["zero_sensitivity_point_count"], 0)
        roszman = next(dataset for dataset in metrics["datasets"] if dataset["id"] == "roszman1")
        self.assertEqual(roszman["folds"][4]["thresholds"]["1"]["covered_count"], 5)
        self.assertAlmostEqual(roszman["folds"][4]["max_residual_to_sensitivity_ratio"], 0.7393687714886938)
        self.assertIsNone(metrics["crossModelProbabilityCoverageScore"])
        self.assertFalse(metrics["decision"]["probability_coverage_claimed"])
        self.assertFalse(metrics["decision"]["native_deterministic_bounds_claimed"])
        receipt = json.loads((ROOT / "validation/native-sensitivity-threshold-coverage-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "exports/native-sensitivity-threshold-coverage.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_deterministic_bound_and_aggregation_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-local-sd-deterministic-residual-bound",
            "claim-fold-ratio-pointwise-coverage",
            "evidence-native-sensitivity-threshold-coverage",
            "counterexample-roszman1-fold5-aggregate-point-divergence",
            "counterexample-chwirut1-fold3-point-extreme",
            "counterexample-enso-all-folds-threshold-violations",
            "experiment-native-sensitivity-threshold-coverage-protocol",
            "limitation-native-sensitivity-threshold-not-probability",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 281)
        self.assertEqual(len(graph["edges"]), 770)
        self.assertEqual(nodes["claim-local-sd-deterministic-residual-bound"]["status"], "falsified")
        self.assertEqual(nodes["claim-fold-ratio-pointwise-coverage"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-roszman1-fold5-aggregate-point-divergence", "claim-fold-ratio-pointwise-coverage", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-fold3-point-extreme", "claim-local-sd-deterministic-residual-bound", "contradicts"), edges)
        self.assertIn(("counterexample-enso-all-folds-threshold-violations", "claim-fold-ratio-pointwise-coverage", "contradicts"), edges)
        self.assertIn(("experiment-native-sensitivity-threshold-coverage-protocol", "claim-local-sd-deterministic-residual-bound", "tests"), edges)
        self.assertIn(("limitation-native-sensitivity-threshold-not-probability", "evidence-native-sensitivity-threshold-coverage", "limits"), edges)
        self.assertIn(("evidence-native-sensitivity-threshold-coverage", "evidence-native-identifiability-cross-model", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

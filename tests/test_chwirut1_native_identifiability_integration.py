import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Chwirut1NativeIdentifiabilityIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_fold1_denominator_and_related_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-native-identifiability", identifiers)
        self.assertEqual(len(packet["items"]), 59)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-native-identifiability")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 5)
        self.assertEqual(metrics["totals"]["held_out_point_count"], 214)
        self.assertEqual(metrics["totals"]["full_numerical_rank_fold_count"], 5)
        self.assertEqual(metrics["totals"]["local_diagnostic_failure_count"], 0)
        self.assertAlmostEqual(metrics["totals"]["max_scaled_condition_number"], 28.674083116404475)
        self.assertAlmostEqual(metrics["totals"]["max_absolute_off_diagonal_parameter_correlation"], 0.9794131139106378)
        self.assertAlmostEqual(metrics["totals"]["max_local_prediction_standard_deviation"], 14.836682306268235)
        self.assertAlmostEqual(metrics["totals"]["minimum_absolute_denominator"], 0.009384279096904605)
        self.assertEqual(metrics["totals"]["pole_inside_observed_range_fold_count"], 0)
        self.assertEqual(metrics["foldObservationCounts"], [57, 54, 51, 23, 29])
        self.assertEqual(metrics["residualDegreesOfFreedom"], [154, 157, 160, 188, 182])
        self.assertAlmostEqual(metrics["parameterStability"]["b2"]["range"], 0.005195445174092934)
        self.assertAlmostEqual(metrics["folds"][0]["parameters"][1]["absolute_relative_standard_error"], 1.7106283204180401)
        self.assertTrue(metrics["analysisScope"]["related_prior_dataset"]["same_native_model_family"])
        self.assertFalse(metrics["decision"]["global_structural_identifiability_proved"])
        self.assertFalse(metrics["decision"]["native_deterministic_bounds_claimed"])
        receipt = json.loads((ROOT / "validation/chwirut1-native-identifiability-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/chwirut1-native-identifiability.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_local_rank_pole_scope_and_fold1_counterexample(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-native-pole-free-observations-global-safety",
            "evidence-chwirut1-native-identifiability",
            "counterexample-chwirut1-native-fold1-local-instability",
            "counterexample-chwirut1-native-low-rmse-parameter-uniqueness",
            "experiment-chwirut1-native-identifiability-protocol",
            "limitation-chwirut1-native-local-and-related-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 263)
        self.assertEqual(len(graph["edges"]), 703)
        self.assertEqual(nodes["claim-native-pole-free-observations-global-safety"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-chwirut1-native-identifiability", "claim-local-rank-global-identifiability", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-native-fold1-local-instability", "claim-local-rank-global-identifiability", "contradicts"), edges)
        self.assertIn(("counterexample-chwirut1-native-low-rmse-parameter-uniqueness", "claim-prediction-stability-parameter-uniqueness", "contradicts"), edges)
        self.assertIn(("experiment-chwirut1-native-identifiability-protocol", "claim-native-pole-free-observations-global-safety", "tests"), edges)
        self.assertIn(("limitation-chwirut1-native-local-and-related-scope", "claim-untouched-data-independent-model-family", "limits"), edges)
        self.assertIn(("evidence-chwirut1-native-identifiability", "evidence-roszman1-native-identifiability", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoNativeIdentifiabilityIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_period_compensation_fold4_and_known_answer_layers(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-native-identifiability", identifiers)
        self.assertEqual(len(packet["items"]), 53)
        item = next(item for item in packet["items"] if item["id"] == "enso-native-identifiability")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 5)
        self.assertEqual(metrics["totals"]["held_out_point_count"], 168)
        self.assertEqual(metrics["totals"]["full_numerical_rank_fold_count"], 5)
        self.assertEqual(metrics["totals"]["local_diagnostic_failure_count"], 0)
        self.assertAlmostEqual(metrics["totals"]["max_scaled_condition_number"], 6.896240781966828)
        self.assertAlmostEqual(metrics["totals"]["max_absolute_off_diagonal_parameter_correlation"], 0.9187090249098154)
        self.assertAlmostEqual(metrics["totals"]["max_local_prediction_standard_deviation"], 1.0603474415430074)
        self.assertAlmostEqual(metrics["totals"]["max_cross_harmonic_block_absolute_correlation"], 0.5591238742033899)
        self.assertAlmostEqual(metrics["totals"]["max_annual_long_block_absolute_correlation"], 0.15212841448706105)
        self.assertEqual(metrics["residualDegreesOfFreedom"], [125, 125, 125, 126, 126])
        self.assertAlmostEqual(metrics["parameterStability"]["b4"]["range"], 3.1263085397655743)
        self.assertAlmostEqual(metrics["parameterStability"]["b7"]["range"], 1.9460668828939873)
        fold4 = metrics["folds"][3]
        self.assertAlmostEqual(fold4["testMetrics"]["rmse"], 2.409878120632471)
        period_se = {entry["name"]: entry["absolute_relative_standard_error"] for entry in fold4["parameters"]}
        self.assertAlmostEqual(period_se["b4"], 0.037359660053584605)
        self.assertAlmostEqual(period_se["b7"], 0.025260794231141546)
        self.assertFalse(metrics["knownAnswer"]["optimizer_within_certified_tolerances"])
        self.assertTrue(metrics["knownAnswer"]["certified_forward_rss_check_passed"])
        self.assertFalse(metrics["decision"]["new_physical_periods_proved"])
        receipt = json.loads((ROOT / "validation/enso-native-identifiability-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-native-identifiability.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_period_uniqueness_and_physical_coupling_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-period-rmse-period-uniqueness",
            "claim-harmonic-correlation-physical-coupling",
            "evidence-enso-native-identifiability",
            "counterexample-enso-fold4-low-rmse-high-period-se",
            "counterexample-enso-period-amplitude-dominant-correlation",
            "experiment-enso-native-identifiability-protocol",
            "limitation-enso-native-local-period-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 217)
        self.assertEqual(len(graph["edges"]), 532)
        self.assertEqual(nodes["claim-period-rmse-period-uniqueness"]["status"], "falsified")
        self.assertEqual(nodes["claim-harmonic-correlation-physical-coupling"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-enso-fold4-low-rmse-high-period-se", "claim-period-rmse-period-uniqueness", "contradicts"), edges)
        self.assertIn(("counterexample-enso-period-amplitude-dominant-correlation", "claim-harmonic-correlation-physical-coupling", "contradicts"), edges)
        self.assertIn(("experiment-enso-native-identifiability-protocol", "claim-local-rank-global-identifiability", "tests"), edges)
        self.assertIn(("limitation-enso-native-local-period-scope", "evidence-enso-native-identifiability", "limits"), edges)
        self.assertIn(("evidence-enso-native-identifiability", "evidence-roszman1-native-identifiability", "supports"), edges)
        self.assertIn(("evidence-enso-native-identifiability", "evidence-chwirut1-native-identifiability", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

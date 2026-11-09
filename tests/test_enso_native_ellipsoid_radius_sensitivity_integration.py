import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoNativeEllipsoidRadiusSensitivityIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_grid_failures_width_and_baseline(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-native-ellipsoid-radius-sensitivity", identifiers)
        self.assertEqual(len(packet["items"]), 62)
        item = next(item for item in packet["items"] if item["id"] == "enso-native-ellipsoid-radius-sensitivity")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["case_count"], 30)
        self.assertEqual(totals["maximum_point_evaluations"], 1008)
        self.assertEqual(totals["maximum_envelope_evaluations"], 1008)
        self.assertEqual(totals["actual_envelope_evaluation_count"], 942)
        self.assertEqual(totals["certified_case_count"], 28)
        self.assertEqual(totals["available_point_count"], 942)
        self.assertEqual(totals["covered_point_count"], 942)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertEqual(totals["unavailable_point_count"], 66)
        self.assertEqual(totals["unavailable_case_ids"], ["enso:4:r32", "enso:5:r32"])
        self.assertEqual(totals["fold_held_out_point_counts"], [34, 34, 34, 33, 33])
        self.assertAlmostEqual(totals["max_envelope_width"], 141.13543485416332)
        self.assertAlmostEqual(totals["max_residual_upper_bound"], 75.54732074215885)
        self.assertAlmostEqual(totals["minimum_critical_period_radius"], 26.76683884611663)
        self.assertEqual(totals["minimum_critical_period_radius_fold"], 4)
        self.assertTrue(metrics["baseline"]["matches_frozen_baseline"])
        self.assertEqual(metrics["baseline"]["exact_fold_projection_match_count"], 5)
        self.assertEqual(metrics["analysisScope"]["count_correction"]["corrected_maximum_evaluations"], 1008)
        fold4 = metrics["folds"][3]
        fold5 = metrics["folds"][4]
        self.assertEqual(fold4["maxCertifiedGridRadius"], 16)
        self.assertEqual(fold5["maxCertifiedGridRadius"], 16)
        case4 = fold4["caseSummaries"][-1]
        case5 = fold5["caseSummaries"][-1]
        self.assertFalse(case4["predictionEnvelopeAvailable"])
        self.assertFalse(case5["predictionEnvelopeAvailable"])
        self.assertAlmostEqual(case4["periodCertificate"]["b4_minimum"], -8.73550962456259)
        self.assertAlmostEqual(case5["periodCertificate"]["b4_minimum"], -0.015584026358234438)
        self.assertIsNone(case4["maxEnvelopeWidth"])
        self.assertIsNone(case5["maxEnvelopeWidth"])
        self.assertFalse(metrics["decision"]["optimal_radius_selected"])
        receipt_path = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing ENSO radius-sensitivity validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-native-ellipsoid-radius-sensitivity.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_failures_width_and_count_amendment(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-enso-grid-all-safe",
            "evidence-enso-native-ellipsoid-radius-sensitivity",
            "counterexample-enso-fold4-radius32-nonpositive",
            "counterexample-enso-fold5-radius32-near-zero",
            "counterexample-enso-radius-width-growth",
            "experiment-enso-native-radius-sensitivity-protocol",
            "experiment-enso-native-radius-count-amendment",
            "limitation-enso-native-radius-grid-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 289)
        self.assertEqual(len(graph["edges"]), 802)
        self.assertEqual(nodes["claim-enso-grid-all-safe"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-enso-fold4-radius32-nonpositive", "claim-enso-grid-all-safe", "contradicts"), edges)
        self.assertIn(("counterexample-enso-fold5-radius32-near-zero", "claim-enso-grid-all-safe", "contradicts"), edges)
        self.assertIn(("counterexample-enso-radius-width-growth", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("experiment-enso-native-radius-count-amendment", "experiment-enso-native-radius-sensitivity-protocol", "supports"), edges)
        self.assertIn(("experiment-enso-native-radius-count-amendment", "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("limitation-enso-native-radius-grid-scope", "claim-grid-max-exact-safe-max", "limits"), edges)
        self.assertIn(("evidence-enso-native-ellipsoid-radius-sensitivity", "evidence-enso-native-ellipsoid-continuous", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

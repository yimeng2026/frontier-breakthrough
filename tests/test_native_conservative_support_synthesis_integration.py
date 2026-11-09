import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class NativeConservativeSupportSynthesisIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_counts_unavailable_fold_and_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("native-conservative-support-synthesis", identifiers)
        self.assertEqual(len(packet["items"]), 69)
        item = next(item for item in packet["items"] if item["id"] == "native-conservative-support-synthesis")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["held_out_point_count"], 407)
        self.assertEqual(totals["available_point_count"], 402)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unavailable_fold_ids"], ["roszman1:5"])
        self.assertEqual(totals["unique_envelope_count"], 210)
        self.assertEqual(totals["tightened_envelope_count"], 79)
        self.assertEqual(totals["unchanged_envelope_count"], 131)
        self.assertEqual(totals["nonempty_intersection_count"], 210)
        self.assertEqual(totals["candidate_evaluation_count"], 964)
        self.assertEqual(totals["candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["source_receipt_verified_count"], 3)
        self.assertEqual(totals["source_projection_mismatch_count"], 0)
        chwirut = metrics["datasets"][0]
        roszman = metrics["datasets"][1]
        enso = metrics["datasets"][2]
        self.assertAlmostEqual(chwirut["ratioSummary"]["median"], 0.25654045819729265)
        self.assertAlmostEqual(roszman["ratioSummary"]["median"], 0.690796188558053)
        self.assertEqual(enso["ratioSummary"]["median"], 1.0)
        self.assertEqual(chwirut["largestTightening"]["x"], 1.5)
        self.assertEqual(roszman["largestTightening"]["x"], -4868.68)
        self.assertEqual(enso["largestTightening"]["x"], 25.0)
        self.assertIsNone(metrics["forbiddenAggregates"]["crossDatasetPooledErrorMetrics"])
        self.assertIsNone(metrics["forbiddenAggregates"]["unifiedStabilityScore"])
        self.assertIsNone(metrics["forbiddenAggregates"]["globalOptimum"])
        self.assertFalse(metrics["decision"]["global_optimum_claimed"])
        receipt_path = ROOT / "validation/native-conservative-support-synthesis-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing conservative-support synthesis receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "exports/native-conservative-support-synthesis.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_inventory_unavailable_fold_and_no_score_scope(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-conservative-synthesis-unified-score",
            "claim-local-tightening-global-optimum",
            "evidence-native-conservative-support-synthesis",
            "counterexample-roszman1-fold5-inventory-unavailable",
            "counterexample-conservative-width-ratio-not-ranking",
            "experiment-native-conservative-support-synthesis-protocol",
            "counterexample-conservative-candidate-not-global-proof",
            "limitation-native-conservative-support-synthesis-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 345)
        self.assertEqual(len(graph["edges"]), 1026)
        self.assertEqual(nodes["claim-conservative-synthesis-unified-score"]["status"], "falsified")
        self.assertEqual(nodes["claim-local-tightening-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-conservative-width-ratio-not-ranking", "claim-conservative-synthesis-unified-score", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold5-inventory-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("evidence-native-conservative-support-synthesis", "claim-local-tightening-global-optimum", "contradicts"), edges)
        self.assertIn(("experiment-native-conservative-support-synthesis-protocol", "experiment-enso-phase-interval-triple-protocol", "supports"), edges)
        self.assertIn(("limitation-native-conservative-support-synthesis-scope", "claim-center-coverage-external-validation", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

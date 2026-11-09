import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class NativeEllipsoidCrossModelIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_units_ratios_and_unavailable_fold(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("native-ellipsoid-cross-model-synthesis", identifiers)
        self.assertEqual(len(packet["items"]), 66)
        item = next(item for item in packet["items"] if item["id"] == "native-ellipsoid-cross-model-synthesis")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["held_out_point_count"], 407)
        self.assertEqual(totals["certified_fold_count"], 14)
        self.assertEqual(totals["available_point_count"], 402)
        self.assertEqual(totals["covered_point_count"], 402)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unique_envelope_count"], 210)
        self.assertEqual(totals["source_receipt_verified_count"], 3)
        self.assertEqual(totals["source_projection_mismatch_count"], 0)
        self.assertEqual(totals["unavailable_fold_ids"], ["roszman1:5"])
        chwirut = metrics["datasets"][0]
        roszman = metrics["datasets"][1]
        enso = metrics["datasets"][2]
        self.assertAlmostEqual(chwirut["totals"]["max_envelope_width"], 170.14630922307612)
        self.assertAlmostEqual(roszman["totals"]["max_envelope_width"], 0.867292251653464)
        self.assertAlmostEqual(enso["totals"]["max_envelope_width"], 17.64192935677042)
        self.assertAlmostEqual(chwirut["folds"][0]["normalization"]["max_width_to_dataset_median"], 8.85159366718222)
        self.assertAlmostEqual(chwirut["folds"][0]["normalization"]["max_residual_to_dataset_median"], 11.007883635582775)
        self.assertAlmostEqual(roszman["folds"][4]["nativeTestRmse"], 0.006228106060478816)
        self.assertFalse(roszman["folds"][4]["predictionEnvelopeAvailable"])
        self.assertIsNone(roszman["folds"][4]["normalization"]["max_width_to_dataset_median"])
        self.assertIsNone(metrics["forbiddenAggregates"]["crossDatasetPooledErrorMetrics"])
        self.assertIsNone(metrics["forbiddenAggregates"]["crossDatasetStabilityScore"])
        self.assertFalse(metrics["decision"]["universal_stability_score_claimed"])
        receipt_path = ROOT / "validation/native-ellipsoid-cross-model-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing native ellipsoid cross-model validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "exports/native-ellipsoid-cross-model-synthesis.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_units_scores_counts_and_failure_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-cross-model-envelope-width-direct-ranking",
            "claim-normalized-envelope-ratio-stability-score",
            "evidence-native-ellipsoid-cross-model",
            "counterexample-roszman-fold5-low-rmse-no-envelope",
            "counterexample-chwirut-fold1-relative-width",
            "counterexample-envelope-count-not-point-count",
            "experiment-native-ellipsoid-cross-model-protocol",
            "limitation-native-ellipsoid-cross-model-normalization",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 321)
        self.assertEqual(len(graph["edges"]), 930)
        self.assertEqual(nodes["claim-cross-model-envelope-width-direct-ranking"]["status"], "falsified")
        self.assertEqual(nodes["claim-normalized-envelope-ratio-stability-score"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-chwirut-fold1-relative-width", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("counterexample-roszman-fold5-low-rmse-no-envelope", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("evidence-native-ellipsoid-cross-model", "claim-normalized-envelope-ratio-stability-score", "contradicts"), edges)
        self.assertIn(("experiment-native-ellipsoid-cross-model-protocol", "claim-center-coverage-external-validation", "tests"), edges)
        self.assertIn(("limitation-native-ellipsoid-cross-model-normalization", "claim-cross-model-envelope-width-direct-ranking", "limits"), edges)
        self.assertIn(("evidence-native-ellipsoid-cross-model", "evidence-native-identifiability-cross-model", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1NativeEllipsoidContinuousIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_crossing_width_and_center_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-native-ellipsoid-continuous-bounds", identifiers)
        self.assertEqual(len(packet["items"]), 67)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-native-ellipsoid-continuous-bounds")
        metrics = item["metrics"]
        self.assertEqual(metrics["totals"]["fold_count"], 5)
        self.assertEqual(metrics["totals"]["held_out_point_count"], 25)
        self.assertEqual(metrics["totals"]["unique_x_count"], 25)
        self.assertEqual(metrics["totals"]["certified_fold_count"], 4)
        self.assertEqual(metrics["totals"]["certified_fold_ids"], [1, 2, 3, 4])
        self.assertEqual(metrics["totals"]["unavailable_fold_ids"], [5])
        self.assertEqual(metrics["totals"]["available_point_count"], 20)
        self.assertEqual(metrics["totals"]["covered_point_count"], 20)
        self.assertEqual(metrics["totals"]["violation_point_count"], 0)
        self.assertEqual(metrics["totals"]["unavailable_point_count"], 5)
        self.assertEqual(metrics["totals"]["center_prediction_envelope_mismatch_count"], 0)
        self.assertAlmostEqual(metrics["totals"]["minimum_critical_sign_radius"], 2.828350890156889)
        self.assertEqual(metrics["totals"]["minimum_critical_sign_radius_fold"], 5)
        self.assertAlmostEqual(metrics["totals"]["max_envelope_width"], 0.867292251653464)
        self.assertAlmostEqual(metrics["totals"]["median_envelope_width"], 0.3543650116278472)
        self.assertAlmostEqual(metrics["totals"]["max_residual_upper_bound"], 0.4433913282171526)
        self.assertAlmostEqual(metrics["totals"]["median_residual_upper_bound"], 0.1853990741468824)
        fold5 = metrics["folds"][4]
        self.assertFalse(fold5["predictionEnvelopeAvailable"])
        self.assertAlmostEqual(fold5["signCertificate"]["endpoint_results"][1]["maximum"], 103.08875349466264)
        self.assertFalse(metrics["analysisScope"]["probability_region"])
        self.assertFalse(metrics["decision"]["center_consistency_used_as_external_validation"])
        receipt = json.loads((ROOT / "validation/roszman1-native-ellipsoid-continuous-check.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-native-ellipsoid-continuous-bounds.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_singularity_width_and_center_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-arctan-bounded-denominator-irrelevant",
            "claim-roszman-fold5-low-rmse-singularity-safe",
            "evidence-roszman1-native-ellipsoid-continuous",
            "counterexample-roszman1-fold5-crossing-singularity",
            "counterexample-roszman1-fold1-wide-envelope",
            "counterexample-roszman1-center-consistency-not-probability",
            "experiment-roszman1-native-ellipsoid-continuous-protocol",
            "limitation-roszman1-native-ellipsoid-sign-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 329)
        self.assertEqual(len(graph["edges"]), 962)
        self.assertEqual(nodes["claim-arctan-bounded-denominator-irrelevant"]["status"], "falsified")
        self.assertEqual(nodes["claim-roszman-fold5-low-rmse-singularity-safe"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-roszman1-fold5-crossing-singularity", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold5-crossing-singularity", "claim-arctan-bounded-denominator-irrelevant", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold1-wide-envelope", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-center-consistency-not-probability", "claim-center-coverage-external-validation", "contradicts"), edges)
        self.assertIn(("limitation-roszman1-native-ellipsoid-sign-scope", "evidence-roszman1-native-ellipsoid-continuous", "limits"), edges)
        self.assertIn(("evidence-roszman1-native-ellipsoid-continuous", "evidence-roszman1-native-identifiability", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

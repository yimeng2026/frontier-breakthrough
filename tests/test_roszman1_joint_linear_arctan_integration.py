import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1JointLinearArctanIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_tightening_unavailable_fold_and_candidates(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-joint-linear-arctan-intersection", identifiers)
        self.assertEqual(len(packet["items"]), 69)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-joint-linear-arctan-intersection")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["available_point_count"], 20)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unavailable_fold_ids"], [5])
        self.assertEqual(totals["joint_alternative_bound_count"], 20)
        self.assertEqual(totals["intersection_bound_count"], 20)
        self.assertEqual(totals["candidate_direction_count"], 32)
        self.assertEqual(totals["candidate_evaluation_count"], 160)
        self.assertEqual(totals["alternative_tighter_count"], 20)
        self.assertEqual(totals["alternative_wider_count"], 0)
        self.assertEqual(totals["intersection_tightened_count"], 20)
        self.assertEqual(totals["intersection_unchanged_count"], 0)
        self.assertEqual(totals["nonempty_intersection_count"], 20)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertEqual(totals["covered_point_count"], 20)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertAlmostEqual(totals["median_intersection_to_independent_width_ratio"], 0.690796188558053)
        self.assertAlmostEqual(totals["max_intersection_width_reduction"], 0.7008593776977347)
        largest = totals["largest_intersection_tightening"]
        self.assertEqual(largest["x"], -4868.68)
        self.assertAlmostEqual(largest["intersection_to_independent_width_ratio"], 0.19189941295847002)
        fold5 = metrics["folds"][4]
        self.assertFalse(fold5["predictionEnvelopeAvailable"])
        self.assertEqual(fold5["candidateEvaluationCount"], 0)
        self.assertEqual(fold5["envelopes"], [])
        self.assertEqual(len(fold5["points"]), 5)
        self.assertFalse(metrics["decision"]["fold5_given_finite_bound"])
        self.assertFalse(metrics["decision"]["joint_alternative_is_global_optimum"])
        receipt_path = ROOT / "validation/roszman1-joint-linear-arctan-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing Roszman1 joint-linear validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-joint-linear-arctan-intersection.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_tightening_unavailable_fold_and_nonoptimal_scope(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-independent-linear-corners-tightest",
            "claim-joint-linear-arctan-global-optimum",
            "evidence-roszman1-joint-linear-arctan",
            "evidence-roszman1-fold1-joint-tightening",
            "counterexample-roszman1-fold5-still-unavailable",
            "experiment-roszman1-joint-linear-protocol",
            "counterexample-roszman1-candidate-not-global-proof",
            "limitation-roszman1-joint-linear-arctan-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 345)
        self.assertEqual(len(graph["edges"]), 1026)
        self.assertEqual(nodes["claim-independent-linear-corners-tightest"]["status"], "falsified")
        self.assertEqual(nodes["claim-joint-linear-arctan-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-roszman1-fold1-joint-tightening", "claim-independent-linear-corners-tightest", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-fold5-still-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("evidence-roszman1-joint-linear-arctan", "claim-joint-linear-arctan-global-optimum", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-joint-linear-protocol", "experiment-roszman1-native-ellipsoid-continuous-protocol", "supports"), edges)
        self.assertIn(("limitation-roszman1-joint-linear-arctan-scope", "claim-prediction-stability-parameter-uniqueness", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Chwirut1LogSupportIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_all_tightening_candidates_and_related_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("chwirut1-log-support-intersection", identifiers)
        self.assertEqual(len(packet["items"]), 69)
        item = next(item for item in packet["items"] if item["id"] == "chwirut1-log-support-intersection")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["held_out_point_count"], 214)
        self.assertEqual(totals["unique_distance_count"], 22)
        self.assertEqual(totals["log_alternative_bound_count"], 22)
        self.assertEqual(totals["intersection_bound_count"], 22)
        self.assertEqual(totals["candidate_direction_count"], 30)
        self.assertEqual(totals["candidate_evaluation_count"], 132)
        self.assertEqual(totals["alternative_tighter_count"], 22)
        self.assertEqual(totals["alternative_wider_count"], 0)
        self.assertEqual(totals["intersection_tightened_count"], 22)
        self.assertEqual(totals["intersection_unchanged_count"], 0)
        self.assertEqual(totals["nonempty_intersection_count"], 22)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertEqual(totals["covered_point_count"], 214)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertAlmostEqual(totals["median_intersection_to_independent_width_ratio"], 0.25654045819729265)
        self.assertAlmostEqual(totals["max_intersection_width_reduction"], 20.935447900396312)
        largest = totals["largest_intersection_tightening"]
        self.assertEqual(largest["x"], 1.5)
        self.assertEqual(largest["tangent_winner"], "d_max")
        self.assertAlmostEqual(largest["intersection_to_independent_width_ratio"], 0.2130823595991901)
        self.assertEqual(totals["tangent_winner_counts"], {"d_min": 7, "d_center": 7, "d_max": 8})
        self.assertEqual(metrics["relatedPriorDataset"]["name"], "Chwirut2")
        self.assertTrue(metrics["relatedPriorDataset"]["same_native_model_family"])
        self.assertFalse(metrics["relatedPriorDataset"]["independent_model_family_or_laboratory_replication"])
        self.assertFalse(metrics["decision"]["log_alternative_is_global_optimum"])
        receipt_path = ROOT / "validation/chwirut1-log-support-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing Chwirut1 log-support validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/chwirut1-log-support-intersection.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_tightening_nonoptimal_scope_and_related_model(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-independent-numerator-denominator-tightest",
            "claim-log-intersection-global-optimum",
            "evidence-chwirut1-log-support",
            "evidence-chwirut1-fold2-x15-tightening",
            "counterexample-chwirut1-independent-extreme-composition-wide",
            "experiment-chwirut1-log-support-protocol",
            "counterexample-chwirut1-candidate-not-global-proof",
            "limitation-chwirut1-log-support-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 345)
        self.assertEqual(len(graph["edges"]), 1026)
        self.assertEqual(nodes["claim-independent-numerator-denominator-tightest"]["status"], "falsified")
        self.assertEqual(nodes["claim-log-intersection-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-chwirut1-independent-extreme-composition-wide", "claim-independent-numerator-denominator-tightest", "contradicts"), edges)
        self.assertIn(("evidence-chwirut1-log-support", "claim-log-intersection-global-optimum", "contradicts"), edges)
        self.assertIn(("evidence-chwirut1-fold2-x15-tightening", "evidence-chwirut1-log-support", "supports"), edges)
        self.assertIn(("experiment-chwirut1-log-support-protocol", "experiment-chwirut1-native-ellipsoid-continuous-protocol", "supports"), edges)
        self.assertIn(("limitation-chwirut1-log-support-scope", "claim-chwirut-extrapolation", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

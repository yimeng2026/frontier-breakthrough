import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1RatioDenominatorIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_extremizers_unavailable_fold_and_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-ratio-denominator-intersection", identifiers)
        self.assertEqual(len(packet["items"]), 68)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-ratio-denominator-intersection")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["available_point_count"], 20)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unavailable_fold_ids"], [5])
        self.assertEqual(totals["ratio_interval_count"], 20)
        self.assertEqual(totals["algebraic_extremizer_count"], 40)
        self.assertEqual(totals["support_candidate_evaluation_count"], 160)
        self.assertEqual(totals["candidate_evaluation_count"], 200)
        self.assertEqual(totals["ratio_candidate_violation_count"], 0)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["intersection_tightened_count"], 20)
        self.assertAlmostEqual(totals["median_intersection_to_joint_linear_width_ratio"], 0.9807825850555489)
        self.assertEqual(totals["largest_intersection_tightening"]["x"], -1208.68)
        self.assertEqual(totals["largest_ratio_tightening"]["x"], -996.31)
        self.assertAlmostEqual(totals["largest_ratio_tightening"]["ratio_interval_width_reduction"], 0.07692375150746189)
        self.assertIsNone(metrics["fullNonlinearGlobalOptimum"])
        self.assertFalse(metrics["decision"]["fold5_given_finite_bound"])
        self.assertFalse(metrics["decision"]["full_nonlinear_global_optimum_claimed"])
        self.assertEqual(metrics["fold2StoredCrossCovarianceDifference"], -1.0e-12)
        receipt_path = ROOT / "validation/roszman1-ratio-denominator-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing ratio-denominator receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-ratio-denominator-intersection.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_ratio_proof_asymmetry_and_unavailable_fold(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-ratio-independent-box-tightest",
            "claim-ratio-component-full-global-optimum",
            "evidence-roszman1-ratio-denominator",
            "counterexample-roszman1-ratio-storage-asymmetry",
            "experiment-roszman1-ratio-denominator-protocol",
            "counterexample-roszman1-ratio-fold5-unavailable",
            "counterexample-roszman1-ratio-candidate-not-global-proof",
            "limitation-roszman1-ratio-component-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 337)
        self.assertEqual(len(graph["edges"]), 994)
        self.assertEqual(nodes["claim-ratio-independent-box-tightest"]["status"], "falsified")
        self.assertEqual(nodes["claim-ratio-component-full-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-roszman1-ratio-denominator", "claim-ratio-independent-box-tightest", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-ratio-storage-asymmetry", "limitation-roszman1-ratio-component-scope", "supports"), edges)
        self.assertIn(("counterexample-roszman1-ratio-fold5-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-ratio-denominator-protocol", "experiment-roszman1-joint-linear-protocol", "supports"), edges)
        self.assertIn(("limitation-roszman1-ratio-component-scope", "claim-center-coverage-external-validation", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

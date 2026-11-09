import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1EllipsoidCoverGridIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_negative_result_and_full_cover_counts(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-ellipsoid-cover-grid", identifiers)
        self.assertEqual(len(packet["items"]), 68)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-ellipsoid-cover-grid")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["available_point_count"], 20)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["grid_cover_count"], 60)
        self.assertEqual(totals["cell_evaluation_count"], 5460)
        self.assertEqual(totals["candidate_evaluation_count"], 200)
        self.assertEqual(totals["candidate_grid_containment_check_count"], 600)
        self.assertEqual(totals["grid_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["primary_intersection_tightened_count"], 0)
        self.assertEqual(totals["primary_intersection_unchanged_count"], 20)
        self.assertEqual(totals["median_primary_intersection_to_ratio_width_ratio"], 1.0)
        self.assertEqual([item["intersection_unchanged_count"] for item in metrics["gridTotals"]], [20, 20, 20])
        self.assertEqual([item["cell_evaluation_count"] for item in metrics["gridTotals"]], [20, 320, 5120])
        self.assertIsNone(metrics["exactGlobalOptimum"])
        self.assertFalse(metrics["decision"]["exact_global_optimum_claimed"])
        self.assertFalse(metrics["decision"]["fold5_given_finite_bound"])
        receipt_path = ROOT / "validation/roszman1-ellipsoid-cover-grid-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing ellipsoid-cover grid receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-ellipsoid-cover-grid.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_negative_grid_result_cover_scope_and_fold5(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-grid-more-cells-tighter",
            "claim-grid-cover-exact-global-optimum",
            "evidence-roszman1-ellipsoid-cover-grid",
            "counterexample-roszman1-grid-all-unchanged",
            "experiment-roszman1-ellipsoid-cover-grid-protocol",
            "counterexample-roszman1-grid-fold5-unavailable",
            "counterexample-roszman1-coordinate-cover-not-optimal",
            "limitation-roszman1-grid-cover-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 337)
        self.assertEqual(len(graph["edges"]), 994)
        self.assertEqual(nodes["claim-grid-more-cells-tighter"]["status"], "falsified")
        self.assertEqual(nodes["claim-grid-cover-exact-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-roszman1-grid-all-unchanged", "claim-grid-more-cells-tighter", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-coordinate-cover-not-optimal", "claim-grid-cover-exact-global-optimum", "contradicts"), edges)
        self.assertIn(("counterexample-roszman1-grid-fold5-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-ellipsoid-cover-grid-protocol", "experiment-roszman1-ratio-denominator-protocol", "supports"), edges)
        self.assertIn(("limitation-roszman1-grid-cover-scope", "claim-center-coverage-external-validation", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

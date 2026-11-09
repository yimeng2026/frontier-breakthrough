import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1WhitenedCoverGridIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_tightening_transform_and_boundary_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-whitened-cover-grid", identifiers)
        self.assertEqual(len(packet["items"]), 71)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-whitened-cover-grid")
        metrics = item["metrics"]
        self.assertEqual(metrics["proofValidity"], "invalid_for_conservative_proof")
        self.assertEqual(metrics["supersededBy"], "roszman1-whitened-cover-grid-erratum-01")
        totals = metrics["totals"]
        self.assertEqual(totals["held_out_point_count"], 25)
        self.assertEqual(totals["available_point_count"], 20)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["grid_cover_count"], 60)
        self.assertEqual(totals["partition_cell_count"], 5460)
        self.assertEqual(totals["native_cell_evaluation_count"], 5460)
        self.assertEqual(totals["outside_cell_count"], 0)
        self.assertEqual(totals["unresolved_cell_count"], 0)
        self.assertEqual(totals["candidate_evaluation_count"], 200)
        self.assertEqual(totals["candidate_grid_containment_check_count"], 600)
        self.assertEqual(totals["transform_witness_count"], 200)
        self.assertEqual(totals["transform_violation_count"], 0)
        self.assertEqual(totals["primary_intersection_tightened_count"], 20)
        self.assertAlmostEqual(totals["median_primary_intersection_to_ratio_width_ratio"], 0.820642571296398)
        self.assertAlmostEqual(totals["max_primary_intersection_width_reduction"], 0.09000651529949602)
        self.assertEqual(totals["largest_primary_intersection_tightening"]["x"], -3373.14)
        self.assertEqual([item["intersection_tightened_count"] for item in metrics["gridTotals"]], [0, 17, 20])
        self.assertEqual([item["intersection_unchanged_count"] for item in metrics["gridTotals"]], [20, 3, 0])
        self.assertEqual(metrics["analysisScope"]["outside_boundary_amendment"], "01")
        self.assertIsNone(metrics["exactGlobalOptimum"])
        self.assertFalse(metrics["decision"]["fold5_given_finite_bound"])
        receipt_path = ROOT / "validation/roszman1-whitened-cover-grid-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing whitened-cover receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-whitened-cover-grid.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_tightening_boundary_counterexample_and_fold5(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-whitening-alone-tightens",
            "claim-whitened-cover-exact-optimum",
            "evidence-roszman1-whitened-cover-grid",
            "counterexample-whitened-grid1-unchanged",
            "experiment-roszman1-whitened-cover-grid-protocol",
            "counterexample-whitened-boundary-rounding",
            "counterexample-whitened-fold5-unavailable",
            "limitation-roszman1-whitened-cover-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 361)
        self.assertEqual(len(graph["edges"]), 1091)
        self.assertEqual(nodes["claim-whitening-alone-tightens"]["status"], "falsified")
        self.assertEqual(nodes["claim-whitened-cover-exact-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-whitened-grid1-unchanged", "claim-whitening-alone-tightens", "contradicts"), edges)
        self.assertIn(("counterexample-whitened-boundary-rounding", "limitation-roszman1-whitened-cover-scope", "supports"), edges)
        self.assertIn(("counterexample-whitened-fold5-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-whitened-cover-grid-protocol", "experiment-roszman1-ellipsoid-cover-grid-protocol", "supports"), edges)
        self.assertIn(("limitation-roszman1-whitened-cover-scope", "claim-center-coverage-external-validation", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

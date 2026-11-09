import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1WhitenedCoverGridErratumIntegrationTests(unittest.TestCase):
    def test_original_is_flagged_and_corrected_evidence_is_current(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(len(packet["items"]), 71)
        original = next(item for item in packet["items"] if item["id"] == "roszman1-whitened-cover-grid")
        self.assertEqual(original["metrics"]["proofValidity"], "invalid_for_conservative_proof")
        self.assertEqual(original["metrics"]["supersededBy"], "roszman1-whitened-cover-grid-erratum-01")
        item = next(item for item in packet["items"] if item["id"] == "roszman1-whitened-cover-grid-erratum-01")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["partition_cell_count"], 5460)
        self.assertEqual(totals["native_cell_evaluation_count"], 5460)
        self.assertEqual(totals["unresolved_cell_count"], 0)
        self.assertEqual(totals["candidate_evaluation_count"], 200)
        self.assertEqual(totals["candidate_grid_containment_check_count"], 600)
        self.assertEqual(totals["vertex_evaluation_count"], 1920)
        self.assertEqual(totals["vertex_interval_violation_count"], 0)
        self.assertEqual(totals["primary_intersection_tightened_count"], 17)
        self.assertEqual(totals["primary_intersection_unchanged_count"], 3)
        self.assertAlmostEqual(totals["median_primary_intersection_to_ratio_width_ratio"], 0.4474424821614995)
        self.assertAlmostEqual(totals["max_primary_intersection_width_reduction"], 0.1610034968796093)
        self.assertEqual(totals["largest_primary_intersection_tightening"]["x"], -1894.65)
        self.assertEqual(metrics["originalProofValidity"], "invalid_for_conservative_proof")
        self.assertFalse(metrics["decision"]["original_results_used_as_valid_cover"])
        self.assertIsNone(metrics["exactGlobalOptimum"])
        receipt_path = ROOT / "validation/roszman1-whitened-cover-grid-erratum-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing corrected whitened-cover receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-whitened-cover-grid-corrected-01.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_distinguishes_original_error_from_corrected_results(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-original-whitened-cover-valid",
            "claim-corrected-whitening-exact-global-optimum",
            "evidence-roszman1-whitened-cover-erratum",
            "counterexample-whitened-denominator-sign-error",
            "experiment-roszman1-whitened-cover-erratum-protocol",
            "counterexample-whitened-corrected-grid1-unchanged",
            "counterexample-whitened-corrected-fold5-unavailable",
            "limitation-roszman1-whitened-original-invalid",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 361)
        self.assertEqual(len(graph["edges"]), 1091)
        self.assertEqual(nodes["claim-original-whitened-cover-valid"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-whitened-denominator-sign-error", "evidence-roszman1-whitened-cover-grid", "contradicts"), edges)
        self.assertIn(("limitation-roszman1-whitened-original-invalid", "evidence-roszman1-whitened-cover-grid", "limits"), edges)
        self.assertIn(("counterexample-whitened-corrected-grid1-unchanged", "claim-whitening-alone-tightens", "contradicts"), edges)
        self.assertIn(("experiment-roszman1-whitened-cover-erratum-protocol", "claim-knowledge-graph", "tests"), edges)


if __name__ == "__main__":
    unittest.main()

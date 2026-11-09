import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class Roszman1WhitenedGridConvergenceIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_incremental_results_and_source_chain(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("roszman1-whitened-grid-convergence", identifiers)
        self.assertEqual(len(packet["items"]), 71)
        item = next(item for item in packet["items"] if item["id"] == "roszman1-whitened-grid-convergence")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["grid8_partition_cell_count"], 81920)
        self.assertEqual(totals["native_cell_evaluation_count"], 51520)
        self.assertEqual(totals["outside_cell_count"], 30400)
        self.assertEqual(totals["unresolved_cell_count"], 0)
        self.assertEqual(totals["candidate_evaluation_count"], 200)
        self.assertEqual(totals["candidate_grid8_containment_check_count"], 200)
        self.assertEqual(totals["grid8_additional_tightened_count"], 20)
        self.assertEqual(totals["grid8_plateau_count"], 0)
        self.assertEqual(totals["grid8_vertex_evaluation_count"], 640)
        self.assertEqual(totals["feasible_vertex_witness_count"], 44)
        self.assertEqual(totals["outer_vertex_witness_count"], 596)
        self.assertAlmostEqual(totals["median_grid8_to_grid4_width_ratio"], 0.5874946735203854)
        self.assertAlmostEqual(totals["max_grid8_width_reduction_vs_grid4"], 0.04639800457926707)
        self.assertEqual(totals["largest_grid8_incremental_tightening"]["x"], -1894.65)
        self.assertEqual(metrics["analysisScope"]["outside_count_amendment"], "03")
        self.assertEqual(metrics["analysisScope"]["original_whitened_proof_validity"], "invalid_for_conservative_proof")
        self.assertIsNone(metrics["exactGlobalOptimum"])
        self.assertTrue(metrics["stage56ReceiptVerified"])
        receipt_path = ROOT / "validation/roszman1-whitened-grid-convergence-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing grid-8 convergence receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/roszman1-whitened-grid-convergence.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_incremental_outer_vertices_and_original_erratum(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-grid8-convergence-global-optimum",
            "claim-outer-vertices-feasible",
            "evidence-roszman1-whitened-grid-convergence",
            "counterexample-grid8-incremental-not-asymptotic",
            "experiment-roszman1-whitened-grid-convergence-protocol",
            "counterexample-grid8-outside-count-not-zero",
            "counterexample-grid8-fold5-unavailable",
            "limitation-roszman1-grid8-convergence-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 361)
        self.assertEqual(len(graph["edges"]), 1091)
        self.assertEqual(nodes["claim-grid8-convergence-global-optimum"]["status"], "falsified")
        self.assertEqual(nodes["claim-outer-vertices-feasible"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-grid8-incremental-not-asymptotic", "claim-grid8-convergence-global-optimum", "contradicts"), edges)
        self.assertIn(("counterexample-grid8-outside-count-not-zero", "claim-grid-cover-exact-global-optimum", "contradicts"), edges)
        self.assertIn(("evidence-roszman1-whitened-grid-convergence", "evidence-roszman1-whitened-cover-erratum", "supports"), edges)
        self.assertIn(("counterexample-grid8-fold5-unavailable", "claim-roszman-fold5-low-rmse-singularity-safe", "contradicts"), edges)


if __name__ == "__main__":
    unittest.main()

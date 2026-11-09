import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoPhaseIntervalTripleIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_width_mismatch_local_gains_and_candidates(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-phase-interval-triple-intersection", identifiers)
        self.assertEqual(len(packet["items"]), 68)
        item = next(item for item in packet["items"] if item["id"] == "enso-phase-interval-triple-intersection")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["phase_alternative_bound_count"], 168)
        self.assertEqual(totals["triple_intersection_bound_count"], 168)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["phase_tighter_than_lipschitz_count"], 29)
        self.assertEqual(totals["phase_wider_than_lipschitz_count"], 139)
        self.assertEqual(totals["triple_tightened_count"], 37)
        self.assertEqual(totals["triple_unchanged_count"], 131)
        self.assertEqual(totals["nonempty_triple_intersection_count"], 168)
        self.assertEqual(totals["phase_candidate_violation_count"], 0)
        self.assertEqual(totals["triple_candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertAlmostEqual(totals["median_phase_to_lipschitz_width_ratio"], 1.5386143812259636)
        self.assertAlmostEqual(totals["min_triple_to_lipschitz_width_ratio"], 0.7474092252857671)
        self.assertEqual(totals["median_triple_to_lipschitz_width_ratio"], 1.0)
        self.assertAlmostEqual(totals["max_triple_width_reduction"], 4.371401855122352)
        largest = totals["largest_triple_tightening"]
        self.assertEqual(largest["x"], 25.0)
        self.assertAlmostEqual(largest["triple_to_lipschitz_width_ratio"], 0.7474092252857671)
        self.assertEqual([fold["phaseTighterThanLipschitzCount"] for fold in metrics["folds"]], [28, 1, 0, 0, 0])
        self.assertEqual([fold["tripleTightenedCount"] for fold in metrics["folds"]], [29, 8, 0, 0, 0])
        self.assertTrue(metrics["independentReceiptVerified"])
        self.assertTrue(metrics["sliceReceiptVerified"])
        self.assertTrue(metrics["lipschitzReceiptVerified"])
        self.assertFalse(metrics["decision"]["phase_alternative_is_global_optimum"])
        self.assertFalse(metrics["decision"]["triple_intersection_is_global_optimum"])
        receipt_path = ROOT / "validation/enso-phase-interval-triple-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing phase-interval triple validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-phase-interval-triple-intersection.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_phase_width_mismatch_local_gains_and_scope(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-phase-alternative-always-tighter",
            "claim-triple-intersection-global-optimum",
            "evidence-enso-phase-interval-triple",
            "counterexample-enso-phase-wider-majority",
            "evidence-enso-phase-triple-37-local-gains",
            "counterexample-enso-phase-width-vs-intersection-mismatch",
            "experiment-enso-phase-interval-triple-protocol",
            "limitation-enso-phase-interval-triple-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 337)
        self.assertEqual(len(graph["edges"]), 994)
        self.assertEqual(nodes["claim-phase-alternative-always-tighter"]["status"], "falsified")
        self.assertEqual(nodes["claim-triple-intersection-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-enso-phase-wider-majority", "claim-phase-alternative-always-tighter", "contradicts"), edges)
        self.assertIn(("evidence-enso-phase-interval-triple", "claim-triple-intersection-global-optimum", "contradicts"), edges)
        self.assertIn(("evidence-enso-phase-triple-37-local-gains", "evidence-enso-phase-interval-triple", "supports"), edges)
        self.assertIn(("counterexample-enso-phase-width-vs-intersection-mismatch", "claim-normalized-envelope-ratio-stability-score", "contradicts"), edges)
        self.assertIn(("experiment-enso-phase-interval-triple-protocol", "experiment-enso-full-lipschitz-protocol", "supports"), edges)
        self.assertIn(("evidence-enso-phase-interval-triple", "evidence-enso-full-lipschitz-intersection", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

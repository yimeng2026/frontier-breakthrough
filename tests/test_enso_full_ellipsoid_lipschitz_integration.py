import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoFullEllipsoidLipschitzIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_wider_alternative_local_intersection_and_candidates(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-full-ellipsoid-lipschitz-intersection", identifiers)
        self.assertEqual(len(packet["items"]), 64)
        item = next(item for item in packet["items"] if item["id"] == "enso-full-ellipsoid-lipschitz-intersection")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["alternative_bound_count"], 168)
        self.assertEqual(totals["intersection_bound_count"], 168)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["alternative_tighter_count"], 13)
        self.assertEqual(totals["alternative_wider_count"], 155)
        self.assertEqual(totals["alternative_equal_count"], 0)
        self.assertEqual(totals["intersection_tightened_count"], 13)
        self.assertEqual(totals["intersection_unchanged_count"], 155)
        self.assertEqual(totals["nonempty_intersection_count"], 168)
        self.assertEqual(totals["alternative_candidate_violation_count"], 0)
        self.assertEqual(totals["intersection_candidate_violation_count"], 0)
        self.assertEqual(totals["independent_candidate_violation_count"], 0)
        self.assertAlmostEqual(totals["median_alternative_to_independent_width_ratio"], 2.3027937209620504)
        self.assertAlmostEqual(totals["min_intersection_to_independent_width_ratio"], 0.509592261709032)
        self.assertEqual(totals["median_intersection_to_independent_width_ratio"], 1.0)
        self.assertAlmostEqual(totals["max_intersection_width_reduction"], 8.086192176366756)
        largest = totals["largest_intersection_tightening"]
        self.assertEqual(largest["x"], 4.0)
        self.assertAlmostEqual(largest["intersection_to_independent_width_ratio"], 0.5359035647336762)
        self.assertEqual([fold["intersectionTightenedCount"] for fold in metrics["folds"]], [13, 0, 0, 0, 0])
        self.assertTrue(metrics["independentReceiptVerified"])
        self.assertTrue(metrics["sliceReceiptVerified"])
        self.assertFalse(metrics["decision"]["intersection_is_global_optimum"])
        self.assertFalse(metrics["decision"]["candidate_checks_replace_analytic_proof"])
        receipt_path = ROOT / "validation/enso-full-ellipsoid-lipschitz-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing full-ellipsoid Lipschitz validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-full-ellipsoid-lipschitz-intersection.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_wider_alternative_local_tightening_and_proof_scope(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-lipschitz-alternative-always-tighter",
            "claim-intersection-global-optimum",
            "evidence-enso-full-lipschitz-intersection",
            "counterexample-enso-lipschitz-wider-majority",
            "evidence-enso-fold1-x4-intersection-tightening",
            "experiment-enso-full-lipschitz-protocol",
            "counterexample-enso-candidate-check-not-global-proof",
            "limitation-enso-full-lipschitz-intersection-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 305)
        self.assertEqual(len(graph["edges"]), 866)
        self.assertEqual(nodes["claim-lipschitz-alternative-always-tighter"]["status"], "falsified")
        self.assertEqual(nodes["claim-intersection-global-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-enso-lipschitz-wider-majority", "claim-lipschitz-alternative-always-tighter", "contradicts"), edges)
        self.assertIn(("evidence-enso-full-lipschitz-intersection", "claim-intersection-global-optimum", "contradicts"), edges)
        self.assertIn(("evidence-enso-fold1-x4-intersection-tightening", "evidence-enso-full-lipschitz-intersection", "supports"), edges)
        self.assertIn(("experiment-enso-full-lipschitz-protocol", "experiment-enso-conditional-period-slice-protocol", "supports"), edges)
        self.assertIn(("limitation-enso-full-lipschitz-intersection-scope", "claim-independent-fourier-envelope-joint-optimum", "limits"), edges)
        self.assertIn(("evidence-enso-full-lipschitz-intersection", "evidence-enso-conditional-period-slice", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

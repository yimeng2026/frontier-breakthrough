import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoConditionalPeriodSliceIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_tightening_witnesses_and_amendment(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-conditional-period-slice-bounds", identifiers)
        self.assertEqual(len(packet["items"]), 67)
        item = next(item for item in packet["items"] if item["id"] == "enso-conditional-period-slice-bounds")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["slice_envelope_count"], 168)
        self.assertEqual(totals["candidate_direction_count"], 20)
        self.assertEqual(totals["candidate_evaluation_count"], 672)
        self.assertEqual(totals["slice_violation_evaluation_count"], 199)
        self.assertEqual(totals["slice_violating_envelope_count"], 95)
        self.assertEqual(totals["full_independent_violation_count"], 0)
        self.assertEqual(totals["slice_containment_violation_count"], 0)
        self.assertEqual(totals["candidate_feasibility_failure_count"], 0)
        self.assertEqual(totals["slice_global_validity"], "falsified_by_feasible_candidate")
        self.assertAlmostEqual(totals["median_slice_to_independent_width_ratio"], 0.31983975629460537)
        self.assertAlmostEqual(totals["max_width_reduction"], 13.283611289252011)
        self.assertAlmostEqual(totals["max_slice_violation_exceedance"], 2.3416912445042737)
        witness = totals["largest_violation_witness"]
        self.assertEqual(witness["fold"], 4)
        self.assertEqual(witness["direction"], "b4_minus")
        self.assertEqual(witness["x"], 134.0)
        self.assertTrue(witness["inside_independent_baseline"])
        self.assertEqual([fold["sliceViolationEvaluationCount"] for fold in metrics["folds"]], [56, 4, 0, 57, 82])
        self.assertEqual(metrics["protocolCommits"]["originalProtocol"], "94d7cb0")
        self.assertEqual(metrics["protocolCommits"]["supportDirectionAmendment"], "e93dae0")
        self.assertFalse(metrics["decision"]["slice_bound_called_full_ellipsoid_bound"])
        self.assertFalse(metrics["decision"]["zero_witness_called_safety_proof"])
        receipt_path = ROOT / "validation/enso-conditional-period-slice-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing conditional-period slice validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-conditional-period-slice-bounds.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_slice_scope_witnesses_and_support_amendment(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-slice-bound-full-ellipsoid",
            "claim-marginal-block-equals-schur-slice",
            "claim-zero-candidate-violations-prove-full-safety",
            "evidence-enso-conditional-period-slice",
            "counterexample-enso-slice-fold4-x134-export",
            "counterexample-enso-fold3-zero-witness-not-safe",
            "counterexample-enso-coordinate-only-candidate-infeasible",
            "experiment-enso-conditional-period-slice-protocol",
            "experiment-enso-support-direction-amendment",
            "limitation-enso-conditional-period-slice-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 329)
        self.assertEqual(len(graph["edges"]), 962)
        self.assertEqual(nodes["claim-slice-bound-full-ellipsoid"]["status"], "falsified")
        self.assertEqual(nodes["claim-marginal-block-equals-schur-slice"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("counterexample-enso-slice-fold4-x134-export", "claim-slice-bound-full-ellipsoid", "contradicts"), edges)
        self.assertIn(("counterexample-enso-fold3-zero-witness-not-safe", "claim-zero-candidate-violations-prove-full-safety", "contradicts"), edges)
        self.assertIn(("counterexample-enso-coordinate-only-candidate-infeasible", "experiment-enso-support-direction-amendment", "supports"), edges)
        self.assertIn(("experiment-enso-support-direction-amendment", "claim-knowledge-graph", "tests"), edges)
        self.assertIn(("limitation-enso-conditional-period-slice-scope", "claim-independent-fourier-envelope-joint-optimum", "limits"), edges)
        self.assertIn(("evidence-enso-conditional-period-slice", "evidence-enso-native-ellipsoid-continuous", "supports"), edges)


if __name__ == "__main__":
    unittest.main()

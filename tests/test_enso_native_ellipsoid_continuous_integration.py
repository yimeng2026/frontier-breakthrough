import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_frontier_knowledge_graph import build_graph


class EnsoNativeEllipsoidContinuousIntegrationTests(unittest.TestCase):
    def test_evidence_preserves_period_width_and_center_scope(self):
        packet = json.loads((ROOT / "exports/frontier-evidence.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in packet["items"]}
        self.assertIn("enso-native-ellipsoid-continuous-bounds", identifiers)
        self.assertEqual(len(packet["items"]), 59)
        item = next(item for item in packet["items"] if item["id"] == "enso-native-ellipsoid-continuous-bounds")
        metrics = item["metrics"]
        totals = metrics["totals"]
        self.assertEqual(totals["fold_count"], 5)
        self.assertEqual(totals["held_out_point_count"], 168)
        self.assertEqual(totals["unique_month_count"], 168)
        self.assertEqual(totals["unique_envelope_count"], 168)
        self.assertEqual(totals["certified_fold_count"], 5)
        self.assertEqual(totals["certified_fold_ids"], [1, 2, 3, 4, 5])
        self.assertEqual(totals["unavailable_fold_ids"], [])
        self.assertEqual(totals["available_point_count"], 168)
        self.assertEqual(totals["covered_point_count"], 168)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertEqual(totals["unavailable_point_count"], 0)
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        self.assertAlmostEqual(totals["minimum_critical_period_radius"], 26.76683884611663)
        self.assertEqual(totals["minimum_critical_period_radius_fold"], 4)
        self.assertEqual(totals["minimum_critical_period_parameter"], "b4")
        self.assertAlmostEqual(totals["max_envelope_width"], 17.64192935677042)
        self.assertAlmostEqual(totals["median_envelope_width"], 13.164436414771593)
        self.assertAlmostEqual(totals["max_residual_upper_bound"], 14.576765863967406)
        self.assertAlmostEqual(totals["median_residual_upper_bound"], 8.516811559710845)
        fold4 = metrics["folds"][3]
        self.assertAlmostEqual(fold4["criticalPeriod"]["b4_radius"], 26.76683884611663)
        self.assertAlmostEqual(fold4["periodCertificate"]["b4_minimum"], 38.0037866239862)
        self.assertAlmostEqual(fold4["periodCertificate"]["b7_minimum"], 24.2810144640915)
        self.assertTrue(fold4["negativeControl"]["half_radius_accepted"])
        self.assertTrue(fold4["negativeControl"]["exact_radius_rejected"])
        self.assertFalse(metrics["analysisScope"]["probability_region"])
        self.assertFalse(metrics["analysisScope"]["taylor_or_fixed_period_approximation"])
        self.assertFalse(metrics["analysisScope"]["exact_rational_certificate"])
        self.assertFalse(metrics["decision"]["center_consistency_used_as_external_validation"])
        receipt_path = ROOT / "validation/enso-native-ellipsoid-continuous-check.json"
        self.assertTrue(receipt_path.is_file(), "Missing ENSO ellipsoid validation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        expected_hash = hashlib.sha256((ROOT / "validation/enso-native-ellipsoid-continuous-bounds.json").read_bytes()).hexdigest()
        self.assertEqual(receipt["summarySha256"], expected_hash)
        self.assertEqual(metrics["implementation"]["summarySha256"], expected_hash)

    def test_graph_links_period_width_and_center_counterexamples(self):
        graph = build_graph(ROOT)
        nodes = {node["id"]: node for node in graph["nodes"]}
        identifiers = [
            "claim-positive-period-proves-physical-period",
            "claim-independent-fourier-envelope-joint-optimum",
            "evidence-enso-native-ellipsoid-continuous",
            "counterexample-enso-wide-fourier-envelope",
            "counterexample-enso-center-consistency-not-probability",
            "experiment-enso-native-ellipsoid-continuous-protocol",
            "limitation-enso-native-ellipsoid-period-scope",
        ]
        for identifier in identifiers:
            self.assertIn(identifier, nodes)
        self.assertEqual(len(graph["nodes"]), 263)
        self.assertEqual(len(graph["edges"]), 703)
        self.assertEqual(nodes["claim-positive-period-proves-physical-period"]["status"], "falsified")
        self.assertEqual(nodes["claim-independent-fourier-envelope-joint-optimum"]["status"], "falsified")
        edges = {(item["from"], item["to"], item["relation"]) for item in graph["edges"]}
        self.assertIn(("evidence-enso-native-ellipsoid-continuous", "claim-positive-period-proves-physical-period", "contradicts"), edges)
        self.assertIn(("counterexample-enso-wide-fourier-envelope", "claim-finite-bound-high-information", "contradicts"), edges)
        self.assertIn(("counterexample-enso-center-consistency-not-probability", "claim-center-coverage-external-validation", "contradicts"), edges)
        self.assertIn(("experiment-enso-native-ellipsoid-continuous-protocol", "claim-independent-fourier-envelope-joint-optimum", "tests"), edges)
        self.assertIn(("limitation-enso-native-ellipsoid-period-scope", "evidence-enso-native-ellipsoid-continuous", "limits"), edges)
        self.assertIn(("evidence-enso-native-ellipsoid-continuous", "evidence-enso-native-identifiability", "supports"), edges)
        self.assertIn(("evidence-enso-native-ellipsoid-continuous", "evidence-roszman1-native-ellipsoid-continuous", "supports"), edges)
        self.assertIn(("evidence-enso-native-ellipsoid-continuous", "counterexample-enso-optimizer-mismatch", "supports"), edges)
        self.assertIn(("limitation-enso-native-ellipsoid-period-scope", "claim-certified-forward-equals-optimizer-reproduction", "limits"), edges)


if __name__ == "__main__":
    unittest.main()

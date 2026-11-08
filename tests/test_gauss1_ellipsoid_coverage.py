import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_gauss1_ellipsoid_coverage.py"


class Gauss1EllipsoidCoverageTests(unittest.TestCase):
    def load_analysis_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Gauss1 analysis wrapper: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_gauss1_ellipsoid_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_frozen_driver_audits_all_250_points_without_success_requirement(self):
        module = self.load_analysis_module()
        summary = module.analyze()
        self.assertEqual(summary["status"], "computed_external_gauss1_ellipsoid_coverage")
        self.assertEqual(summary["analysis_scope"]["observations"], 250)
        self.assertTrue(summary["analysis_scope"]["candidate_model_not_native"])
        self.assertFalse(summary["analysis_scope"]["independent_physical_experiment"])
        self.assertEqual(summary["totals"]["point_count"], 250)
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual([len(case["point_results"]) for case in summary["folds"]], [50] * 5)
        self.assertEqual(summary["totals"]["coverage_violation_count"], sum(point.get("coverage_violation") == 1 for case in summary["folds"] for point in case["point_results"]))
        self.assertEqual(module.validate_summary(summary), [])

    def test_final_outputs_retain_audit_and_real_figure(self):
        module = self.load_analysis_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        summary = json.loads(module.OUT.read_text(encoding="utf-8"))
        protocol = json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(summary["protocol_sha256"], hashlib.sha256(module.PROTOCOL.read_bytes()).hexdigest())
        self.assertEqual(summary["analysis_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(hashlib.sha256((ROOT / protocol["implementation_rule"]["driver"]).read_bytes()).hexdigest(), protocol["implementation_rule"]["driver_sha256"])
        self.assertEqual(module.validate_summary(summary), [])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["native_physical_model_claimed"])
        self.assertFalse(summary["decision"]["universal_external_validity_claimed"])


if __name__ == "__main__":
    unittest.main()

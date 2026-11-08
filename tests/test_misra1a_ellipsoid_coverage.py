import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_misra1a_ellipsoid_coverage.py"


class Misra1aEllipsoidCoverageTests(unittest.TestCase):
    def load_analysis_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Misra1a analysis wrapper: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_misra1a_ellipsoid_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_frozen_driver_audits_all_14_points_without_success_requirement(self):
        module = self.load_analysis_module()
        summary = module.analyze()
        self.assertEqual(summary["status"], "computed_external_misra1a_ellipsoid_coverage")
        self.assertEqual(summary["analysis_scope"]["observations"], 14)
        self.assertTrue(summary["analysis_scope"]["candidate_model_not_native"])
        self.assertFalse(summary["analysis_scope"]["independent_physical_experiment"])
        self.assertEqual(summary["totals"]["point_count"], 14)
        self.assertEqual(len(summary["folds"]), 5)
        self.assertEqual([len(case["point_results"]) for case in summary["folds"]], [3, 3, 3, 3, 2])
        self.assertEqual(summary["totals"]["coverage_violation_count"], sum(point.get("coverage_violation") == 1 for case in summary["folds"] for point in case["point_results"]))
        for case in summary["folds"]:
            for point in case["point_results"]:
                if point["ellipsoid_available"]:
                    self.assertAlmostEqual(point["actual_absolute_residual"] + point["ellipsoid_prediction_shift_upper_bound_float"], point["ellipsoid_absolute_residual_upper_bound_float"], places=8)
                    self.assertGreaterEqual(point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"], 0)
                    self.assertLessEqual(point["ellipsoid_prediction_shift_upper_bound_float"] / point["ellipsoid_absolute_residual_upper_bound_float"], 1)
        self.assertEqual(module.validate_summary(summary), [])

    def test_final_outputs_retain_audit_and_real_figure(self):
        module = self.load_analysis_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        summary = module.analyze()
        protocol = module.PROTOCOL.read_text(encoding="utf-8")
        self.assertEqual(summary["protocol_sha256"], hashlib.sha256(module.PROTOCOL.read_bytes()).hexdigest())
        self.assertEqual(summary["analysis_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(summary["analysis_scope"]["native_model"], module.json.loads(protocol)["dataset_scope"]["native_model"])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["native_physical_model_claimed"])
        self.assertFalse(summary["decision"]["universal_external_validity_claimed"])


if __name__ == "__main__":
    unittest.main()

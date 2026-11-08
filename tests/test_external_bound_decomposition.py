import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_external_bound_decomposition.py"


class ExternalBoundDecompositionTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing decomposition builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_external_bound_decomposition", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_all_available_points_decompose_without_mismatch(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 365)
        self.assertEqual(totals["ellipsoid_available_point_count"], 305)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 60)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual(totals["undefined_zero_bound_count"], 0)
        self.assertEqual(summary["gauss1_regression"]["check_count"], 4)
        self.assertEqual(summary["gauss1_regression"]["mismatch_count"], 0)
        self.assertEqual(module.validate_summary(summary), [])

    def test_dataset_distributions_and_scope_are_preserved(self):
        module = self.load_module()
        summary = module.analyze()
        datasets = {item["id"]: item for item in summary["datasets"]}
        self.assertEqual([datasets[key]["ellipsoid_available_point_count"] for key in ["filip", "mgh17", "gauss1"]], [82, 33, 190])
        maximum = datasets["gauss1"]["maximum_residual_upper_bound"]
        self.assertEqual(maximum["x"], 72.0)
        self.assertGreater(maximum["shift_share"], 0.95)
        self.assertFalse(summary["decision"]["universal_dataset_ranking_claimed"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["unavailable_points_treated_as_zero"])

    def test_zero_bound_share_remains_undefined(self):
        module = self.load_module()
        synthetic = {"folds": [{"fold": 1, "point_results": [{"x": 0.0, "ellipsoid_available": True, "actual_absolute_residual": 0.0, "ellipsoid_prediction_shift_upper_bound_float": 0.0, "ellipsoid_absolute_residual_upper_bound_float": 0.0}]}]}
        records, mismatches = module.decompose_points(synthetic, 0.5)
        self.assertEqual(mismatches, [])
        self.assertIsNone(records[0]["shift_share"])
        self.assertEqual(records[0]["dominant"], "undefined_zero_bound")

    def test_final_outputs_are_real(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

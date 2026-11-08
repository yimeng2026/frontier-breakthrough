import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
EXTERNAL_SCRIPT = ROOT / "scripts/build_external_bound_decomposition_v5.py"


class BoundDecompositionV5Tests(unittest.TestCase):
    def load_module(self, path, name):
        self.assertTrue(path.is_file(), f"Missing v5 builder: {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_seven_external_datasets_include_roszman1_increment(self):
        module = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v5")
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 786)
        self.assertEqual(totals["ellipsoid_available_point_count"], 532)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 254)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 255)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 277)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual([item["ellipsoid_available_point_count"] for item in summary["datasets"]], [82, 33, 190, 4, 83, 135, 5])
        roszman1 = summary["datasets"][-1]
        self.assertEqual(roszman1["id"], "roszman1")
        self.assertEqual(roszman1["ellipsoid_unavailable_point_count"], 20)
        self.assertEqual(roszman1["prediction_shift_dominant_point_count"], 5)
        self.assertEqual(roszman1["snapshot_residual_dominant_point_count"], 0)
        self.assertEqual([case["available_point_count"] for case in roszman1["folds"]], [0, 5, 0, 0, 0])
        self.assertEqual(summary["gauss1_regression"]["mismatch_count"], 0)
        self.assertIn("254 unavailable points", " ".join(summary["limitations"]))
        self.assertFalse(summary["analysis_scope"]["chwirut1_independent_model_family_test"])
        self.assertFalse(summary["analysis_scope"]["enso_native_periodic_model_claimed"])
        self.assertFalse(summary["analysis_scope"]["roszman1_native_arctangent_model_claimed"])
        self.assertFalse(summary["analysis_scope"]["roszman1_independent_physical_experiment"])
        self.assertIn("only in fold 2", " ".join(summary["limitations"]))
        self.assertEqual(module.validate_summary(summary), [])

    def test_final_v5_external_output_is_real(self):
        module = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v5")
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

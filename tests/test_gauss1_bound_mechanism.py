import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_gauss1_bound_mechanism.py"


class Gauss1BoundMechanismTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing diagnostic: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_gauss1_bound_mechanism", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_all_points_are_classified_and_stored_bounds_agree(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 250)
        self.assertEqual(totals["ellipsoid_available_point_count"], 190)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 60)
        self.assertEqual(totals["classification_mismatch_count"], 0)
        self.assertEqual(totals["stored_bound_agreement_count"], 190)
        self.assertEqual(totals["stored_bound_mismatch_count"], 0)
        self.assertEqual(module.validate_summary(summary), [])
        folds = {case["fold"]: case for case in summary["folds"]}
        self.assertFalse(folds[2]["continuous_ellipsoid_safe"])
        self.assertEqual(folds[2]["ellipsoid_available_point_count"], 40)
        self.assertFalse(folds[5]["continuous_ellipsoid_safe"])
        self.assertEqual(folds[5]["ellipsoid_available_point_count"], 0)
        self.assertEqual(sum(folds[5]["unavailable_reason_counts"].values()), 50)
        first_maximum = folds[1]["maximum_residual_upper_bound"]
        second_maximum = folds[2]["maximum_residual_upper_bound"]
        self.assertIn("shift_share", first_maximum)
        self.assertIn("shift_share", second_maximum)
        self.assertLess(first_maximum["shift_share"], 0.05)
        self.assertGreater(second_maximum["shift_share"], 0.95)
        self.assertAlmostEqual(first_maximum["actual_absolute_residual"] + first_maximum["prediction_shift"], first_maximum["value"], places=8)
        self.assertAlmostEqual(second_maximum["actual_absolute_residual"] + second_maximum["prediction_shift"], second_maximum["value"], places=8)

    def test_analysis_is_post_hoc_and_not_refit(self):
        module = self.load_module()
        summary = module.analyze()
        self.assertTrue(summary["analysis_scope"]["post_hoc"])
        self.assertFalse(summary["analysis_scope"]["refit"])
        self.assertFalse(summary["analysis_scope"]["retuned"])
        self.assertFalse(summary["decision"]["continuous_noncertification_called_unsafe"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["native_physical_model_claimed"])

    def test_mechanism_figure_uses_symmetric_log_for_extreme_scales(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.FIGURE = Path(directory) / "figure.png"
            module.render_figure(module.analyze())
            axis = plt.gcf().axes[0]
            self.assertEqual(axis.get_yscale(), "symlog")
            self.assertEqual(axis.yaxis.get_transform().linthresh, 1.0)
        plt.close("all")

    def test_final_outputs_are_real_and_current(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        summary = module.analyze()
        self.assertEqual(module.validate_summary(summary), [])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

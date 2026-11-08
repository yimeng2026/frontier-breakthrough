import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
COMBINED_SCRIPT = ROOT / "scripts/build_internal_external_bound_comparison_v5.py"


class InternalExternalBoundComparisonV5Tests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(COMBINED_SCRIPT.is_file(), f"Missing v5 builder: {COMBINED_SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_internal_external_bound_comparison_v5", COMBINED_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_ten_dataset_combined_scope_is_not_success_rate(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["ellipsoid_available_point_count"], 901)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 599)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 302)
        self.assertEqual(totals["external_unavailable_point_count"], 254)
        self.assertEqual(totals["internal_unavailable_rooted_fold_count"], 2)
        self.assertEqual(len(summary["datasets"]), 10)
        self.assertEqual(summary["analysis_scope"]["external_total_point_count"], 786)
        self.assertEqual(summary["datasets"][-1]["id"], "roszman1")
        self.assertEqual(summary["datasets"][-1]["ellipsoid_available_point_count"], 5)
        self.assertEqual(summary["datasets"][-1]["prediction_shift_dominant_point_count"], 5)
        self.assertFalse(summary["decision"]["combined_success_rate_claimed"])
        self.assertFalse(summary["analysis_scope"]["chwirut1_independent_model_family_test"])
        self.assertFalse(summary["analysis_scope"]["enso_native_periodic_model_claimed"])
        self.assertFalse(summary["analysis_scope"]["roszman1_native_arctangent_model_claimed"])
        self.assertFalse(summary["analysis_scope"]["roszman1_independent_physical_experiment"])
        self.assertIn("only in fold 2", " ".join(summary["limitations"]))
        self.assertEqual(module.validate_summary(summary), [])

    def test_ten_dataset_figure_title_is_not_stale(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.base.FIGURE = Path(directory) / "figure.png"
            module.base.render_figure(module.analyze())
            self.assertTrue(plt.gcf().axes[1].get_title().startswith("10 distributions"))
        plt.close("all")

    def test_final_v5_combined_outputs_are_real(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

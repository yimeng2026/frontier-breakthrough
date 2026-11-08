import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
EXTERNAL_SCRIPT = ROOT / "scripts/build_external_bound_decomposition_v4.py"
COMBINED_SCRIPT = ROOT / "scripts/build_internal_external_bound_comparison_v4.py"


class BoundDecompositionV4Tests(unittest.TestCase):
    def load_module(self, path, name):
        self.assertTrue(path.is_file(), f"Missing v4 builder: {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_six_external_datasets_include_enso_increment(self):
        module = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v4")
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 761)
        self.assertEqual(totals["ellipsoid_available_point_count"], 527)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 234)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 250)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 277)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual([item["ellipsoid_available_point_count"] for item in summary["datasets"]], [82, 33, 190, 4, 83, 135])
        self.assertEqual(summary["datasets"][-1]["id"], "enso")
        self.assertEqual(summary["datasets"][-1]["prediction_shift_dominant_point_count"], 33)
        self.assertEqual(summary["datasets"][-1]["snapshot_residual_dominant_point_count"], 102)
        self.assertEqual(summary["gauss1_regression"]["mismatch_count"], 0)
        self.assertIn("234 unavailable points", " ".join(summary["limitations"]))
        self.assertNotIn("201 unavailable points", " ".join(summary["limitations"]))
        self.assertFalse(summary["analysis_scope"]["chwirut1_independent_model_family_test"])
        self.assertFalse(summary["analysis_scope"]["enso_native_periodic_model_claimed"])
        self.assertIn("not an independent model-family", " ".join(summary["limitations"]))
        self.assertIn("not the native ENSO", " ".join(summary["limitations"]))
        self.assertEqual(module.validate_summary(summary), [])

    def test_nine_dataset_combined_scope_is_not_success_rate(self):
        module = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v4")
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["ellipsoid_available_point_count"], 896)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 594)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 302)
        self.assertEqual(totals["external_unavailable_point_count"], 234)
        self.assertEqual(totals["internal_unavailable_rooted_fold_count"], 2)
        self.assertEqual(len(summary["datasets"]), 9)
        self.assertEqual(summary["analysis_scope"]["external_total_point_count"], 761)
        self.assertFalse(summary["decision"]["combined_success_rate_claimed"])
        self.assertFalse(summary["analysis_scope"]["chwirut1_independent_model_family_test"])
        self.assertFalse(summary["analysis_scope"]["enso_native_periodic_model_claimed"])
        self.assertIn("not the native ENSO", " ".join(summary["limitations"]))
        self.assertEqual(module.validate_summary(summary), [])

    def test_nine_dataset_figure_title_is_not_stale(self):
        module = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v4")
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.base.FIGURE = Path(directory) / "figure.png"
            module.base.render_figure(module.analyze())
            self.assertTrue(plt.gcf().axes[1].get_title().startswith("9 distributions"))
        plt.close("all")

    def test_final_v4_outputs_are_real(self):
        external = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v4")
        combined = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v4")
        for module in [external, combined]:
            self.assertTrue(module.OUT.is_file(), module.OUT)
            self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
            self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
EXTERNAL_SCRIPT = ROOT / "scripts/build_external_bound_decomposition_v2.py"
COMBINED_SCRIPT = ROOT / "scripts/build_internal_external_bound_comparison_v2.py"


class BoundDecompositionV2Tests(unittest.TestCase):
    def load_module(self, path, name):
        self.assertTrue(path.is_file(), f"Missing v2 builder: {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_four_external_datasets_retain_new_scope(self):
        module = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v2")
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["point_count"], 379)
        self.assertEqual(totals["ellipsoid_available_point_count"], 309)
        self.assertEqual(totals["ellipsoid_unavailable_point_count"], 70)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 142)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 167)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual(summary["gauss1_regression"]["mismatch_count"], 0)
        self.assertEqual([item["ellipsoid_available_point_count"] for item in summary["datasets"]], [82, 33, 190, 4])
        self.assertEqual(module.validate_summary(summary), [])

    def test_seven_dataset_combined_scope_is_not_success_rate(self):
        module = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v2")
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["ellipsoid_available_point_count"], 678)
        self.assertEqual(totals["prediction_shift_dominant_point_count"], 486)
        self.assertEqual(totals["snapshot_residual_dominant_point_count"], 192)
        self.assertEqual(totals["external_unavailable_point_count"], 70)
        self.assertEqual(totals["internal_unavailable_rooted_fold_count"], 2)
        self.assertEqual(len(summary["datasets"]), 7)
        self.assertEqual(summary["analysis_scope"]["external_total_point_count"], 379)
        self.assertFalse(summary["decision"]["combined_success_rate_claimed"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_seven_dataset_figure_title_is_not_stale(self):
        module = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v2")
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.base.FIGURE = Path(directory) / "figure.png"
            module.base.render_figure(module.analyze())
            self.assertTrue(plt.gcf().axes[1].get_title().startswith("7 distributions"))
        plt.close("all")

    def test_final_v2_outputs_are_real(self):
        external = self.load_module(EXTERNAL_SCRIPT, "build_external_bound_decomposition_v2")
        combined = self.load_module(COMBINED_SCRIPT, "build_internal_external_bound_comparison_v2")
        for module in [external, combined]:
            self.assertTrue(module.OUT.is_file(), module.OUT)
            self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
            self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(module.validate_summary(module.analyze()), [])


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_enso_ellipsoid_coverage.py"
ADAPTER = ROOT / "scripts/external_coverage_scoped.py"


class EnsoEllipsoidCoverageTests(unittest.TestCase):
    def load_analysis_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing ENSO analysis wrapper: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_enso_ellipsoid_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_scope_adapter_uses_enso_text_and_preserves_hashes(self):
        module = self.load_analysis_module()
        protocol = module.json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
        summary = {"analysis_scope": {}, "limitations": ["Wrong generic Filip text", "Keep this limitation"]}
        scoped = module.analyze(runner=lambda protocol_path, runner_path: summary)
        self.assertEqual(scoped["limitations"][0], protocol["candidate_rule"]["scope_limitation"])
        self.assertIn("ENSO nine-parameter Fourier", scoped["limitations"][0])
        self.assertNotIn("Filip", scoped["limitations"][0])
        self.assertEqual(scoped["limitations"][1], "Keep this limitation")
        self.assertEqual(scoped["analysis_scope"]["scope_adapter_sha256"], hashlib.sha256(ADAPTER.read_bytes()).hexdigest())
        self.assertEqual(scoped["analysis_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())

    def prepare_fake_main(self, module, directory):
        module.OUT = Path(directory) / "summary.json"
        module.FIGURE = Path(directory) / "figure.png"
        summary = {"status": "fake_without_fitting"}
        def render(received, path):
            self.assertEqual(received, summary)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")
        return summary, lambda: summary, render

    def test_main_writes_real_output_files(self):
        module = self.load_analysis_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            summary, analyze, render = self.prepare_fake_main(module, directory)
            module.main(analyze_func=analyze, render_func=render)
            self.assertEqual(module.json.loads(module.OUT.read_text(encoding="utf-8")), summary)
            self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_main_refuses_to_overwrite_existing_outputs(self):
        module = self.load_analysis_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            summary, analyze, render = self.prepare_fake_main(module, directory)
            module.OUT.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                module.main(analyze_func=analyze, render_func=render)
            self.assertEqual(module.OUT.read_text(encoding="utf-8"), "preserve")
            self.assertFalse(module.FIGURE.exists())

    def test_all_168_points_and_bound_identities_are_audited(self):
        module = self.load_analysis_module()
        summary = module.analyze()
        self.assertEqual(summary["totals"]["point_count"], 168)
        self.assertEqual(summary["totals"]["ellipsoid_available_point_count"], 135)
        self.assertEqual(summary["totals"]["coverage_violation_count"], 0)
        self.assertEqual(summary["totals"]["optimizer_failure_count"], 0)
        self.assertEqual(summary["totals"]["continuous_safe_fold_count"], 4)
        self.assertEqual(summary["totals"]["independent_box_continuous_safe_fold_count"], 3)
        self.assertEqual(summary["totals"]["tighter_point_count"], 131)
        self.assertEqual(summary["totals"]["looser_point_count"], 0)
        self.assertEqual([len(case["point_results"]) for case in summary["folds"]], [34, 34, 34, 33, 33])
        self.assertEqual([sum(point.get("ellipsoid_available", False) for point in case["point_results"]) for case in summary["folds"]], [34, 34, 34, 33, 0])
        self.assertEqual([sum(point.get("box_available", False) for point in case["point_results"]) for case in summary["folds"]], [30, 34, 34, 33, 0])
        self.assertEqual([case["test_metrics"]["rmse"] < case["baseline_test_metrics"]["rmse"] for case in summary["folds"]], [True, True, False, True, True])
        points = [point for case in summary["folds"] for point in case["point_results"]]
        self.assertEqual(sum(point.get("ellipsoid_available") and not point.get("box_available", False) for point in points), 4)
        for case in summary["folds"]:
            squared_errors = [(point["observed_y"] - point["snapshot_prediction"]) ** 2 for point in case["point_results"]]
            self.assertTrue(math.isclose(math.sqrt(sum(squared_errors) / len(squared_errors)), case["test_metrics"]["rmse"], rel_tol=1.0e-12))
            for point in case["point_results"]:
                if point["ellipsoid_available"]:
                    self.assertTrue(math.isclose(point["actual_absolute_residual"] + point["ellipsoid_prediction_shift_upper_bound_float"], point["ellipsoid_absolute_residual_upper_bound_float"], rel_tol=1.0e-8, abs_tol=1.0e-9))
                    self.assertEqual(point["coverage_violation"], 0)
                    if point.get("box_available"):
                        self.assertGreater(point["shift_ratio_ellipsoid_over_box"], 0)
                        self.assertLess(point["shift_ratio_ellipsoid_over_box"], 1)
                else:
                    self.assertIn("not certified", point["ellipsoid_unavailable_reason"])
        self.assertEqual(module.validate_summary(summary), [])

    def test_final_outputs_match_frozen_protocol_wrapper_and_adapter(self):
        module = self.load_analysis_module()
        stored = module.json.loads(module.OUT.read_text(encoding="utf-8"))
        self.assertEqual(module.analyze(), stored)
        self.assertEqual(stored["protocol_sha256"], hashlib.sha256(module.PROTOCOL.read_bytes()).hexdigest())
        self.assertEqual(stored["analysis_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(stored["analysis_scope"]["scope_adapter_sha256"], hashlib.sha256(ADAPTER.read_bytes()).hexdigest())
        protocol = module.json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(stored["data_sha256"], protocol["dataset_scope"]["sha256"])
        self.assertEqual(stored["limitations"][0], protocol["candidate_rule"]["scope_limitation"])
        self.assertNotIn("Filip", " ".join(stored["limitations"]))
        self.assertTrue(stored["analysis_scope"]["dataset_specific_scope_text"])
        self.assertFalse(stored["analysis_scope"]["independent_physical_experiment"])
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

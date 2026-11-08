import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_internal_bound_decomposition.py"


class InternalBoundDecompositionTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing internal decomposition builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_internal_bound_decomposition", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_all_369_identities_and_rooted_scope_pass(self):
        module = self.load_module()
        summary = module.analyze()
        totals = summary["totals"]
        self.assertEqual(totals["ellipsoid_available_point_count"], 369)
        self.assertEqual(totals["unavailable_rooted_fold_count"], 2)
        self.assertEqual(totals["bound_identity_mismatch_count"], 0)
        self.assertEqual(totals["undefined_zero_bound_count"], 0)
        self.assertEqual(totals["prediction_shift_dominant_point_count"] + totals["snapshot_residual_dominant_point_count"], 369)
        self.assertEqual(module.validate_summary(summary), [])

    def test_actual_residual_comes_from_independent_prediction_snapshot(self):
        module = self.load_module()
        comparison = json.loads((ROOT / "validation/rational-ellipsoid-box-comparison.json").read_text(encoding="utf-8"))
        prediction = json.loads((ROOT / "validation/rational-prediction-box-bounds.json").read_text(encoding="utf-8"))
        normalized = module.normalize_case(comparison["cases"][1], prediction["cases"][1])
        point = normalized["point_results"][0]
        self.assertAlmostEqual(point["actual_absolute_residual"], abs(9.959 - 9.98132752799673), places=12)
        self.assertAlmostEqual(point["actual_absolute_residual"] + point["ellipsoid_prediction_shift_upper_bound_float"], point["ellipsoid_absolute_residual_upper_bound_float"], places=10)

    def test_dataset_distributions_and_limits_are_preserved(self):
        module = self.load_module()
        summary = module.analyze()
        self.assertEqual([item["id"] for item in summary["datasets"]], ["hahn1", "thurber", "kirby2"])
        self.assertEqual(sum(item["ellipsoid_available_point_count"] for item in summary["datasets"]), 369)
        self.assertFalse(summary["decision"]["universal_internal_external_ranking_claimed"])
        self.assertFalse(summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(summary["decision"]["rooted_folds_treated_as_zero"])

    def test_final_outputs_are_real_and_current(self):
        module = self.load_module()
        self.assertTrue(module.OUT.is_file(), module.OUT)
        self.assertTrue(module.FIGURE.is_file(), module.FIGURE)
        summary = module.analyze()
        self.assertEqual(summary["protocol_sha256"], module.sha256(module.PROTOCOL))
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(module.validate_summary(summary), [])


if __name__ == "__main__":
    unittest.main()

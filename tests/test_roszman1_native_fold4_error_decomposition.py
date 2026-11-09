import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_roszman1_native_fold4_error_decomposition import (  # noqa: E402
    PROTOCOL,
    analyze,
    render_figure,
    validate_summary,
)


class Roszman1NativeFold4ErrorDecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_all_five_points_and_aggregate_directions_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["point_count"], 5)
        self.assertEqual(totals["native_absolute_winner_count"], 3)
        self.assertEqual(totals["rational_absolute_winner_count"], 2)
        self.assertEqual(totals["absolute_tie_count"], 0)
        aggregate = self.summary["aggregate"]
        self.assertGreater(aggregate["absolute_delta_sum"], 0)
        self.assertLess(aggregate["squared_delta_sum"], 0)
        self.assertGreater(aggregate["native_mae"], aggregate["rational_mae"])
        self.assertLess(aggregate["native_rmse"], aggregate["rational_rmse"])
        self.assertEqual(aggregate["weight_identity_mismatch_count"], 0)
        self.assertEqual(aggregate["frozen_metric_mismatch_count"], 0)
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["leave_one_out_refit"])

    def test_point_identities_and_group_sums_are_exact(self):
        points = self.summary["points"]
        self.assertEqual([point["index"] for point in points], [1, 2, 3, 4, 5])
        for point in points:
            delta = point["native_absolute_residual"] - point["rational_absolute_residual"]
            squared = point["native_absolute_residual"] ** 2 - point["rational_absolute_residual"] ** 2
            weight = point["native_absolute_residual"] + point["rational_absolute_residual"]
            self.assertTrue(math.isclose(point["absolute_delta"], delta, rel_tol=1e-13, abs_tol=1e-15))
            self.assertTrue(math.isclose(point["squared_delta"], squared, rel_tol=1e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(point["weight"], weight, rel_tol=1e-13, abs_tol=1e-15))
            self.assertTrue(math.isclose(point["squared_delta"], delta * weight, rel_tol=1e-12, abs_tol=1e-15))
            self.assertEqual(point["absolute_delta"] < 0, point["squared_delta"] < 0)
            self.assertEqual(point["absolute_delta"] > 0, point["squared_delta"] > 0)
        for group_name in ["native", "rational"]:
            group_points = [point for point in points if point["absolute_winner"] == group_name]
            group = self.summary["groups"][group_name]
            self.assertEqual(group["point_indices"], [point["index"] for point in group_points])
            self.assertTrue(math.isclose(group["absolute_delta_sum"], sum(point["absolute_delta"] for point in group_points), rel_tol=1e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(group["squared_delta_sum"], sum(point["squared_delta"] for point in group_points), rel_tol=1e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(group["weight_sum"], sum(point["weight"] for point in group_points), rel_tol=1e-12, abs_tol=1e-15))

    def test_leave_one_out_is_metric_arithmetic_not_refitting(self):
        aggregate = self.summary["aggregate"]
        records = self.summary["leave_one_out"]
        self.assertEqual(len(records), 5)
        for record in records:
            point = self.summary["points"][record["point_index"] - 1]
            remaining_absolute = aggregate["absolute_delta_sum"] - point["absolute_delta"]
            remaining_squared = aggregate["squared_delta_sum"] - point["squared_delta"]
            self.assertTrue(math.isclose(record["remaining_absolute_delta_sum"], remaining_absolute, rel_tol=1e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(record["remaining_squared_delta_sum"], remaining_squared, rel_tol=1e-12, abs_tol=1e-15))
            expected_mae = "native" if remaining_absolute < 0 else "rational" if remaining_absolute > 0 else "tie"
            expected_rmse = "native" if remaining_squared < 0 else "rational" if remaining_squared > 0 else "tie"
            self.assertEqual(record["remaining_mae_direction"], expected_mae)
            self.assertEqual(record["remaining_rmse_direction"], expected_rmse)
            self.assertEqual(record["reverses_rational_mae"], remaining_absolute <= 0)
            self.assertEqual(record["reverses_native_rmse"], remaining_squared >= 0)
        self.assertFalse(self.summary["decision"]["leave_one_out_refitting_performed"])

    def test_validator_rejects_aggregate_leave_one_out_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["aggregate"]["absolute_delta_sum"] = -1
        self.assertTrue(any("aggregate" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["leave_one_out"][0]["remaining_squared_delta_sum"] = 0
        self.assertTrue(any("leave-one-out" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["statistical_significance_claimed"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))

    def test_input_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed = copy.deepcopy(self.protocol)
            changed["inputs"]["native_holdout"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                analyze(path)

    def test_figure_is_real_png(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            render_figure(self.summary, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(output.stat().st_size, 40000)


if __name__ == "__main__":
    unittest.main()

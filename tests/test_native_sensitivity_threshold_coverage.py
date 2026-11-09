import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_native_sensitivity_threshold_coverage import (  # noqa: E402
    PROTOCOL,
    analyze,
    evaluate_point,
    render_figure,
    validate_summary,
)

THRESHOLDS = [1, 2, 4]


class NativeSensitivityThresholdCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_zero_deviation_rule_and_nested_thresholds(self):
        zero_covered = evaluate_point(0, 0, THRESHOLDS)
        self.assertEqual(zero_covered["covered_by_threshold"], {"1": True, "2": True, "4": True})
        self.assertEqual(zero_covered["failed_thresholds"], [])
        self.assertIsNone(zero_covered["residual_to_sensitivity_ratio"])
        zero_violation = evaluate_point(0.5, 0, THRESHOLDS)
        self.assertEqual(zero_violation["covered_by_threshold"], {"1": False, "2": False, "4": False})
        self.assertEqual(zero_violation["failed_thresholds"], [1, 2, 4])
        normal = evaluate_point(2.5, 1, THRESHOLDS)
        self.assertEqual(normal["covered_by_threshold"], {"1": False, "2": False, "4": True})
        self.assertEqual(normal["failed_thresholds"], [1, 2])
        self.assertEqual(normal["residual_to_sensitivity_ratio"], 2.5)

    def test_all_points_evaluations_and_nested_counts_are_present(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["point_count"], 407)
        self.assertEqual(totals["evaluation_count"], 1221)
        self.assertEqual(totals["missing_residual_count"], 0)
        self.assertEqual(totals["missing_standard_deviation_count"], 0)
        self.assertEqual([dataset["id"] for dataset in self.summary["datasets"]], ["roszman1", "chwirut1", "enso"])
        for dataset in self.summary["datasets"]:
            previous_covered = -1
            for threshold in THRESHOLDS:
                record = dataset["thresholds"][str(threshold)]
                self.assertEqual(record["covered_count"] + record["violation_count"], dataset["held_out_point_count"])
                self.assertGreaterEqual(record["covered_count"], previous_covered)
                previous_covered = record["covered_count"]
            for fold in dataset["folds"]:
                previous_covered = -1
                for threshold in THRESHOLDS:
                    record = fold["thresholds"][str(threshold)]
                    self.assertEqual(record["covered_count"] + record["violation_count"], fold["test_count"])
                    self.assertGreaterEqual(record["covered_count"], previous_covered)
                    previous_covered = record["covered_count"]
        previous_covered = -1
        for threshold in THRESHOLDS:
            record = totals["thresholds"][str(threshold)]
            self.assertEqual(record["covered_count"] + record["violation_count"], 407)
            self.assertGreaterEqual(record["covered_count"], previous_covered)
            previous_covered = record["covered_count"]

    def test_point_ratios_and_violation_details_are_exact(self):
        expected_violations = {str(threshold): [] for threshold in THRESHOLDS}
        for dataset in self.summary["datasets"]:
            for fold in dataset["folds"]:
                ratios = []
                for point in fold["points"]:
                    self.assertGreaterEqual(point["absolute_residual"], 0)
                    self.assertGreaterEqual(point["local_standard_deviation"], 0)
                    if point["local_standard_deviation"] > 0:
                        expected_ratio = point["absolute_residual"] / point["local_standard_deviation"]
                        self.assertTrue(math.isclose(point["residual_to_sensitivity_ratio"], expected_ratio, rel_tol=1e-12, abs_tol=1e-12))
                        ratios.append(expected_ratio)
                    else:
                        self.assertIsNone(point["residual_to_sensitivity_ratio"])
                    for threshold in THRESHOLDS:
                        expected_covered = point["absolute_residual"] <= threshold * point["local_standard_deviation"]
                        self.assertEqual(point["covered_by_threshold"][str(threshold)], expected_covered)
                        if not expected_covered:
                            expected_violations[str(threshold)].append(f"{dataset['id']}:{fold['fold']}:{point['point_index']}")
                if ratios:
                    self.assertTrue(math.isclose(fold["max_residual_to_sensitivity_ratio"], max(ratios), rel_tol=1e-12, abs_tol=1e-12))
        self.assertEqual(self.summary["totals"]["violation_point_ids_by_threshold"], expected_violations)
        for threshold in THRESHOLDS:
            self.assertEqual(len(expected_violations[str(threshold)]), self.summary["totals"]["thresholds"][str(threshold)]["violation_count"])

    def test_no_probability_or_optimized_threshold_claim(self):
        for key in ["probability_coverage_claimed", "confidence_interval_claimed", "threshold_optimized", "violations_hidden", "native_deterministic_bounds_claimed", "global_identifiability_claimed", "independent_experiment_claimed", "cross_model_probability_score_claimed"]:
            self.assertFalse(self.summary["decision"][key], key)
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["covariance_recomputed"])

    def test_validator_rejects_count_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["totals"]["thresholds"]["1"]["covered_count"] += 1
        self.assertTrue(any("count" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["probability_coverage_claimed"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))

    def test_input_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed = copy.deepcopy(self.protocol)
            changed["inputs"]["enso"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                analyze(path)

    def test_figure_is_real_png(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            render_figure(self.summary, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(output.stat().st_size, 50000)


if __name__ == "__main__":
    unittest.main()

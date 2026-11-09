import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_native_identifiability_cross_model import (  # noqa: E402
    PROTOCOL,
    analyze,
    render_figure,
    validate_summary,
)


class NativeIdentifiabilityCrossModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_structure_and_all_frozen_folds_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["held_out_point_count"], 407)
        self.assertEqual(totals["full_numerical_rank_fold_count"], 15)
        self.assertEqual(totals["local_diagnostic_failure_count"], 0)
        self.assertEqual([item["id"] for item in self.summary["datasets"]], ["roszman1", "chwirut1", "enso"])
        self.assertEqual([item["parameter_count"] for item in self.summary["datasets"]], [4, 3, 9])
        self.assertEqual([item["held_out_point_count"] for item in self.summary["datasets"]], [25, 214, 168])
        self.assertTrue(all(len(item["folds"]) == 5 for item in self.summary["datasets"]))
        self.assertIsNone(self.summary["cross_model_pooled_error_metrics"])
        self.assertIsNone(self.summary["cross_model_stability_score"])
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["covariance_recomputed"])

    def test_sensitivity_error_ratios_and_counterexamples_are_recomputed(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["sensitivity_exceeds_rmse_fold_ids"], ["roszman1:1", "roszman1:5", "chwirut1:1"])
        self.assertEqual(totals["sensitivity_equals_rmse_fold_ids"], [])
        for dataset in self.summary["datasets"]:
            for fold in dataset["folds"]:
                expected = fold["max_local_prediction_standard_deviation"] / fold["native_test_rmse"]
                self.assertTrue(math.isclose(fold["sensitivity_to_rmse_ratio"], expected, rel_tol=1e-12, abs_tol=1e-12))
                self.assertEqual(fold["sensitivity_exceeds_rmse"], expected > 1)
        roszman = self.summary["datasets"][0]
        chwirut = self.summary["datasets"][1]
        enso = self.summary["datasets"][2]
        self.assertAlmostEqual(roszman["summary"]["max_scaled_condition_number"], 90.74335888809009)
        self.assertAlmostEqual(chwirut["summary"]["max_scaled_condition_number"], 28.674083116404475)
        self.assertAlmostEqual(enso["summary"]["max_scaled_condition_number"], 6.896240781966828)
        self.assertGreater(roszman["folds"][4]["sensitivity_to_rmse_ratio"], 2.6)
        self.assertGreater(chwirut["folds"][0]["sensitivity_to_rmse_ratio"], 1)
        self.assertTrue(all(fold["sensitivity_to_rmse_ratio"] < 1 for fold in enso["folds"]))

    def test_scope_specific_parameters_and_known_answer_layers_are_preserved(self):
        roszman = self.summary["datasets"][0]
        chwirut = self.summary["datasets"][1]
        enso = self.summary["datasets"][2]
        self.assertAlmostEqual(roszman["parameter_stability"]["b2"]["range"], 1.0411858782379334e-05)
        self.assertAlmostEqual(roszman["parameter_stability"]["b4"]["range"], 112.23614139349083)
        self.assertAlmostEqual(chwirut["parameter_stability"]["b2"]["range"], 0.005195445174092934)
        self.assertAlmostEqual(chwirut["scope_specific"]["fold1_b2_absolute_relative_standard_error"], 1.7106283204180401)
        self.assertAlmostEqual(chwirut["scope_specific"]["minimum_absolute_denominator"], 0.009384279096904605)
        self.assertEqual(chwirut["scope_specific"]["pole_inside_observed_range_fold_count"], 0)
        self.assertAlmostEqual(enso["parameter_stability"]["b4"]["range"], 3.1263085397655743)
        self.assertAlmostEqual(enso["parameter_stability"]["b7"]["range"], 1.9460668828939873)
        self.assertAlmostEqual(enso["scope_specific"]["fold4_b4_absolute_relative_standard_error"], 0.037359660053584605)
        self.assertAlmostEqual(enso["scope_specific"]["fold4_b7_absolute_relative_standard_error"], 0.025260794231141546)
        self.assertAlmostEqual(enso["scope_specific"]["max_cross_harmonic_block_absolute_correlation"], 0.5591238742033899)
        self.assertFalse(enso["known_answer"]["optimizer_within_certified_tolerances"])
        self.assertTrue(enso["known_answer"]["certified_forward_rss_check_passed"])
        self.assertFalse(enso["known_answer"]["used_as_holdout"])

    def test_no_universal_stability_or_global_identifiability_claim(self):
        for key in ["universal_stability_score_claimed", "condition_number_quality_ranking_claimed", "global_identifiability_claimed", "calibrated_coverage_claimed", "cross_model_pooled_metric_claimed", "new_physical_periods_claimed", "independent_experiment_claimed", "rational_bounds_transferred_to_native"]:
            self.assertFalse(self.summary["decision"][key], key)

    def test_validator_rejects_ratio_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["datasets"][0]["folds"][0]["sensitivity_to_rmse_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["universal_stability_score_claimed"] = True
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

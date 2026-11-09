import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_native_cross_dataset_synthesis import (  # noqa: E402
    PROTOCOL,
    analyze,
    render_figure,
    validate_summary,
)


class NativeCrossDatasetSynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_frozen_structure_and_all_points_are_retained(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["point_count"], 407)
        self.assertEqual(totals["native_optimizer_failure_count"], 0)
        self.assertEqual(totals["missing_point_prediction_count"], 0)
        self.assertEqual([item["id"] for item in self.summary["datasets"]], ["roszman1", "enso", "chwirut1"])
        self.assertEqual([item["totals"]["point_count"] for item in self.summary["datasets"]], [25, 168, 214])
        self.assertTrue(all(len(item["folds"]) == 5 for item in self.summary["datasets"]))
        self.assertIsNone(self.summary["cross_dataset_pooled_error_metrics"])
        self.assertFalse(self.summary["analysis_scope"]["refit"])
        self.assertFalse(self.summary["analysis_scope"]["cross_dataset_error_pooling"])

    def test_fold_winners_and_every_counterexample_are_preserved(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["native_better_than_rational_fold_count"], 11)
        self.assertEqual(totals["rational_better_than_native_fold_count"], 4)
        self.assertEqual(totals["native_better_than_cubic_fold_count"], 13)
        self.assertEqual(totals["cubic_better_than_native_fold_count"], 2)
        self.assertEqual(totals["overall_best_model_fold_counts"], {"native": 10, "rational": 3, "cubic": 2, "tie": 0})
        self.assertEqual(totals["native_rational_sweep_dataset_count"], 0)
        self.assertEqual(totals["native_cubic_sweep_dataset_count"], 2)
        self.assertEqual(totals["native_overall_sweep_dataset_count"], 0)
        self.assertEqual(
            totals["rational_beats_native_fold_ids"],
            ["roszman1:1", "roszman1:2", "enso:1", "chwirut1:2"],
        )
        self.assertEqual(totals["cubic_beats_native_fold_ids"], ["roszman1:2", "roszman1:3"])
        roszman = self.summary["datasets"][0]
        self.assertGreater(roszman["folds"][0]["native_to_rational_rmse_ratio"], 10)
        self.assertLess(roszman["folds"][4]["native_to_rational_rmse_ratio"], 0.02)
        self.assertEqual(roszman["folds"][1]["overall_winner"], "cubic")
        self.assertEqual(roszman["folds"][2]["overall_winner"], "cubic")

    def test_point_and_fold_diagnostics_are_independently_recomputed(self):
        expected_point_counts = {}
        expected_metric_disagreements = []
        expected_point_fold_disagreements = []
        for dataset_id, info in self.protocol["inputs"].items():
            source = json.loads((ROOT / info["file"]).read_text(encoding="utf-8"))
            native = rational = tie = 0
            for fold in source["folds"]:
                for point in fold["point_results"]:
                    left = point["native_absolute_residual"]
                    right = point["rational_absolute_residual"]
                    native += left < right
                    rational += right < left
                    tie += left == right
                directions = {}
                for metric in ["rmse", "mae", "max_absolute_residual"]:
                    left = fold["native_test_metrics"][metric]
                    right = fold["rational_candidate_test_metrics"][metric]
                    directions[metric] = "native" if left < right else "rational" if right < left else "tie"
                if directions["rmse"] != directions["mae"] or directions["rmse"] != directions["max_absolute_residual"]:
                    expected_metric_disagreements.append(f"{dataset_id}:{fold['fold']}")
                point_native = sum(p["native_absolute_residual"] < p["rational_absolute_residual"] for p in fold["point_results"])
                point_rational = sum(p["rational_absolute_residual"] < p["native_absolute_residual"] for p in fold["point_results"])
                majority = "native" if point_native > point_rational else "rational" if point_rational > point_native else "tie"
                if majority != "tie" and majority != directions["rmse"]:
                    expected_point_fold_disagreements.append(f"{dataset_id}:{fold['fold']}")
            expected_point_counts[dataset_id] = {"native": native, "rational": rational, "tie": tie}
        for dataset in self.summary["datasets"]:
            self.assertEqual(dataset["point_outcomes"], expected_point_counts[dataset["id"]])
        self.assertEqual(self.summary["totals"]["metric_direction_disagreement_fold_ids"], expected_metric_disagreements)
        self.assertEqual(self.summary["totals"]["point_fold_disagreement_fold_ids"], expected_point_fold_disagreements)
        self.assertEqual(self.summary["totals"]["pooled_metric_mismatch_count"], 0)
        self.assertEqual(sum(self.summary["totals"]["point_outcomes"].values()), 407)

    def test_known_answer_and_proof_boundaries_remain_separate(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["optimizer_known_answer_pass_dataset_ids"], ["roszman1", "chwirut1"])
        self.assertEqual(totals["optimizer_miss_but_certified_forward_pass_dataset_ids"], ["enso"])
        self.assertFalse(self.summary["decision"]["native_deterministic_bounds_claimed"])
        self.assertFalse(self.summary["decision"]["rational_bounds_transferred_to_native"])
        self.assertFalse(self.summary["decision"]["probability_calibration_claimed"])
        self.assertFalse(self.summary["decision"]["independent_experiment_claimed"])
        self.assertFalse(self.summary["decision"]["universal_model_ranking_claimed"])
        self.assertFalse(self.summary["decision"]["cross_dataset_pooled_metric_claimed"])

    def test_validator_rejects_changed_counts_ratio_and_overclaim(self):
        changed = copy.deepcopy(self.summary)
        changed["totals"]["native_better_than_rational_fold_count"] = 15
        self.assertTrue(any("fold" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["datasets"][0]["folds"][0]["native_to_rational_rmse_ratio"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["universal_model_ranking_claimed"] = True
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

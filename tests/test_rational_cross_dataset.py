import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_rational_cross_dataset import analyze, validate_summary


class RationalCrossDatasetTests(unittest.TestCase):
    def test_synthesis_retains_all_folds_and_evidence_levels(self):
        summary = analyze()
        self.assertEqual(validate_summary(summary), [])
        self.assertEqual(len(summary["datasets"]), 3)
        self.assertEqual(summary["totals"]["fold_count"], 15)
        self.assertEqual(summary["totals"]["gate_consistent_fold_count"], 13)
        self.assertEqual(summary["totals"]["dataset_all_folds_count"], 1)
        self.assertEqual(summary["totals"]["domain_failed_fold_count"], 2)
        hahn = next(item for item in summary["datasets"] if item["id"] == "hahn1")
        thurber = next(item for item in summary["datasets"] if item["id"] == "thurber")
        kirby = next(item for item in summary["datasets"] if item["id"] == "kirby2")
        self.assertTrue(all(fold["assessment_type"] == "post_hoc_gate_reconstruction" for fold in hahn["folds"]))
        self.assertTrue(all(fold["assessment_type"] == "frozen_dataset_prospective_gate" for fold in thurber["folds"] + kirby["folds"]))
        self.assertEqual(hahn["folds"][0]["root_count_in_held_out_interval"], 2)
        self.assertEqual(thurber["folds"][0]["root_count_in_held_out_interval"], 1)
        self.assertFalse(hahn["overall_all_folds_gate_consistent"])
        self.assertFalse(thurber["overall_all_folds_gate_consistent"])
        self.assertTrue(kirby["overall_all_folds_gate_consistent"])

    def test_fold_gate_is_recomputed_from_three_separate_axes(self):
        summary = analyze()
        for dataset in summary["datasets"]:
            for fold in dataset["folds"]:
                expected = fold["domain_admissible"] and fold["minimal_numerical_identifiability"] and fold["baseline_not_worse"]
                self.assertEqual(fold["gate_consistent"], expected)
        self.assertFalse(summary["decision"]["universal_detection_accuracy_claimed"])


if __name__ == "__main__":
    unittest.main()

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_native_ellipsoid_cross_model import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    render_figure,
    validate_summary,
)


class NativeEllipsoidCrossModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_structure_counts_and_receipts_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["fold_count"], 15)
        self.assertEqual(totals["held_out_point_count"], 407)
        self.assertEqual(totals["certified_fold_count"], 14)
        self.assertEqual(totals["available_point_count"], 402)
        self.assertEqual(totals["covered_point_count"], 402)
        self.assertEqual(totals["violation_point_count"], 0)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unique_envelope_count"], 210)
        self.assertEqual(totals["center_prediction_envelope_mismatch_count"], 0)
        self.assertEqual(totals["source_receipt_verified_count"], 3)
        self.assertEqual(totals["source_projection_mismatch_count"], 0)
        self.assertEqual(totals["unavailable_fold_ids"], ["roszman1:5"])
        self.assertEqual([item["id"] for item in self.summary["datasets"]], ["chwirut1", "roszman1", "enso"])
        self.assertTrue(all(item["source_receipt_verified"] for item in self.summary["datasets"]))
        self.assertTrue(all(item["recomputed_source_mismatch_count"] == 0 for item in self.summary["datasets"]))

    def test_raw_metrics_remain_in_model_specific_units(self):
        expected = {
            "chwirut1": (214, 22, 170.14630922307612, 19.222110234669167, 165.679601537622, 15.050994997990879),
            "roszman1": (20, 20, 0.867292251653464, 0.3543650116278472, 0.4433913282171526, 0.1853990741468824),
            "enso": (168, 168, 17.64192935677042, 13.164436414771593, 14.576765863967406, 8.516811559710845),
        }
        for dataset in self.summary["datasets"]:
            available, envelopes, max_width, median_width, max_residual, median_residual = expected[dataset["id"]]
            totals = dataset["totals"]
            self.assertEqual(totals["available_point_count"], available)
            self.assertEqual(totals["unique_envelope_count"], envelopes)
            self.assertAlmostEqual(totals["max_envelope_width"], max_width)
            self.assertAlmostEqual(totals["median_envelope_width"], median_width)
            self.assertAlmostEqual(totals["max_residual_upper_bound"], max_residual)
            self.assertAlmostEqual(totals["median_residual_upper_bound"], median_residual)

    def test_unavailable_fold_and_all_point_accounting_are_preserved(self):
        roszman = self.summary["datasets"][1]
        fold5 = roszman["folds"][4]
        self.assertFalse(fold5["prediction_envelope_available"])
        self.assertEqual(fold5["coverage"]["available_point_count"], 0)
        self.assertEqual(fold5["coverage"]["unavailable_point_count"], 5)
        self.assertEqual(fold5["envelope_count"], 0)
        self.assertIsNone(fold5["max_envelope_width"])
        self.assertIsNone(fold5["normalization"]["max_width_to_dataset_median"])
        self.assertIsNone(fold5["normalization"]["max_residual_to_dataset_median"])
        for dataset in self.summary["datasets"]:
            for fold in dataset["folds"]:
                coverage = fold["coverage"]
                self.assertEqual(coverage["available_point_count"] + coverage["unavailable_point_count"], fold["point_count"])
                self.assertEqual(coverage["covered_point_count"] + coverage["violation_point_count"], coverage["available_point_count"])
                self.assertEqual(coverage["center_prediction_envelope_mismatch_count"], 0)

    def test_ratios_use_only_the_same_dataset_median(self):
        for dataset in self.summary["datasets"]:
            width_median = dataset["totals"]["median_envelope_width"]
            residual_median = dataset["totals"]["median_residual_upper_bound"]
            self.assertGreater(width_median, 0)
            self.assertGreater(residual_median, 0)
            for fold in dataset["folds"]:
                if not fold["prediction_envelope_available"]:
                    continue
                expected_width = fold["max_envelope_width"] / width_median
                expected_residual = fold["max_residual_upper_bound"] / residual_median
                self.assertTrue(math.isclose(fold["normalization"]["max_width_to_dataset_median"], expected_width, rel_tol=1e-12, abs_tol=1e-12))
                self.assertTrue(math.isclose(fold["normalization"]["max_residual_to_dataset_median"], expected_residual, rel_tol=1e-12, abs_tol=1e-12))
        chwirut = self.summary["datasets"][0]
        enso = self.summary["datasets"][2]
        self.assertNotEqual(chwirut["folds"][0]["normalization"]["max_width_to_dataset_median"], chwirut["folds"][0]["max_envelope_width"] / enso["totals"]["median_envelope_width"])

    def test_no_pooled_metric_probability_or_universal_winner(self):
        for key in ["cross_dataset_pooled_error_metrics", "cross_dataset_pooled_envelope_widths", "cross_dataset_pooled_residual_upper_bounds", "cross_dataset_stability_score", "universal_model_winner", "probability_coverage"]:
            self.assertIsNone(self.summary[key], key)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertTrue(self.summary["analysis_scope"]["within_dataset_normalization_only"])

    def test_known_answer_and_related_study_layers_are_separate(self):
        chwirut = self.summary["datasets"][0]
        enso = self.summary["datasets"][2]
        self.assertEqual(chwirut["scope_specific"]["related_prior_dataset"], "Chwirut2")
        self.assertFalse(chwirut["scope_specific"]["independent_model_family_test"])
        self.assertFalse(enso["known_answer"]["optimizer_within_certified_tolerances"])
        self.assertTrue(enso["known_answer"]["certified_forward_rss_check_passed"])
        self.assertFalse(enso["known_answer"]["used_as_holdout"])

    def test_validator_rejects_ratio_unavailable_and_scope_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["datasets"][0]["folds"][0]["normalization"]["max_width_to_dataset_median"] = 1
        self.assertTrue(any("ratio" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["totals"]["unavailable_point_count"] = 0
        self.assertTrue(any("unavailable" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["universal_stability_score_claimed"] = True
        self.assertTrue(any("overclaim" in error.lower() for error in validate_summary(changed)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "protocol.json"
            changed_protocol = copy.deepcopy(self.protocol)
            changed_protocol["inputs"]["enso_bounds"]["sha256"] = "0" * 64
            path.write_text(json.dumps(changed_protocol), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                analyze(path)

    def test_stored_output_and_figure_are_real(self):
        stored = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(self.summary, stored)
        self.assertTrue(FIGURE.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figure.png"
            render_figure(self.summary, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(output.stat().st_size, 50000)


if __name__ == "__main__":
    unittest.main()

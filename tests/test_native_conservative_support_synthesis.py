import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_native_conservative_support_synthesis import (  # noqa: E402
    FIGURE,
    OUT,
    PROTOCOL,
    analyze,
    render_figure,
    validate_summary,
)


class NativeConservativeSupportSynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.summary = analyze()

    def test_structure_counts_and_receipts_are_complete(self):
        totals = self.summary["totals"]
        self.assertEqual(totals["dataset_count"], 3)
        self.assertEqual(totals["held_out_point_count"], 407)
        self.assertEqual(totals["available_point_count"], 402)
        self.assertEqual(totals["unavailable_point_count"], 5)
        self.assertEqual(totals["unavailable_fold_ids"], ["roszman1:5"])
        self.assertEqual(totals["unique_envelope_count"], 210)
        self.assertEqual(totals["tightened_envelope_count"], 79)
        self.assertEqual(totals["unchanged_envelope_count"], 131)
        self.assertEqual(totals["nonempty_intersection_count"], 210)
        self.assertEqual(totals["candidate_evaluation_count"], 964)
        self.assertEqual(totals["candidate_violation_count"], 0)
        self.assertEqual(totals["center_prediction_mismatch_count"], 0)
        self.assertEqual(totals["source_receipt_verified_count"], 3)
        self.assertEqual(totals["source_projection_mismatch_count"], 0)
        self.assertEqual([item["id"] for item in self.summary["datasets"]], ["chwirut1", "roszman1", "enso"])
        self.assertTrue(all(item["source_receipt_verified"] for item in self.summary["datasets"]))

    def test_model_specific_results_and_largest_cases_are_preserved(self):
        chwirut = self.summary["datasets"][0]
        roszman = self.summary["datasets"][1]
        enso = self.summary["datasets"][2]
        self.assertEqual(chwirut["totals"]["tightened_envelope_count"], 22)
        self.assertEqual(roszman["totals"]["tightened_envelope_count"], 20)
        self.assertEqual(enso["totals"]["tightened_envelope_count"], 37)
        self.assertAlmostEqual(chwirut["ratio_summary"]["median"], 0.25654045819729265)
        self.assertAlmostEqual(roszman["ratio_summary"]["median"], 0.690796188558053)
        self.assertEqual(enso["ratio_summary"]["median"], 1.0)
        self.assertEqual(chwirut["largest_tightening"]["x"], 1.5)
        self.assertAlmostEqual(chwirut["largest_tightening"]["intersection_width_reduction"], 20.935447900396312)
        self.assertEqual(roszman["largest_tightening"]["x"], -4868.68)
        self.assertAlmostEqual(roszman["largest_tightening"]["intersection_width_reduction"], 0.7008593776977347)
        self.assertEqual(enso["largest_tightening"]["x"], 25.0)
        self.assertAlmostEqual(enso["largest_tightening"]["triple_width_reduction"], 4.371401855122352)

    def test_unavailable_fold_and_candidate_inventory_are_not_rewritten(self):
        roszman = self.summary["datasets"][1]
        self.assertEqual(roszman["totals"]["unavailable_point_count"], 5)
        self.assertEqual(roszman["totals"]["unavailable_fold_ids"], [5])
        self.assertEqual(roszman["totals"]["candidate_evaluation_count"], 160)
        self.assertEqual(roszman["folds"][4]["prediction_envelope_available"], False)
        self.assertEqual(roszman["folds"][4]["candidate_evaluation_count"], 0)
        self.assertEqual(len(roszman["folds"][4]["points"]), 5)
        self.assertEqual(self.summary["datasets"][0]["totals"]["candidate_evaluation_count"], 132)
        self.assertEqual(self.summary["datasets"][2]["totals"]["candidate_evaluation_count"], 672)

    def test_no_cross_dataset_metric_or_global_optimum_is_present(self):
        for key in ["cross_dataset_pooled_error_metrics", "cross_dataset_raw_widths", "unified_stability_score", "probability_coverage", "global_optimum"]:
            self.assertIsNone(self.summary[key], key)
        for key, value in self.summary["decision"].items():
            self.assertFalse(value, key)
        self.assertTrue(self.summary["analysis_scope"]["model_specific_baselines_only"])
        self.assertFalse(self.summary["analysis_scope"]["cross_dataset_raw_width_pooling"])

    def test_validator_rejects_count_scope_and_hash_changes(self):
        changed = copy.deepcopy(self.summary)
        changed["totals"]["tightened_envelope_count"] = 0
        self.assertTrue(any("count" in error.lower() for error in validate_summary(changed)))
        changed = copy.deepcopy(self.summary)
        changed["decision"]["global_optimum_claimed"] = True
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

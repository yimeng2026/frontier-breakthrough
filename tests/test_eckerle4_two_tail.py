import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_eckerle4_two_tail import analyze, eckerle_model, load_eckerle_data, split_two_tail


class Eckerle4TwoTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT / "validation/eckerle4-two-tail-protocol.json").read_text(encoding="utf-8"))
        cls.x, cls.y = load_eckerle_data(ROOT / "data/Eckerle4.dat", cls.protocol["data"]["sha256"])

    def test_raw_data_and_two_tail_split_match_protocol(self):
        self.assertEqual(len(self.x), 35)
        low, middle, high = split_two_tail(self.x)
        self.assertEqual((low.sum(), middle.sum(), high.sum()), (3, 27, 5))
        self.assertTrue(np.all(self.x[low] <= 410))
        self.assertTrue(np.all((self.x[middle] > 410) & (self.x[middle] < 480)))
        self.assertTrue(np.all(self.x[high] >= 480))

    def test_model_is_gaussian_with_center_amplitude_b1_over_b2(self):
        self.assertAlmostEqual(eckerle_model(450, 2, 4, 450), 0.5)
        self.assertAlmostEqual(eckerle_model(450, 2, 4, 451), 0.5 * np.exp(-0.5 * (1 / 4) ** 2))

    def test_full_fit_reproduces_nist_certification(self):
        summary = analyze(ROOT / "data/Eckerle4.dat", ROOT / "validation/eckerle4-two-tail-protocol.json")
        certified = self.protocol["full_fit_certification_rule"]["certified_parameters"]
        for name in ("b1", "b2", "b3"):
            self.assertAlmostEqual(summary["full_fit_certification"]["parameters"][name] / certified[name], 1.0, places=4)
        self.assertAlmostEqual(
            summary["full_fit_certification"]["residual_standard_deviation"],
            self.protocol["full_fit_certification_rule"]["certified_residual_standard_deviation"],
            places=5,
        )

    def test_two_tail_gate_and_predictions_are_consistent(self):
        summary = analyze(ROOT / "data/Eckerle4.dat", ROOT / "validation/eckerle4-two-tail-protocol.json")
        metrics = summary["middle_fit"]["metrics"]
        linear = summary["baselines"]["linear"]
        expected = (
            metrics["holdout_rmse"] < 3 * metrics["middle_rmse"]
            and metrics["holdout_rmse"] < linear["holdout_rmse"]
            and metrics["low_rmse"] < linear["low_rmse"]
            and metrics["high_rmse"] < linear["high_rmse"]
        )
        self.assertEqual(summary["decision"]["limited_support"], expected)
        self.assertFalse(summary["decision"]["universal_law_claimed"])
        self.assertEqual(len(summary["predictions"]), 35)

    def test_independent_prediction_audit_passes(self):
        from verify_eckerle4_two_tail import verify_summary
        result = verify_summary(ROOT / "validation/eckerle4-two-tail.json")
        self.assertEqual(result["verification"], "passed")
        self.assertEqual(result["prediction_count"], 35)
        self.assertEqual(result["maximum_metric_absolute_error"], 0)


if __name__ == "__main__":
    unittest.main()

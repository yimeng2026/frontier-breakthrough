import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_chwirut_holdout import (
    analyze,
    chwirut_model,
    fit_linear,
    load_chwirut_data,
    split_holdout,
)


class ChwirutHoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT / "validation/chwirut-holdout-protocol.json").read_text(encoding="utf-8"))
        cls.x, cls.y = load_chwirut_data(ROOT / "data/Chwirut2.dat", cls.protocol["data"]["sha256"])

    def test_raw_data_and_grouped_split_match_frozen_protocol(self):
        self.assertEqual(len(self.x), 54)
        self.assertEqual(len(set(self.x)), 22)
        train, holdout = split_holdout(self.x, 5.0)
        self.assertEqual(train.sum(), 47)
        self.assertEqual(holdout.sum(), 7)
        self.assertFalse(set(self.x[train]) & set(self.x[holdout]))
        self.assertTrue(np.all(self.x[train] < 5.0))
        self.assertTrue(np.all(self.x[holdout] >= 5.0))

    def test_model_uses_the_nist_equation(self):
        self.assertEqual(chwirut_model(0, 0.2, 0.5, 0.1), 2.0)
        expected = np.exp(-0.2 * 3.0) / (0.5 + 0.1 * 3.0)
        self.assertAlmostEqual(chwirut_model(3.0, 0.2, 0.5, 0.1), expected)

    def test_linear_baseline_is_exact_on_a_line(self):
        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = 2.0 + 4.0 * x
        slope, intercept = fit_linear(x, y)
        self.assertAlmostEqual(slope, 4.0)
        self.assertAlmostEqual(intercept, 2.0)

    def test_full_fit_reproduces_nist_certified_values(self):
        summary = analyze(ROOT / "data/Chwirut2.dat", ROOT / "validation/chwirut-holdout-protocol.json")
        certified = self.protocol["full_fit_certification_rule"]["certified_parameters"]
        for name in ("b1", "b2", "b3"):
            actual = summary["full_fit_certification"]["parameters"][name]
            self.assertAlmostEqual(actual / certified[name], 1.0, places=4)
        self.assertAlmostEqual(
            summary["full_fit_certification"]["residual_standard_deviation"],
            self.protocol["full_fit_certification_rule"]["certified_residual_standard_deviation"],
            places=4,
        )

    def test_holdout_gate_is_recomputed_from_predictions(self):
        summary = analyze(ROOT / "data/Chwirut2.dat", ROOT / "validation/chwirut-holdout-protocol.json")
        train_rmse = summary["train_fit"]["metrics"]["train_rmse"]
        holdout_rmse = summary["train_fit"]["metrics"]["holdout_rmse"]
        linear_rmse = summary["baselines"]["linear"]["holdout_rmse"]
        expected = holdout_rmse < 3 * train_rmse and holdout_rmse < linear_rmse
        self.assertEqual(summary["decision"]["limited_support"], expected)
        self.assertFalse(summary["decision"]["universal_law_claimed"])
        self.assertEqual(len(summary["predictions"]), 54)

    def test_independent_prediction_audit_passes(self):
        from verify_chwirut_holdout import verify_summary
        result = verify_summary(ROOT / "validation/chwirut-holdout.json")
        self.assertEqual(result["verification"], "passed")
        self.assertEqual(result["prediction_count"], 54)
        self.assertEqual(result["maximum_metric_absolute_error"], 0)


if __name__ == "__main__":
    unittest.main()

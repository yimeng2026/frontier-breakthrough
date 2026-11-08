import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_hahn1_high_temperature import analyze, fit_cubic_baseline, hahn_model, load_hahn_data, split_high_temperature


class Hahn1HighTemperatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT / "validation/hahn1-high-temperature-protocol.json").read_text(encoding="utf-8"))
        cls.x, cls.y = load_hahn_data(ROOT / "data/Hahn1.dat", cls.protocol["data"]["sha256"])

    def test_raw_data_and_high_temperature_split(self):
        self.assertEqual(len(self.x), 236)
        train, holdout = split_high_temperature(self.x)
        self.assertEqual((train.sum(), holdout.sum()), (219, 17))
        self.assertTrue(np.all(self.x[train] < 700))
        self.assertTrue(np.all(self.x[holdout] >= 700))

    def test_rational_model_at_zero_is_b1(self):
        self.assertEqual(hahn_model(0, 2, 3, 4, 5, 6, 7, 8), 2)

    def test_cubic_baseline_is_exact_on_cubic_data(self):
        x = np.linspace(-2, 2, 12)
        expected = 1 + 2 * x + 3 * x ** 2 + 4 * x ** 3
        coefficients = fit_cubic_baseline(x, expected)
        self.assertTrue(np.allclose(coefficients, [4, 3, 2, 1]))

    def test_full_fit_reproduces_nist_certification(self):
        summary = analyze(ROOT / "data/Hahn1.dat", ROOT / "validation/hahn1-high-temperature-protocol.json")
        certified = self.protocol["full_fit_certification_rule"]["certified_parameters"]
        for name in ("b1", "b2", "b3", "b4", "b5", "b6", "b7"):
            self.assertAlmostEqual(summary["full_fit_certification"]["parameters"][name] / certified[name], 1.0, places=3)
        self.assertAlmostEqual(
            summary["full_fit_certification"]["residual_standard_deviation"],
            self.protocol["full_fit_certification_rule"]["certified_residual_standard_deviation"],
            places=5,
        )

    def test_holdout_gate_and_prediction_count(self):
        summary = analyze(ROOT / "data/Hahn1.dat", ROOT / "validation/hahn1-high-temperature-protocol.json")
        metrics = summary["train_fit"]["metrics"]
        cubic = summary["baselines"]["cubic_polynomial"]
        expected = metrics["holdout_rmse"] < 3 * metrics["train_rmse"] and metrics["holdout_rmse"] < cubic["holdout_rmse"]
        self.assertEqual(summary["decision"]["limited_support"], expected)
        self.assertFalse(summary["decision"]["universal_law_claimed"])
        self.assertEqual(len(summary["predictions"]), 236)

    def test_independent_prediction_audit_passes(self):
        from verify_hahn1_high_temperature import verify_summary
        result = verify_summary(ROOT / "validation/hahn1-high-temperature.json")
        self.assertEqual(result["verification"], "passed")
        self.assertEqual(result["prediction_count"], 236)
        self.assertEqual(result["maximum_metric_absolute_error"], 0)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_box_bounds import pointwise_prediction_bound


class PredictionBoxBoundTests(unittest.TestCase):
    def test_known_rational_prediction_shift_and_residual_bound(self):
        result = pointwise_prediction_bound(
            numerator_coefficients=[1, 1],
            x="0.5",
            denominator_coefficients=[1, "-0.1"],
            standard_errors=["0.2"],
            radius=1,
            observed_y=2,
        )
        self.assertEqual(result["prediction_shift_upper_bound"], Fraction(60, 323))
        self.assertEqual(result["snapshot_prediction"], Fraction(30, 19))
        self.assertEqual(result["absolute_residual_upper_bound"], Fraction(3724, 6137))
        self.assertEqual(result["denominator_lower_bound"], Fraction(17, 20))

    def test_invalid_denominator_bound_is_rejected(self):
        with self.assertRaises(ValueError):
            pointwise_prediction_bound([1], 1, [1, -1], [1], 1)


if __name__ == "__main__":
    unittest.main()

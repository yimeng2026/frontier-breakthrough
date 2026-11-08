import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ellipsoid_bounds import covariance_support_upper_bound, pointwise_ellipsoid_bound, require_positive_definite


class EllipsoidBoundTests(unittest.TestCase):
    def test_covariance_support_is_exact_rational_upper_bound(self):
        upper, variance = covariance_support_upper_bound([[Fraction(1, 25)]], [Fraction(1)])
        self.assertEqual(variance, Fraction(1, 25))
        self.assertEqual(upper, Fraction(1, 5))
        upper_irrational, variance_irrational = covariance_support_upper_bound([[2]], [1])
        self.assertEqual(variance_irrational, 2)
        self.assertGreaterEqual(upper_irrational * upper_irrational, 2)

    def test_known_pointwise_bound_matches_box_when_covariance_is_isotropic(self):
        result = pointwise_ellipsoid_bound(
            numerator_coefficients=[1, 1], x="0.5",
            denominator_coefficients=[1, "-0.1"], denominator_covariance=[["0.04"]],
            radius=1, observed_y=2,
        )
        self.assertEqual(result["prediction_shift_upper_bound"], Fraction(60, 323))
        self.assertEqual(result["absolute_residual_upper_bound"], Fraction(3724, 6137))
        self.assertEqual(result["denominator_lower_bound"], Fraction(17, 20))

    def test_positive_definiteness_is_checked_exactly(self):
        require_positive_definite([[2, 1], [1, 2]])
        with self.assertRaises(ValueError):
            require_positive_definite([[1, 2], [2, 1]])


if __name__ == "__main__":
    unittest.main()

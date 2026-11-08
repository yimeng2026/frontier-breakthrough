import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ellipsoid_interval import certify_ellipsoid_interval, support_variance_coefficients


class EllipsoidIntervalTests(unittest.TestCase):
    def test_support_variance_polynomial_is_exact(self):
        coefficients = support_variance_coefficients([[Fraction(1, 25)]], 1)
        self.assertEqual(coefficients, [0, 0, Fraction(1, 25)])

    def test_continuous_safe_and_uncertified_intervals(self):
        safe = certify_ellipsoid_interval([1, "-0.1"], [["0.04"]], 1, 0, 1)
        self.assertTrue(safe["continuous_ellipsoid_safe"])
        self.assertEqual(safe["support_polynomial_root_count"], 0)
        unsafe = certify_ellipsoid_interval([1, "-0.1"], [["0.04"]], 10, 0, 1)
        self.assertFalse(unsafe["continuous_ellipsoid_safe"])
        self.assertGreater(unsafe["support_polynomial_root_count"], 0)

    def test_negative_interval_uses_same_squared_certificate(self):
        safe = certify_ellipsoid_interval([1, "0.1"], [["0.01"]], 1, -1, 0)
        self.assertTrue(safe["continuous_ellipsoid_safe"])


if __name__ == "__main__":
    unittest.main()

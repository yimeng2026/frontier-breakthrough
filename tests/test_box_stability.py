import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from box_stability import certified_box_safe, certify_parameter_box_radius


class BoxStabilityTests(unittest.TestCase):
    def test_positive_x_box_proof_is_continuous_not_point_sampling(self):
        coefficients = [1, "-0.1"]
        standard_errors = ["0.2"]
        self.assertTrue(certified_box_safe(coefficients, standard_errors, 0, 1, 1))
        self.assertFalse(certified_box_safe(coefficients, standard_errors, 0, 1, 10))

    def test_negative_x_box_uses_absolute_x_correctly(self):
        coefficients = [1, "0.1"]
        standard_errors = ["0.05"]
        self.assertTrue(certified_box_safe(coefficients, standard_errors, -1, 0, 1))
        self.assertFalse(certified_box_safe(coefficients, standard_errors, -1, 0, 20))

    def test_zero_crossing_interval_is_split_before_absolute_x_bounds(self):
        self.assertTrue(certified_box_safe([1, "-0.9"], ["0.1"], -1, 1, 0))
        self.assertFalse(certified_box_safe([1, "-0.9"], ["0.1"], -1, 1, 1))

    def test_radius_search_returns_certified_lower_bracket(self):
        result = certify_parameter_box_radius([1, "-0.1"], ["0.2"], 0, 1, cap=5, iterations=12)
        self.assertTrue(result["snapshot_safe"])
        self.assertTrue(result["certified_region_safe"])
        self.assertGreater(result["certified_radius_lower_bound"], 4)
        self.assertLess(result["certified_radius_lower_bound"], 5)
        self.assertTrue(certified_box_safe([1, "-0.1"], ["0.2"], 0, 1, result["certified_radius_lower_bound"]))
        self.assertFalse(certified_box_safe([1, "-0.1"], ["0.2"], 0, 1, result["uncertified_radius_upper_bound"]))


if __name__ == "__main__":
    unittest.main()

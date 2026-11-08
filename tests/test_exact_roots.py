import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exact_roots import exact_root_intervals


class ExactRootTests(unittest.TestCase):
    def test_three_integer_roots_and_closed_endpoints(self):
        coefficients = [-6, 11, -6, 1]
        intervals = exact_root_intervals(coefficients, 0, 4)
        self.assertEqual(len(intervals), 3)
        closed = exact_root_intervals(coefficients, 1, 3)
        self.assertEqual(len(closed), 3)
        for root in [Fraction(1), Fraction(2), Fraction(3)]:
            self.assertTrue(any(lower <= root <= upper for lower, upper in closed))
        self.assertEqual(closed[0], (Fraction(1), Fraction(1)))
        self.assertEqual(closed[-1], (Fraction(3), Fraction(3)))

    def test_repeated_root_is_counted_once(self):
        coefficients = [2, -5, 4, -1]
        intervals = exact_root_intervals(coefficients, 0, 3)
        self.assertEqual(len(intervals), 2)
        for root in [Fraction(1), Fraction(2)]:
            self.assertTrue(any(lower <= root <= upper for lower, upper in intervals))

    def test_no_real_roots_and_roots_outside_interval(self):
        self.assertEqual(exact_root_intervals([1, 0, 1], -10, 10), [])
        self.assertEqual(exact_root_intervals([-2, 0, 1], 0, 1), [])
        self.assertEqual(len(exact_root_intervals([-2, 0, 1], -2, 2)), 2)

    def test_thurber_fold_one_snapshot_has_one_exact_root(self):
        coefficients = [1, "1.0705802538223104", "0.4575080167330002", "0.07041862249370805"]
        intervals = exact_root_intervals(coefficients, "-3.067", "-2.699")
        self.assertEqual(len(intervals), 1)
        lower, upper = intervals[0]
        self.assertLessEqual(lower, Fraction("-3.01966"))
        self.assertGreaterEqual(upper, Fraction("-3.019663"))
        self.assertGreaterEqual(lower, Fraction("-3.067"))
        self.assertLessEqual(upper, Fraction("-2.699"))


if __name__ == "__main__":
    unittest.main()

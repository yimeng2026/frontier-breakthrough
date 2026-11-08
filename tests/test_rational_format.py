import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rational_format import bounded_text


class RationalFormatTests(unittest.TestCase):
    def test_small_fractions_remain_exact(self):
        self.assertEqual(bounded_text(Fraction(2, 3)), "2/3")

    def test_huge_positive_value_rounds_up_without_losing_bound(self):
        original = Fraction(10 ** 5000, 3)
        text = bounded_text(original)
        self.assertIn("e", text.lower())
        self.assertGreaterEqual(Fraction(text), original)

    def test_huge_negative_value_rounds_away_from_zero(self):
        original = Fraction(-(10 ** 5000), 3)
        text = bounded_text(original)
        self.assertLessEqual(Fraction(text), original)


if __name__ == "__main__":
    unittest.main()

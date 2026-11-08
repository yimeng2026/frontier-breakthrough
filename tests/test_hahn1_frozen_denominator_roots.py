import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_hahn1_frozen_denominator_roots import analyze, polynomial_root_records


class Hahn1FrozenDenominatorRootTests(unittest.TestCase):
    def test_known_cubic_roots_and_residues(self):
        parameters = {"b1": 1.0, "b2": 0.0, "b3": 0.0, "b4": 0.0, "b5": -6.0, "b6": 11.0, "b7": -6.0}
        records = polynomial_root_records(parameters)
        roots = [record["root_x"] for record in records if record["is_real"]]
        np.testing.assert_allclose(roots, [1.0 / 3.0, 0.5, 1.0], rtol=0, atol=1.0e-12)
        for record in records:
            if record["is_real"]:
                self.assertLess(record["absolute_denominator_residual"], 1.0e-12)
                self.assertNotEqual(record["numerator_at_root"], 0.0)
                self.assertNotEqual(record["denominator_derivative_at_root"], 0.0)

    def test_all_frozen_folds_are_audited_without_refitting(self):
        summary = analyze()
        self.assertEqual(len(summary["folds"]), 5)
        self.assertTrue(summary["analysis_scope"]["exploratory_follow_up"])
        self.assertFalse(summary["analysis_scope"]["refit"])
        for fold in summary["folds"]:
            for root in fold["real_roots"]:
                self.assertLess(root["absolute_denominator_residual"], 1.0e-6)
                self.assertIn("nearest_training_observation_distance_x", root)
        first = summary["folds"][0]
        self.assertEqual(first["real_root_count_in_held_out_closed_interval"], 2)
        poles = [root for root in first["real_roots"] if root["within_held_out_closed_interval"]]
        self.assertAlmostEqual(poles[0]["root_x"], 45.52697791771662)
        self.assertAlmostEqual(poles[1]["root_x"], 72.131671472642)
        for pole in poles:
            self.assertNotEqual(pole["numerator_at_root"], 0.0)
            self.assertNotEqual(pole["denominator_derivative_at_root"], 0.0)
        for fold in summary["folds"][1:]:
            self.assertEqual(fold["real_root_count_in_held_out_closed_interval"], 0)
        self.assertFalse(summary["decision"]["fold_1_failure_reversed"])


if __name__ == "__main__":
    unittest.main()

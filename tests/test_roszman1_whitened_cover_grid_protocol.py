import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-whitened-cover-grid-protocol.json"


class Roszman1WhitenedCoverGridProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Whitened-cover protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_grid_and_point_accounting(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_whitened_cover_grid")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 5)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["ratio_bounds"]["sha256"], "7e4a70116617e408ada047597e1ff2609224e64cb0c6e7cd230dd6d4c4b0c103")
        self.assertEqual(inputs["ratio_receipt"]["sha256"], "d43372719b626a3ccc233b493e42b806e316761c283b0d1c60eb2781a170dc65")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["interval_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")
        self.assertEqual(self.protocol["whitening_rule"]["subdivisions_per_dimension"], [1, 2, 4])
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["grid_cover_count"], 60)
        self.assertEqual(expected["partition_cell_count"], 5460)
        self.assertEqual(expected["outside_cell_count"], 0)
        self.assertEqual(expected["nonempty_intersection_count"], 60)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["candidate_grid_containment_check_count"], 600)
        self.assertEqual(expected["transform_witness_count"], 200)
        self.assertEqual(expected["transform_violation_count"], 0)
        self.assertEqual(expected["grid_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)

    def test_nonidentity_whitening_known_answer(self):
        # C=diag(4,1,1,1), L=diag(2,1,1,1), r=1, u=L^-1 delta.
        # The whitened cube [-1,1]^4 covers the ball but also contains points outside it.
        self.assertEqual([2 * -1, 2 * 1], [-2, 2])
        b1_interval = [1 - 2, 1 + 2]
        self.assertEqual(b1_interval, [-1, 3])
        self.assertEqual(-1 + 0.0, -1.0)
        self.assertEqual(3 - math.atan(-1) / math.pi, 3.25)
        delta3, delta4 = 0.6, -0.8
        norm = math.sqrt(delta3 ** 2 + delta4 ** 2)
        self.assertAlmostEqual(norm, 1.0)
        prediction = 1 - math.atan(1.6 / -1.2) / math.pi
        self.assertGreaterEqual(prediction, -1.0)
        self.assertLessEqual(prediction, 3.25)
        outside_min_norm = math.sqrt(4 * 0.75 ** 2)
        self.assertGreater(outside_min_norm, 1.0)
        possible_ball_min_norm = math.sqrt(4 * 0.25 ** 2)
        self.assertLessEqual(possible_ball_min_norm, 1.0)
        known = self.protocol["whitening_rule"]["known_answer"]
        self.assertEqual(known["cholesky_diagonal"], [2, 1, 1, 1])
        self.assertEqual(known["natural_prediction_minimum"], -1.0)
        self.assertEqual(known["natural_prediction_maximum"], 3.25)
        self.assertEqual(known["outside_minimum_norm"], 1.5)
        self.assertEqual(known["possible_ball_minimum_norm"], 0.5)

    def test_unresolved_cells_and_scope_are_frozen(self):
        rule = self.protocol["whitening_rule"]
        self.assertEqual(rule["transform"], "C=L*L^T; u=L^-1*(theta-theta_center); ||u||<=r; theta=theta_center+L*u")
        self.assertEqual(rule["whitened_box"], "[-r,r]^4")
        self.assertEqual(rule["outside_rule"], "Discard a cell only when its minimum Euclidean distance to the whitened origin is strictly greater than r")
        self.assertEqual(rule["crossing_rule"], "If a cell may intersect the ball and its denominator interval contains zero, preserve it as unresolved and make the grid union unbounded; never drop it or assign a finite native interval")
        crossing = [-1.0, 0.5]
        self.assertLessEqual(crossing[0], 0.0)
        self.assertGreaterEqual(crossing[1], 0.0)
        self.assertTrue(self.protocol["analysis_scope"]["whole_ellipsoid_conservative"])
        self.assertTrue(self.protocol["analysis_scope"]["unresolved_cells_preserved"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["crossing_cells_given_finite_native_intervals"])
        self.assertFalse(self.protocol["decision"]["unproven_cells_discarded"])
        self.assertFalse(self.protocol["decision"]["exact_global_optimum_claimed"])


if __name__ == "__main__":
    unittest.main()

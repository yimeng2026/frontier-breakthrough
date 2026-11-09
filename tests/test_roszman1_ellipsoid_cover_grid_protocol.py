import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-ellipsoid-cover-grid-protocol.json"


class Roszman1EllipsoidCoverGridProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Ellipsoid-cover grid protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_grid_and_unavailable_fold(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_ellipsoid_cover_grid")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 5)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["ratio_bounds"]["sha256"], "7e4a70116617e408ada047597e1ff2609224e64cb0c6e7cd230dd6d4c4b0c103")
        self.assertEqual(inputs["ratio_receipt"]["sha256"], "d43372719b626a3ccc233b493e42b806e316761c283b0d1c60eb2781a170dc65")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["interval_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")
        expected = self.protocol["expected_structure"]
        self.assertEqual(self.protocol["grid_rule"]["subdivisions_per_dimension"], [1, 2, 4])
        self.assertEqual(self.protocol["grid_rule"]["cells_per_grid"], [1, 16, 256])
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["grid_cover_count"], 60)
        self.assertEqual(expected["cell_evaluation_count"], 5460)
        self.assertEqual(expected["nonempty_intersection_count"], 60)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["candidate_grid_containment_check_count"], 600)
        self.assertEqual(expected["grid_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)

    def test_known_answer_cover_native_interval_and_nested_grids(self):
        # Unit ellipsoid: b1 in [0,2], b2 in [-0.9,1.1], b3 in [0,2], b4 in [1,3], x=0.
        # Every denominator x-b4 is negative, and the whole ellipsoid is inside this box.
        bounds = [[0.0, 2.0], [-0.9, 1.1], [0.0, 2.0], [1.0, 3.0]]
        for divisions in [1, 2, 4]:
            partitions = []
            for lower, upper in bounds:
                partitions.append([lower + index * (upper - lower) / divisions for index in range(divisions + 1)])
            self.assertEqual([len(values) for values in partitions], [divisions + 1] * 4)
            self.assertEqual([values[0] for values in partitions], [row[0] for row in bounds])
            self.assertEqual([values[-1] for values in partitions], [row[1] for row in bounds])
            for values in partitions:
                self.assertEqual(values, sorted(values))
        # Natural interval: b1 in [0,2], b3/(x-b4) in [-1,0], -atan(z)/pi in [0,1/4].
        self.assertEqual(0.0 + 0.0, 0.0)
        self.assertEqual(2.0 - math.atan(-1.0) / math.pi, 2.25)
        witness = {"b1": 1.0, "b2": 0.1, "b3": 1.6, "b4": 1.2}
        self.assertAlmostEqual((witness["b3"] - 1) ** 2 + (witness["b4"] - 2) ** 2, 1.0)
        prediction = witness["b1"] - math.atan(witness["b3"] / (0 - witness["b4"])) / math.pi
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 2.25)
        known = self.protocol["grid_rule"]["known_answer"]
        self.assertEqual(known["coordinate_bounds"], bounds)
        self.assertEqual(known["natural_prediction_minimum"], 0.0)
        self.assertEqual(known["natural_prediction_maximum"], 2.25)
        self.assertEqual(known["singular_control_b4_upper"], 1.5)
        self.assertEqual(known["singular_control_denominator_maximum"], 0.5)
        self.assertGreater(known["singular_control_denominator_maximum"], 0.0)

    def test_full_cover_scope_and_rejected_shortcut_are_frozen(self):
        self.assertIn("quadratic", self.protocol["rejected_shortcut"]["reason"])
        self.assertTrue(self.protocol["analysis_scope"]["whole_ellipsoid_conservative"])
        self.assertTrue(self.protocol["analysis_scope"]["nested_grid_cover"])
        self.assertTrue(self.protocol["analysis_scope"]["crossing_fold_receives_no_bound"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["exact_global_optimum_claimed"])
        self.assertFalse(self.protocol["decision"]["linear_fractional_shortcut_used"])
        self.assertFalse(self.protocol["decision"]["fold5_given_finite_bound"])


if __name__ == "__main__":
    unittest.main()

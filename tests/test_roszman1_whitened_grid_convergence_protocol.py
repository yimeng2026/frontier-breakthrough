import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-whitened-grid-convergence-protocol.json"


class Roszman1WhitenedGridConvergenceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Whitened-grid convergence protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_structure_and_storage_budget(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_whitened_grid_convergence")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 6)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["whitened_bounds"]["sha256"], "76bcbec485dac10e2b73b2eb91426ff657c3c482a2610df6ed8cf145e8b1cd3c")
        self.assertEqual(inputs["whitened_receipt"]["sha256"], "4809ab4f01712094814b58e3ead4728b9bdcb105d5fe6a7e3c2cc88750c97e9a")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["whitened_runner"]["sha256"], "abd9b89610398953386e86cf2676081056d14737f9ae1870687d9c7e3dde64a9")
        self.assertEqual(inputs["interval_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["grid4_reference_count"], 20)
        self.assertEqual(expected["grid8_cover_count"], 20)
        self.assertEqual(expected["grid8_partition_cell_count"], 81920)
        self.assertEqual(expected["outside_cell_count"], 0)
        self.assertEqual(expected["nonempty_intersection_count"], 20)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["candidate_grid8_containment_check_count"], 200)
        self.assertEqual(expected["transform_witness_count"], 200)
        self.assertEqual(expected["transform_violation_count"], 0)
        self.assertEqual(expected["grid8_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["point_grid8_consistency_check_count"], 20)
        self.assertEqual(expected["refit_count"], 0)
        self.assertFalse(self.protocol["output_rule"]["duplicate_all_cell_records"])

    def test_incremental_ratio_plateau_and_witness_known_answers(self):
        rule = self.protocol["comparison_rule"]
        self.assertEqual(rule["incremental_width_ratio"], "grid8_intersection_width/grid4_intersection_width")
        self.assertEqual(rule["plateau"], "incremental_width_ratio=1 within the frozen 1e-12 relative-plus-absolute numerical tolerance; descriptive only, not a convergence proof")
        width4, width8 = 0.2, 0.15
        self.assertAlmostEqual(width8 / width4, 0.75)
        self.assertAlmostEqual(0.2 / 0.2, 1.0)
        # Unit-ball known answer: n=1 cube vertices have norm 2 and are outside;
        # n=2 also admits vertices with only one nonzero coordinate and norm 1.
        self.assertEqual(math.sqrt(4 * 1.0), 2.0)
        self.assertEqual(math.sqrt(1.0), 1.0)
        self.assertEqual(self.protocol["witness_rule"]["known_answer"]["grid1_vertex_norm"], 2.0)
        self.assertEqual(self.protocol["witness_rule"]["known_answer"]["grid2_single_axis_vertex_norm"], 1.0)
        self.assertEqual(self.protocol["witness_rule"]["vertices_per_witness_cell"], 16)

    def test_witness_and_failure_scope_are_frozen(self):
        rule = self.protocol["witness_rule"]
        self.assertEqual(rule["selection"], "For each bounded grid-8 union endpoint, retain the attaining cell and evaluate all 16 whitened-cell vertices with the original native model")
        self.assertEqual(rule["feasibility"], "A vertex is a feasible extremum candidate only when its whitened norm is at most r within tolerance and its denominator is negative; outer-cover vertices remain witnesses but are not feasible extrema")
        self.assertEqual(rule["unresolved"], "No finite vertex witness is manufactured for an unresolved denominator cell; an unbounded union remains unbounded")
        self.assertEqual(self.protocol["comparison_rule"]["native_cell_evaluation_count"], "81920-unresolved_cell_count")
        self.assertEqual(self.protocol["comparison_rule"]["vertex_evaluation_count"], "16*witness_cell_count")
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["grid8_called_global_optimum"])
        self.assertFalse(self.protocol["decision"]["plateau_called_convergence_proof"])
        self.assertFalse(self.protocol["decision"]["outer_vertices_called_feasible"])
        self.assertFalse(self.protocol["decision"]["fold5_given_finite_bound"])


if __name__ == "__main__":
    unittest.main()

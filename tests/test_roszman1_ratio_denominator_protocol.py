import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/roszman1-ratio-denominator-protocol.json"


class Roszman1RatioDenominatorProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "Ratio-denominator protocol must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_inputs_and_structure_preserve_the_unavailable_fold(self):
        self.assertEqual(self.protocol["status"], "frozen_before_roszman1_ratio_denominator_joint_interval")
        inputs = self.protocol["inputs"]
        self.assertEqual(len(inputs), 7)
        self.assertEqual(inputs["native_identifiability"]["sha256"], "9888145d181c157da33b3bf0f93980ef0db15e4d3b368a96330c775363bc4322")
        self.assertEqual(inputs["independent_bounds"]["sha256"], "50c672fc3022b34465557daf98a12ce1f975b358e6ba5c9590202a2bdc4660a9")
        self.assertEqual(inputs["independent_receipt"]["sha256"], "e711e4f452234dd816334709cdf73901c8131bafdf72fcd524a94be2f209f3e3")
        self.assertEqual(inputs["joint_linear_bounds"]["sha256"], "45852e2534f51098ae390e62092d1b8df04c609d37aba5211121f637599c3b35")
        self.assertEqual(inputs["joint_linear_receipt"]["sha256"], "5f0eb06cc99161eaaabbdc033ffa49998f97a9c8bb795b8cf09edf888d9e4ff5")
        self.assertEqual(inputs["native_model_runner"]["sha256"], "fa1c255122d0b8db9c3866e3dc9b8ac9565289667d1531230f499416b389ee0d")
        self.assertEqual(inputs["baseline_runner"]["sha256"], "c3b84888aba9326ccb82e052401d7827e7c38b623855cc8e76cebd4d5505295e")
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["held_out_point_count"], 25)
        self.assertEqual(expected["available_point_count"], 20)
        self.assertEqual(expected["unavailable_point_count"], 5)
        self.assertEqual(expected["unavailable_fold_ids"], [5])
        self.assertEqual(expected["ratio_interval_count"], 20)
        self.assertEqual(expected["algebraic_extremizer_count"], 40)
        self.assertEqual(expected["support_candidate_evaluation_count"], 160)
        self.assertEqual(expected["candidate_evaluation_count"], 200)
        self.assertEqual(expected["ratio_candidate_violation_count"], 0)
        self.assertEqual(expected["alternative_candidate_violation_count"], 0)
        self.assertEqual(expected["intersection_candidate_violation_count"], 0)
        self.assertEqual(expected["center_prediction_mismatch_count"], 0)
        self.assertEqual(expected["refit_count"], 0)

    def test_known_answer_quadratic_branches_and_extremizers(self):
        # b3=1+delta3, d=-2-delta4, delta3^2+delta4^2<=1, d<0.
        # alpha=1+2t, q=1+t^2, hence alpha^2-q=3t^2+4t.
        roots = [-4 / 3, 0.0]
        alpha = lambda t: 1 + 2 * t
        q = lambda t: 1 + t * t
        h_plus = lambda t: alpha(t) + math.sqrt(q(t))
        h_minus = lambda t: alpha(t) - math.sqrt(q(t))
        self.assertAlmostEqual(h_plus(roots[0]), 0.0)
        self.assertAlmostEqual(h_minus(roots[1]), 0.0)
        self.assertNotAlmostEqual(h_minus(roots[0]), 0.0)
        self.assertNotAlmostEqual(h_plus(roots[1]), 0.0)
        lower_delta = [0.6, -0.8]
        upper_delta = [-1.0, 0.0]
        self.assertAlmostEqual(sum(value * value for value in lower_delta), 1.0)
        self.assertAlmostEqual(sum(value * value for value in upper_delta), 1.0)
        self.assertAlmostEqual((1 + lower_delta[0]) / (-2 - lower_delta[1]), roots[0])
        self.assertAlmostEqual((1 + upper_delta[0]) / (-2 - upper_delta[1]), roots[1])
        for scale in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            delta = [scale * 0.6, -scale * 0.8]
            ratio = (1 + delta[0]) / (-2 - delta[1])
            self.assertGreaterEqual(ratio, roots[0] - 1.0e-15)
            self.assertLessEqual(ratio, roots[1] + 1.0e-15)
        self.assertLessEqual(-2 - lower_delta[1], 0.0)
        self.assertLessEqual(-2 - upper_delta[1], 0.0)
        self.assertEqual(self.protocol["ratio_rule"]["known_answer"]["ratio_minimum"], -4 / 3)
        self.assertEqual(self.protocol["ratio_rule"]["known_answer"]["ratio_maximum"], 0.0)

    def test_scope_and_singular_negative_control_are_frozen(self):
        rule = self.protocol["ratio_rule"]
        self.assertEqual(rule["denominator_sign"], "negative")
        self.assertEqual(rule["quadratic_form"], "A=d0^2-r^2*C44; B=c*d0+r^2*C34; D=c^2-r^2*C33; solve A*t^2-2*B*t+D=0")
        self.assertEqual(rule["lower_branch"], "alpha=c-t*d0<=0 and alpha+r*sqrt(C33+2*t*C34+t^2*C44)=0")
        self.assertEqual(rule["upper_branch"], "alpha=c-t*d0>=0 and alpha-r*sqrt(C33+2*t*C34+t^2*C44)=0")
        self.assertEqual(rule["lower_extremizer"], "delta=+r*C*(e3+t*e4)/sqrt((e3+t*e4)^T*C*(e3+t*e4))")
        self.assertEqual(rule["upper_extremizer"], "delta=-r*C*(e3+t*e4)/sqrt((e3+t*e4)^T*C*(e3+t*e4))")
        self.assertLessEqual((-1) ** 2 - 1 ** 2 * 1, 0.0, "A<=0 must reject the sign-crossing toy example")
        self.assertTrue(self.protocol["analysis_scope"]["ratio_component_exact_support"])
        self.assertTrue(self.protocol["analysis_scope"]["crossing_fold_receives_no_bound"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["charnes_cooper_relaxation_used"])
        self.assertFalse(self.protocol["decision"]["full_nonlinear_global_optimum_claimed"])
        self.assertFalse(self.protocol["decision"]["fold5_given_finite_bound"])


if __name__ == "__main__":
    unittest.main()

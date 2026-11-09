import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-protocol.json"
AMENDMENT = ROOT / "validation/enso-native-ellipsoid-radius-sensitivity-protocol-amendment-01.json"


class EnsoNativeEllipsoidRadiusSensitivityProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOCOL.is_file(), "ENSO radius-sensitivity protocol must be frozen before implementation")
        self.assertTrue(AMENDMENT.is_file(), "Fold-specific count correction must be frozen before implementation")
        self.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        self.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))

    def test_frozen_inputs_match_stage47_and_native_identifiability(self):
        self.assertEqual(self.protocol["status"], "frozen_before_enso_native_ellipsoid_radius_sensitivity")
        inputs = self.protocol["inputs"]
        self.assertEqual(inputs["native_identifiability"]["sha256"], "19656ed9f5930bed7e9bbdcd1072f50b5e68a8836c1975ab550dc1d828011d7e")
        self.assertEqual(inputs["baseline_bounds"]["sha256"], "d6eab927eaafc9dc8d469fa42e830660b0e673bde52031b1cd2bd78f795f61ea")
        self.assertEqual(inputs["baseline_bounds"]["baseline_radius"], 4)
        self.assertEqual(inputs["baseline_runner"]["sha256"], "614a419ce8388ab644b9665023600ebfb475c82577b550e74ee632b4f9c438e1")
        self.assertEqual(self.amendment["original_protocol"]["sha256"], "c1a7cceef711a7b1b401de43dd451cf2a37f1974010a13a9c2a0dd8f5d955ef2")

    def test_grid_and_maximum_evaluation_counts_are_frozen(self):
        grid = self.protocol["grid_rule"]
        self.assertEqual(grid["radii"], [1, 2, 4, 8, 16, 32])
        self.assertEqual(grid["case_count"], 30)
        expected = self.protocol["expected_structure"]
        self.assertEqual(expected["fold_count"], 5)
        self.assertEqual(expected["radius_count"], 6)
        self.assertEqual(expected["case_count"], 30)
        self.assertEqual(expected["refit_count"], 0)
        corrected = self.amendment["correction"]["corrected_structure"]
        self.assertEqual(corrected["held_out_point_count_per_radius"], 168)
        self.assertEqual(corrected["unique_month_count_per_radius"], 168)
        self.assertEqual(corrected["fold_held_out_point_counts"], [34, 34, 34, 33, 33])
        self.assertEqual(corrected["fold_unique_month_counts"], [34, 34, 34, 33, 33])
        self.assertEqual(corrected["maximum_point_evaluations"], 1008)
        self.assertEqual(corrected["maximum_envelope_evaluations"], 1008)
        self.assertEqual(corrected["formula"], "6 radii * (34+34+34+33+33) fold-specific held-out observations = 1008 evaluations")
        self.assertEqual(grid["maximum_point_evaluations"], 5040)
        self.assertTrue(self.amendment["preservation_rule"]["original_protocol_file_unchanged"])

    def test_baseline_and_scope_prohibit_radius_optimization(self):
        self.assertEqual(self.protocol["baseline_rule"]["radius"], 4)
        self.assertTrue(self.protocol["analysis_scope"]["retrospective_fixed_grid_sensitivity"])
        self.assertFalse(self.protocol["analysis_scope"]["prospective_independent_validation"])
        for key, value in self.protocol["decision"].items():
            self.assertFalse(value, key)
        self.assertFalse(self.protocol["decision"]["optimal_radius_selected"])
        self.assertFalse(self.protocol["decision"]["unavailable_cases_given_bounds"])
        self.assertFalse(self.protocol["decision"]["positive_period_used_as_physical_proof"])


if __name__ == "__main__":
    unittest.main()

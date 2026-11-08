import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_grouped_stress import analyze, make_contiguous_folds, validate_summary


class GroupedStressTests(unittest.TestCase):
    def test_contiguous_folds_have_no_x_leakage_and_cover_all_observations(self):
        x = np.array([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        folds = make_contiguous_folds(x, 5)
        self.assertEqual(len(folds), 5)
        for fold in folds:
            train, test = fold
            self.assertFalse(set(x[train]) & set(x[test]))
            self.assertGreater(len(test), 0)
            self.assertGreater(len(train), 0)
            self.assertEqual(int(train.sum() + test.sum()), len(x))
        self.assertSetEqual(set(np.concatenate([x[test] for _, test in folds])), set(x))

    def test_summary_has_fifteen_audited_folds_and_explicit_decisions(self):
        summary = analyze()
        self.assertEqual(len(summary["datasets"]), 3)
        self.assertEqual(sum(len(item["folds"]) for item in summary["datasets"]), 15)
        self.assertEqual(validate_summary(summary), [])
        for item in summary["datasets"]:
            finite = all(fold["model_metrics"]["rmse"] is not None and fold["baseline_metrics"]["rmse"] is not None for fold in item["folds"])
            all_not_worse = all(fold["model_metrics"]["rmse"] <= fold["baseline_metrics"]["rmse"] for fold in item["folds"])
            self.assertEqual(item["decision"]["robust_limited_support"], finite and all_not_worse)
            self.assertFalse(item["decision"]["universal_law_claimed"])
        self.assertTrue((ROOT / "papers/08_跨数据集压力测试/fig08_grouped_stress.png").is_file())


if __name__ == "__main__":
    unittest.main()

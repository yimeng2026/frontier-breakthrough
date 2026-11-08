import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_continuation_word import EXPECTED, OUTPUT, prepare_continuation_markdown
from build_total_word import audit_docx_package


class FrontierContinuationWordTests(unittest.TestCase):
    def test_prepare_inserts_eckerle_figure_and_caption(self):
        source = "# 前沿共生续展：双尾外推与求解器复核\n\n公式 \\(y=(b_1/b_2)\\exp[-\\frac{1}{2}((x-b_3)/b_2)^2]+e\\)。\n\n图：`papers/06_第二真实数据外推/fig06_eckerle4_two_tail.png`。\n"
        result = prepare_continuation_markdown(source)
        self.assertIn("![](papers/06_第二真实数据外推/fig06_eckerle4_two_tail.png)", result)
        self.assertIn("**图 06｜Eckerle4 双尾外推检验**", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn("\\(y=(b_1/b_2)\\exp[-\\frac{1}{2}((x-b_3)/b_2)^2]+e\\)", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_continuation_word_has_native_content(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 7, "images": 1, "tables": 4})


if __name__ == "__main__":
    unittest.main()

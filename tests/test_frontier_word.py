import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_word import EXPECTED, OUTPUT, audit_docx_package, prepare_frontier_markdown


class FrontierWordTests(unittest.TestCase):
    def test_prepare_inserts_real_figures_and_preserves_math(self):
        source = "# 前沿共生计划扩展工作包：首轮五条主线\n\n公式 \\(y=\\exp(-b_1x)/(b_2+b_3x)+e\\)。\n\n图：`papers/04_真实数据留出/fig04_chwirut_holdout.png`。\n\n图：`papers/05_材料跨库复核/fig05_material_crosscheck.png`。\n"
        result = prepare_frontier_markdown(source)
        self.assertIn("![](papers/04_真实数据留出/fig04_chwirut_holdout.png)", result)
        self.assertIn("![](papers/05_材料跨库复核/fig05_material_crosscheck.png)", result)
        self.assertIn("**图 04｜NIST Chwirut2 高距离留出检验**", result)
        self.assertIn("**图 05｜MP／OQMD／PyMatGen 材料跨库复核**", result)
        self.assertIn("\\(y=\\exp(-b_1x)/(b_2+b_3x)+e\\)", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_native_math_images_and_tables(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 5, "images": 2, "tables": 3})


if __name__ == "__main__":
    unittest.main()

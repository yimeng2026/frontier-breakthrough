import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_rational_word import EXPECTED, OUTPUT, prepare_rational_markdown
from build_total_word import audit_docx_package


class FrontierRationalWordTests(unittest.TestCase):
    def test_prepare_inserts_hahn1_figure_and_caption(self):
        source = "# 前沿共生第三阶段：有理模型外推与分母边界\n\n公式 \\(y=(b_1+b_2x)/(1+b_5x)+e\\)。\n\n图：`papers/07_有理模型外推/fig07_hahn1_high_temperature.png`。\n"
        result = prepare_rational_markdown(source)
        self.assertIn("![](papers/07_有理模型外推/fig07_hahn1_high_temperature.png)", result)
        self.assertIn("**图 07｜Hahn1 高温有理模型外推**", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn("\\(y=(b_1+b_2x)/(1+b_5x)+e\\)", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_rational_word_has_native_content(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 7, "images": 1, "tables": 4})


if __name__ == "__main__":
    unittest.main()

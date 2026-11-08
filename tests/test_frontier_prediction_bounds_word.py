import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_prediction_bounds_word import EXPECTED, OUTPUT, prepare_prediction_bounds_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/15_参数盒预测界/fig15_prediction_box_bounds.png"


class FrontierPredictionBoundsWordTests(unittest.TestCase):
    def test_prepare_inserts_prediction_bounds_figure_and_caption(self):
        source = "# 前沿共生第十一阶段：参数盒内预测误差界\n\n**日期**：2026-11-09  \n\n公式 \\(R(x)=\\rho\\sum_j\\sigma_j|x|^j\\)。\n\n图：`papers/15_参数盒预测界/fig15_prediction_box_bounds.png`。\n"
        result = prepare_prediction_bounds_markdown(source)
        self.assertIn("![](papers/15_参数盒预测界/fig15_prediction_box_bounds.png)", result)
        self.assertIn("**图 15｜认证参数盒内逐点预测与残差上界**", result)
        self.assertIn("§3「结果：13 折有界，但信息质量差异巨大」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_prediction_bounds_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 12, "images": 1, "tables": 3})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_box_stability_word import EXPECTED, OUTPUT, prepare_box_stability_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/14_参数盒稳定性/fig14_parameter_box_stability.png"


class FrontierBoxStabilityWordTests(unittest.TestCase):
    def test_prepare_inserts_box_stability_figure_and_caption(self):
        source = "# 前沿共生第十阶段：系数扰动下的参数盒稳定性\n\n**日期**：2026-11-09  \n\n公式 \\(|\\delta c_j|\\leq\\rho\\sigma_j\\)。\n\n图：`papers/14_参数盒稳定性/fig14_parameter_box_stability.png`。\n"
        result = prepare_box_stability_markdown(source)
        self.assertIn("![](papers/14_参数盒稳定性/fig14_parameter_box_stability.png)", result)
        self.assertIn("**图 14｜连续参数盒无根认证半径**", result)
        self.assertIn("§3「十五折结果」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_box_stability_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 14, "images": 1, "tables": 3})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

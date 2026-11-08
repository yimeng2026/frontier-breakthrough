import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_ellipsoid_bounds_word import EXPECTED, OUTPUT, prepare_ellipsoid_bounds_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png"


class FrontierEllipsoidBoundsWordTests(unittest.TestCase):
    def test_prepare_inserts_ellipsoid_figure_and_caption(self):
        source = "# 前沿共生第十二阶段：协方差椭球与独立参数盒的比较\n\n**日期**：2026-11-09  \n\n公式 \\(R_E(x)=\\rho\\sqrt{z(x)^T\\Sigma z(x)}\\)。\n\n图：`papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png`。\n"
        result = prepare_ellipsoid_bounds_markdown(source)
        self.assertIn("![](papers/16_椭球与参数盒/fig16_ellipsoid_box_comparison.png)", result)
        self.assertIn("**图 16｜协方差椭球与独立参数盒逐点比较**", result)
        self.assertIn("§3「全部适用点的比较结果」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_ellipsoid_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 10, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

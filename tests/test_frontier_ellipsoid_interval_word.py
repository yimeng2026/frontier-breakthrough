import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_ellipsoid_interval_word import EXPECTED, OUTPUT, prepare_ellipsoid_interval_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png"


class FrontierEllipsoidIntervalWordTests(unittest.TestCase):
    def test_prepare_inserts_ellipsoid_interval_figure_and_caption(self):
        source = "# 前沿共生第十三阶段：协方差椭球的连续区间安全证明\n\n**日期**：2026-11-09  \n\n公式 \\(D(x)^2-\\rho^2z(x)^T\\Sigma z(x)>0\\)。\n\n图：`papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png`。\n"
        result = prepare_ellipsoid_interval_markdown(source)
        self.assertIn("![](papers/17_椭球连续区间/fig17_ellipsoid_interval_safety.png)", result)
        self.assertIn("**图 17｜协方差椭球连续区间平方支撑证明**", result)
        self.assertIn("§3「十三折连续区间验收结果」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_ellipsoid_interval_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 4, "images": 1, "tables": 3})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

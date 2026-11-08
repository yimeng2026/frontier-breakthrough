import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_filip_coverage_word import EXPECTED, OUTPUT, prepare_filip_coverage_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png"


class FrontierFilipCoverageWordTests(unittest.TestCase):
    def test_prepare_inserts_filip_figure_and_caption(self):
        source = "# 前沿共生第十四阶段：Filip 外部数据上的椭球覆盖与候选压力测试\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。\n"
        result = prepare_filip_coverage_markdown(source)
        self.assertIn("![](papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png)", result)
        self.assertIn("**图 18｜Filip 外部候选预测与逐点界可用性**", result)
        self.assertIn("§3「逐点覆盖与界的宽度」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_filip_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 2, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

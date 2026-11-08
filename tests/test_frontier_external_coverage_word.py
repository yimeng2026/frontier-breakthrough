import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_external_coverage_word import EXPECTED, OUTPUT, prepare_external_coverage_markdown
from build_total_word import audit_docx_package

FIGURES = [
    ROOT / "papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png",
    ROOT / "papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png",
]


class FrontierExternalCoverageWordTests(unittest.TestCase):
    def test_prepare_inserts_both_figures_in_order(self):
        source = "# 前沿共生第十五阶段：可复用外部覆盖协议与跨数据对照\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。\n\n图：`papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png`。\n"
        result = prepare_external_coverage_markdown(source)
        first = result.index("![](papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png)")
        second = result.index("![](papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png)")
        self.assertLess(first, second)
        self.assertIn("顺序第 1 幅，共 2 幅", result)
        self.assertIn("顺序第 2 幅，共 2 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_external_word_has_both_exact_figures_and_native_content(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 1, "images": 2, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = sorted(name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/"))
            self.assertEqual(len(media), 2)
            embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media}
            source_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in FIGURES}
            self.assertEqual(embedded_hashes, source_hashes)
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

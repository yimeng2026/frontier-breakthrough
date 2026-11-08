import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_gauss1_coverage_word.py"
FIGURES = [
    ROOT / "papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png",
    ROOT / "papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png",
    ROOT / "papers/20_Gauss1椭球覆盖/fig20_gauss1_ellipsoid_coverage.png",
]


class FrontierGauss1CoverageWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Gauss1 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_gauss1_coverage_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_three_figures_in_order(self):
        module = self.load_builder()
        source = "# 前沿共生第十六阶段：Gauss1 外部反例与三数据证据轴对照\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/18_Filip椭球覆盖/fig18_filip_ellipsoid_coverage.png`。\n\n图：`papers/19_MGH17椭球覆盖/fig19_mgh17_ellipsoid_coverage.png`。\n\n图：`papers/20_Gauss1椭球覆盖/fig20_gauss1_ellipsoid_coverage.png`。\n"
        result = module.prepare_gauss1_coverage_markdown(source)
        positions = [result.index(f"![]({path.relative_to(ROOT).as_posix()})") for path in FIGURES]
        self.assertEqual(positions, sorted(positions))
        for index in range(1, 4):
            self.assertIn(f"顺序第 {index} 幅，共 3 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_three_exact_figures_and_native_content(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 1, "images": 3, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = sorted(name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/"))
            self.assertEqual(len(media), 3)
            embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media}
            source_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in FIGURES}
            self.assertEqual(embedded_hashes, source_hashes)
            document = archive.read("word/document.xml")
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

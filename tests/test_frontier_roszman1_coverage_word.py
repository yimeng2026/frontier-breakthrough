import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_coverage_word.py"
FIGURE = ROOT / "papers/35_Roszman1椭球覆盖/fig35_roszman1_ellipsoid_coverage.png"


class FrontierRoszman1CoverageWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Roszman1 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_coverage_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第二十九阶段：Roszman1 小样本预测—证明解离与平移主导界审计\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/35_Roszman1椭球覆盖/fig35_roszman1_ellipsoid_coverage.png`。\n"
        result = module.prepare_roszman1_coverage_markdown(source)
        self.assertIn("![](papers/35_Roszman1椭球覆盖/fig35_roszman1_ellipsoid_coverage.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 2, "images": 1, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_small_sample_and_fold_specific_boundaries(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_COVERAGE_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["5 点可给界，20 点不可用", "第 1、4 折", "0 个可用界", "4 个盒／椭球可比较点", "1 点只有椭球界", "四参数反正切模型", "不写成 25 点全部覆盖"]:
            self.assertIn(text, report)
        self.assertNotIn("native Filip", report)


if __name__ == "__main__":
    unittest.main()

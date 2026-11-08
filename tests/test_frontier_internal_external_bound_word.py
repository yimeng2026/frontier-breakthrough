import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_internal_external_bound_word.py"
FIGURE = ROOT / "papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png"


class FrontierInternalExternalBoundWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing internal/external Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_internal_external_bound_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第十九阶段：内外部界组成对照与六组分布\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png`。\n"
        result = module.prepare_internal_external_bound_markdown(source)
        self.assertIn("![](papers/24_内外部界组成对照/fig24_internal_external_bound_comparison.png)", result)
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

    def test_report_preserves_scope_and_six_distributions(self):
        self.load_builder()
        report = (ROOT / "docs/INTERNAL_EXTERNAL_BOUND_COMPARISON_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["674", "482", "192", "0.982085", "0.898048", "0.944464", "0.169474", "不计算合并成功率"]:
            self.assertIn(text, report)
        self.assertNotIn("内部必然优于外部", report.replace("不支持任何“内部必然优于外部”", ""))


if __name__ == "__main__":
    unittest.main()

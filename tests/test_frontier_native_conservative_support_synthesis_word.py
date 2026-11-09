import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_native_conservative_support_synthesis_word.py"
FIGURE = ROOT / "papers/62_三模型保守支撑综合/fig62_native_conservative_support_synthesis.png"


class FrontierNativeConservativeSupportSynthesisWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing conservative-support synthesis Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_native_conservative_support_synthesis_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十五阶段：三模型保守支撑与局部收紧综合\n\n**日期**：2026-11-09  \n\n公式 \\(N\\)。\n\n图：`papers/62_三模型保守支撑综合/fig62_native_conservative_support_synthesis.png`。\n"
        result = module.prepare_native_conservative_support_synthesis_markdown(source)
        self.assertIn("![](papers/62_三模型保守支撑综合/fig62_native_conservative_support_synthesis.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 3, "images": 1, "tables": 5})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 3)
            self.assertEqual(document.count(b"<m:oMath>"), 3)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counts_unavailable_fold_and_scope(self):
        self.load_builder()
        report = (ROOT / "docs/NATIVE_CONSERVATIVE_SUPPORT_SYNTHESIS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["210", "79", "131", "964", "0.256540", "0.690796", "20.935448", "0.700859", "4.371402", "不是概率覆盖率", "没有统一稳定性评分", "不是全局最优", "第 5 折仍有 5 个不可用点"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明全局最优", report)
        self.assertNotIn("统一稳定性评分为", report)


if __name__ == "__main__":
    unittest.main()

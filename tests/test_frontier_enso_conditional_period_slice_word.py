import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_enso_conditional_period_slice_word.py"
FIGURE = ROOT / "papers/57_ENSO条件周期切片界/fig57_enso_conditional_period_slice_bounds.png"


class FrontierEnsoConditionalPeriodSliceWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing conditional-period slice Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_enso_conditional_period_slice_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十阶段：ENSO 条件周期切片联合支撑与全域反例\n\n**日期**：2026-11-09  \n\n公式 \\(S\\)。\n\n图：`papers/57_ENSO条件周期切片界/fig57_enso_conditional_period_slice_bounds.png`。\n"
        result = module.prepare_enso_conditional_period_slice_markdown(source)
        self.assertIn("![](papers/57_ENSO条件周期切片界/fig57_enso_conditional_period_slice_bounds.png)", result)
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

    def test_report_preserves_tightening_witnesses_and_slice_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ENSO_CONDITIONAL_PERIOD_SLICE_BOUNDS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["199", "95", "0.319840", "13.283611", "2.341691", "b4_minus", "x=134", "672／672", "第 3 折没有候选越界也不证明全域安全", "不是边际系数协方差", "原坐标公式修正已单独保留", "默认优化器未达原容差、认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明所有月份切片界均可全域使用", report)
        self.assertNotIn("四个方向已经给出全局最优", report)


if __name__ == "__main__":
    unittest.main()

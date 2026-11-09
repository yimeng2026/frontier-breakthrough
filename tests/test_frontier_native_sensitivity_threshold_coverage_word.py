import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_native_sensitivity_threshold_coverage_word.py"
FIGURE = ROOT / "papers/50_三模型敏感度阈值覆盖/fig50_native_sensitivity_threshold_coverage.png"


class FrontierNativeSensitivityThresholdCoverageWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing sensitivity coverage Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_native_sensitivity_threshold_coverage_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十三阶段：三模型局部敏感度固定阈值覆盖审计\n\n**日期**：2026-11-09  \n\n公式 \\(C_i(k)\\)。\n\n图：`papers/50_三模型敏感度阈值覆盖/fig50_native_sensitivity_threshold_coverage.png`。\n"
        result = module.prepare_native_sensitivity_threshold_coverage_markdown(source)
        self.assertIn("![](papers/50_三模型敏感度阈值覆盖/fig50_native_sensitivity_threshold_coverage.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 1, "images": 1, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 1)
            self.assertEqual(document.count(b"<m:oMath>"), 1)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counts_aggregation_counterexamples_and_scope(self):
        self.load_builder()
        report = (ROOT / "docs/NATIVE_SENSITIVITY_THRESHOLD_COVERAGE_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["85／322", "181／226", "283／124", "25.724483", "0.739369", "5／5", "11.958800", "最大局部敏感度与最大实际残差不必发生在同一点", "不是概率、期望覆盖率或模型间统一评分", "小于 1 的折级比值不能证明逐点安全、周期安全或校准"]:
            self.assertIn(text, report)
        self.assertNotIn("概率覆盖率已校准", report)


if __name__ == "__main__":
    unittest.main()

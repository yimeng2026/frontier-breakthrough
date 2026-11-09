import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_chwirut1_native_identifiability_word.py"
FIGURE = ROOT / "papers/47_Chwirut1原生参数可识别性/fig47_chwirut1_native_identifiability.png"


class FrontierChwirut1NativeIdentifiabilityWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Chwirut1 native identifiability Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_chwirut1_native_identifiability_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十阶段：Chwirut1 原生参数可识别性与分母诊断\n\n**日期**：2026-11-09  \n\n公式 \\(J_i\\)。\n\n图：`papers/47_Chwirut1原生参数可识别性/fig47_chwirut1_native_identifiability.png`。\n"
        result = module.prepare_chwirut1_native_identifiability_markdown(source)
        self.assertIn("![](papers/47_Chwirut1原生参数可识别性/fig47_chwirut1_native_identifiability.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 2, "images": 1, "tables": 6})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertEqual(document.count(b"<m:oMath>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_fold1_related_scope_and_proof_boundaries(self):
        self.load_builder()
        report = (ROOT / "docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["154、157、160、188、182", "28.674083", "0.979413", "14.836682", "0.009384279", "1.710628", "极点都位于观测距离范围之外", "不是独立模型族或独立实验室复现", "不能据此生成校准误差棒", "没有调用 `curve_fit`"]:
            self.assertIn(text, report)
        self.assertNotIn("已证明全局可识别", report.split("禁止推断")[0])


if __name__ == "__main__":
    unittest.main()

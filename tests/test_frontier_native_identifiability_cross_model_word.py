import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_native_identifiability_cross_model_word.py"
FIGURE = ROOT / "papers/49_三模型局部可识别性综合/fig49_native_identifiability_cross_model.png"


class FrontierNativeIdentifiabilityCrossModelWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing cross-model identifiability Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_native_identifiability_cross_model_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十二阶段：三模型局部可识别性受限综合\n\n**日期**：2026-11-09  \n\n公式 \\(R_{d,k}\\)。\n\n图：`papers/49_三模型局部可识别性综合/fig49_native_identifiability_cross_model.png`。\n"
        result = module.prepare_native_identifiability_cross_model_markdown(source)
        self.assertIn("![](papers/49_三模型局部可识别性综合/fig49_native_identifiability_cross_model.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 1, "images": 1, "tables": 5})
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

    def test_report_preserves_ratio_counterexamples_and_no_pooling_scope(self):
        self.load_builder()
        report = (ROOT / "docs/NATIVE_IDENTIFIABILITY_CROSS_MODEL_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["15／15", "2.697264", "1.025658", "0.446846", "Roszman1 第 5 折", "ENSO 第 4 折", "不合并残差、协方差、参数值或条件数", "不是覆盖率、误差概率或校准分数", "同研究同模型族", "认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("统一稳定性评分已建立", report)


if __name__ == "__main__":
    unittest.main()

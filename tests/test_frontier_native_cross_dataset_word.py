import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_native_cross_dataset_word.py"
FIGURE = ROOT / "papers/45_三数据原生同折综合/fig45_native_cross_dataset_synthesis.png"


class FrontierNativeCrossDatasetWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native cross-dataset Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_native_cross_dataset_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十八阶段：三数据原生模型同折对照综合\n\n**日期**：2026-11-09  \n\n公式 \\(r_{d,k}\\)。\n\n图：`papers/45_三数据原生同折综合/fig45_native_cross_dataset_synthesis.png`。\n"
        result = module.prepare_native_cross_dataset_markdown(source)
        self.assertIn("![](papers/45_三数据原生同折综合/fig45_native_cross_dataset_synthesis.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 7, "images": 1, "tables": 6})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 3)
            self.assertEqual(document.count(b"<m:oMath>"), 7)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counterexamples_and_pooling_boundaries(self):
        self.load_builder()
        report = (ROOT / "docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["11／15", "10／3／2", "12／25", "13／25", "256／407", "151／407", "Roszman1：第 4 折", "有理更低", "18 个", "不匹配数为 0", "不把残差、平方误差或参数合成一个跨数据总指标", "没有重新拟合", "不能继承有理证书"]:
            self.assertIn(text, report)
        self.assertNotIn("原生模型全面最优", report)


if __name__ == "__main__":
    unittest.main()

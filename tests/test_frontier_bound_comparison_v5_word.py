import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_bound_comparison_v5_word.py"
FIGURES = [
    ROOT / "papers/36_外部七组界组成/fig36_external_bound_decomposition_v5.png",
    ROOT / "papers/37_十组界组成对照/fig37_internal_external_bound_comparison_v5.png",
]


class FrontierBoundComparisonV5WordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v5 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_bound_comparison_v5_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_two_figures_in_order(self):
        module = self.load_builder()
        source = "# 前沿共生第三十阶段：七外部与十组界组成对照\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/36_外部七组界组成/fig36_external_bound_decomposition_v5.png`。\n\n图：`papers/37_十组界组成对照/fig37_internal_external_bound_comparison_v5.png`。\n"
        result = module.prepare_bound_comparison_v5_markdown(source)
        first = result.index("![](papers/36_外部七组界组成/fig36_external_bound_decomposition_v5.png)")
        second = result.index("![](papers/37_十组界组成对照/fig37_internal_external_bound_comparison_v5.png)")
        self.assertLess(first, second)
        self.assertIn("顺序第 1 幅，共 2 幅", result)
        self.assertIn("顺序第 2 幅，共 2 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_both_exact_figures_and_native_content(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 2, "images": 2, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 2)
            embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media}
            source_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in FIGURES}
            self.assertEqual(embedded_hashes, source_hashes)
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_new_counts_and_small_sample_counterexample(self):
        self.load_builder()
        report = (ROOT / "docs/BOUND_COMPARISON_V5_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["786", "532", "254", "901", "599", "+20", "0.997834", "十组最大界中九组由平移主导，ENSO 由实际残差主导", "不计算成功率", "原生四参数反正切模型", "全部位于第 2 折"]:
            self.assertIn(text, report)
        self.assertIn("exports/external-bound-decomposition-v4.json", report)
        self.assertIn("internal-external-bound-comparison-v5.json", report)
        self.assertNotIn("十组最大界仍都由平移主导", report)


if __name__ == "__main__":
    unittest.main()

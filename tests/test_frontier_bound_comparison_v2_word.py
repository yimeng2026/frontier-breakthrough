import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_bound_comparison_v2_word.py"
FIGURES = [
    ROOT / "papers/26_外部四组界组成/fig26_external_bound_decomposition_v2.png",
    ROOT / "papers/27_七组界组成对照/fig27_internal_external_bound_comparison_v2.png",
]


class FrontierBoundComparisonV2WordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_bound_comparison_v2_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_two_figures_in_order(self):
        module = self.load_builder()
        source = "# 前沿共生第二十一阶段：四外部与七组界组成对照\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/26_外部四组界组成/fig26_external_bound_decomposition_v2.png`。\n\n图：`papers/27_七组界组成对照/fig27_internal_external_bound_comparison_v2.png`。\n"
        result = module.prepare_bound_comparison_v2_markdown(source)
        first = result.index("![](papers/26_外部四组界组成/fig26_external_bound_decomposition_v2.png)")
        second = result.index("![](papers/27_七组界组成对照/fig27_internal_external_bound_comparison_v2.png)")
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

    def test_report_preserves_versions_and_scope_differences(self):
        self.load_builder()
        report = (ROOT / "docs/BOUND_COMPARISON_V2_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["379", "309", "678", "+10", "+4", "0.999612", "不计算成功率", "旧文件"]:
            self.assertIn(text, report)
        self.assertIn("exports/external-bound-decomposition.json", report)
        self.assertIn("internal-external-bound-comparison-v2.json", report)


if __name__ == "__main__":
    unittest.main()

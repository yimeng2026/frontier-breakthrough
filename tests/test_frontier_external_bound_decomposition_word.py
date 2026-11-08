import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_external_bound_decomposition_word.py"
FIGURE = ROOT / "papers/22_外部界组成对照/fig22_external_bound_decomposition.png"


class FrontierExternalBoundDecompositionWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing bound-decomposition Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_external_bound_decomposition_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第十八阶段：三数据界组成对照与机制异质性\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/22_外部界组成对照/fig22_external_bound_decomposition.png`。\n"
        result = module.prepare_external_bound_decomposition_markdown(source)
        self.assertIn("![](papers/22_外部界组成对照/fig22_external_bound_decomposition.png)", result)
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

    def test_report_preserves_dataset_heterogeneity_and_limits(self):
        self.load_builder()
        report = (ROOT / "docs/EXTERNAL_BOUND_DECOMPOSITION_2026-11-09.md").read_text(encoding="utf-8")
        self.assertIn("0.992109", report)
        self.assertIn("0.169474", report)
        self.assertIn("138", report)
        self.assertIn("167", report)
        self.assertIn("不是概率贡献", report)
        self.assertNotIn("所有数据集均由预测平移主导", report)


if __name__ == "__main__":
    unittest.main()

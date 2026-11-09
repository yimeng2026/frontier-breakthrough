import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_chwirut1_native_holdout_word.py"
FIGURE = ROOT / "papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png"


class FrontierChwirut1NativeHoldoutWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native Chwirut1 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_chwirut1_native_holdout_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十五阶段：Chwirut1 原生指数模型同折对照\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png`。\n"
        result = module.prepare_chwirut1_native_holdout_markdown(source)
        self.assertIn("![](papers/42_Chwirut1原生指数对照/fig42_chwirut1_native_holdout.png)", result)
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

    def test_report_preserves_counts_fold_losses_and_related_scope(self):
        self.load_builder()
        report = (ROOT / "docs/CHWIRUT1_NATIVE_HOLDOUT_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["57", "54", "51", "23", "29", "7.778996", "9.456158", "第 2 折", "同研究、同原生模型族", "0.005195445", "不伪造其 214 点汇总", "没有继承有理模型的证明区域"]:
            self.assertIn(text, report)
        self.assertNotIn("原生指数模型全面最优", report)


if __name__ == "__main__":
    unittest.main()

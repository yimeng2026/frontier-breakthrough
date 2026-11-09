import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_fold4_decomposition_word.py"
FIGURE = ROOT / "papers/46_Roszman1第4折误差分解/fig46_roszman1_fold4_error_decomposition.png"


class FrontierRoszman1Fold4DecompositionWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Roszman1 fold-4 Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_fold4_decomposition_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十九阶段：Roszman1 第 4 折误差贡献分解\n\n**日期**：2026-11-09  \n\n公式 \\(\\delta_i\\)。\n\n图：`papers/46_Roszman1第4折误差分解/fig46_roszman1_fold4_error_decomposition.png`。\n"
        result = module.prepare_roszman1_fold4_decomposition_markdown(source)
        self.assertIn("![](papers/46_Roszman1第4折误差分解/fig46_roszman1_fold4_error_decomposition.png)", result)
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

    def test_report_preserves_all_five_points_and_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["+0.000461975122", "-1.317350031e-5", "4.32 倍", "移除第 4 或第 5 点", "没有任何单点移除", "逐点方向不一致数为 0", "9.32e-21", "不是五个新模型", "不重新训练模型", "不是显著性"]:
            self.assertIn(text, report)
        self.assertNotIn("原生模型全面最优", report)


if __name__ == "__main__":
    unittest.main()

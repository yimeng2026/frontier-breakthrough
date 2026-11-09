import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_whitened_grid_convergence_word.py"
FIGURE = ROOT / "papers/66_Roszman1白化网格收敛与共享见证/fig66_roszman1_whitened_grid_convergence.png"


class FrontierRoszman1WhitenedGridConvergenceWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing whitened-grid convergence Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_whitened_grid_convergence_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十九阶段：Roszman1 白化网格增量诊断与共享极值见证\n\n**日期**：2026-11-09  \n\n公式 \\(R\\)。\n\n图：`papers/66_Roszman1白化网格收敛与共享见证/fig66_roszman1_whitened_grid_convergence.png`。\n"
        result = module.prepare_roszman1_whitened_grid_convergence_markdown(source)
        self.assertIn("![](papers/66_Roszman1白化网格收敛与共享见证/fig66_roszman1_whitened_grid_convergence.png)", result)
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

    def test_report_preserves_incremental_results_witnesses_and_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_WHITENED_GRID_CONVERGENCE_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["81920", "51520", "30400", "0.587495", "0.046398005", "0.588036", "44", "596", "平台不是全局收敛证明", "不是渐近误差界", "第 5 折", "0.026678028"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明渐近收敛或全局最优", report)
        self.assertNotIn("所有顶点都是可行极值", report)


if __name__ == "__main__":
    unittest.main()

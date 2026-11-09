import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_whitened_cover_grid_word.py"
FIGURE = ROOT / "papers/65_Roszman1协方差白化覆盖/fig65_roszman1_whitened_cover_grid.png"


class FrontierRoszman1WhitenedCoverGridWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing whitened-cover Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_whitened_cover_grid_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十八阶段：Roszman1 协方差白化覆盖与全预测区间\n\n**日期**：2026-11-09  \n\n公式 \\(u\\)。\n\n图：`papers/65_Roszman1协方差白化覆盖/fig65_roszman1_whitened_cover_grid.png`。\n"
        result = module.prepare_roszman1_whitened_cover_grid_markdown(source)
        self.assertIn("![](papers/65_Roszman1协方差白化覆盖/fig65_roszman1_whitened_cover_grid.png)", result)
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

    def test_report_preserves_tightening_boundary_amendment_and_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_WHITENED_COVER_GRID_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["5460", "20／20", "0.820643", "0.090006515", "600／600", "第 5 折", "16.000000000000007", "不是精确全局最优", "第 1 层全部保持", "未决为 0"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明精确全局最优", report)
        self.assertNotIn("本阶段三层网格全部收紧", report)


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_chwirut1_log_support_word.py"
FIGURE = ROOT / "papers/60_Chwirut1对数支撑交集/fig60_chwirut1_log_support_intersection.png"


class FrontierChwirut1LogSupportWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Chwirut1 log-support Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_chwirut1_log_support_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十三阶段：Chwirut1 对数支撑与保守交集\n\n**日期**：2026-11-09  \n\n公式 \\(L\\)。\n\n图：`papers/60_Chwirut1对数支撑交集/fig60_chwirut1_log_support_intersection.png`。\n"
        result = module.prepare_chwirut1_log_support_markdown(source)
        self.assertIn("![](papers/60_Chwirut1对数支撑交集/fig60_chwirut1_log_support_intersection.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 4, "images": 1, "tables": 5})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 4)
            self.assertEqual(document.count(b"<m:oMath>"), 4)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_tightening_candidates_and_model_scope(self):
        self.load_builder()
        report = (ROOT / "docs/CHWIRUT1_LOG_SUPPORT_INTERSECTION_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["22／22", "0.256540", "20.935448", "132／132", "214／214", "d_max", "不是全局最优", "Chwirut2 同研究同模型族", "不改变原生模型", "候选检查不替代解析证明"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明所有参数和所有距离都获得证明", report)
        self.assertNotIn("候选评价证明全局最优", report)


if __name__ == "__main__":
    unittest.main()

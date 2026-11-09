import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_enso_phase_interval_triple_word.py"
FIGURE = ROOT / "papers/59_ENSO三角区间三重交集/fig59_enso_phase_interval_triple_intersection.png"


class FrontierEnsoPhaseIntervalTripleWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing phase-interval triple Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_enso_phase_interval_triple_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十二阶段：ENSO 精确三角区间余项与三重交集\n\n**日期**：2026-11-09  \n\n公式 \\(R\\)。\n\n图：`papers/59_ENSO三角区间三重交集/fig59_enso_phase_interval_triple_intersection.png`。\n"
        result = module.prepare_enso_phase_interval_triple_markdown(source)
        self.assertIn("![](papers/59_ENSO三角区间三重交集/fig59_enso_phase_interval_triple_intersection.png)", result)
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

    def test_report_preserves_local_gains_width_mismatch_and_proof_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ENSO_PHASE_INTERVAL_TRIPLE_INTERSECTION_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["37", "131", "29", "0.747409", "4.371402", "x=25", "672／672", "不是全局最优", "临界点全部枚举", "相位替代界更宽但三重交集仍收紧的 8 个月份", "默认优化器未达原容差、认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明三重交集在所有月份都收紧", report)
        self.assertNotIn("本阶段候选评价证明全局最优", report)


if __name__ == "__main__":
    unittest.main()

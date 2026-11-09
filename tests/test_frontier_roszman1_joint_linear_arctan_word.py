import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_joint_linear_arctan_word.py"
FIGURE = ROOT / "papers/61_Roszman1联合线性反正切交集/fig61_roszman1_joint_linear_arctan_intersection.png"


class FrontierRoszman1JointLinearArctanWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Roszman1 joint-linear Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_joint_linear_arctan_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十四阶段：Roszman1 联合线性支撑与反正切交集\n\n**日期**：2026-11-09  \n\n公式 \\(A\\)。\n\n图：`papers/61_Roszman1联合线性反正切交集/fig61_roszman1_joint_linear_arctan_intersection.png`。\n"
        result = module.prepare_roszman1_joint_linear_arctan_markdown(source)
        self.assertIn("![](papers/61_Roszman1联合线性反正切交集/fig61_roszman1_joint_linear_arctan_intersection.png)", result)
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

    def test_report_preserves_tightening_unavailable_fold_and_proof_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_JOINT_LINEAR_ARCTAN_INTERSECTION_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["20／20", "0.690796", "0.700859", "160／160", "第 5 折没有有限包络", "不是完整非线性最优", "b1−b2x", "候选检查不替代支撑证明", "0.191899"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明第 5 折获得有限包络", report)
        self.assertNotIn("本阶段候选评价证明全局最优", report)


if __name__ == "__main__":
    unittest.main()

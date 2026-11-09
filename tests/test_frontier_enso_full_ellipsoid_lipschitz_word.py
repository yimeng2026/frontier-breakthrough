import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_enso_full_ellipsoid_lipschitz_word.py"
FIGURE = ROOT / "papers/58_ENSO全椭球Lipschitz交集/fig58_enso_full_ellipsoid_lipschitz_intersection.png"


class FrontierEnsoFullEllipsoidLipschitzWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing full-ellipsoid Lipschitz Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_enso_full_ellipsoid_lipschitz_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第五十一阶段：ENSO 全椭球 Lipschitz 保守界与交集收紧\n\n**日期**：2026-11-09  \n\n公式 \\(D\\)。\n\n图：`papers/58_ENSO全椭球Lipschitz交集/fig58_enso_full_ellipsoid_lipschitz_intersection.png`。\n"
        result = module.prepare_enso_full_ellipsoid_lipschitz_markdown(source)
        self.assertIn("![](papers/58_ENSO全椭球Lipschitz交集/fig58_enso_full_ellipsoid_lipschitz_intersection.png)", result)
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

    def test_report_preserves_local_tightening_unchanged_cases_and_proof_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ENSO_FULL_ELLIPSOID_LIPSCHITZ_INTERSECTION_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["13", "155", "0.535904", "8.086192", "672／672", "不是所有月份都收紧", "不是联合全域最优", "候选检查不是全局证明", "第 2—5 折没有交集收紧", "默认优化器未达原容差、认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("本阶段证明交集在所有月份都收紧", report)
        self.assertNotIn("本阶段候选评价证明全局最优", report)


if __name__ == "__main__":
    unittest.main()

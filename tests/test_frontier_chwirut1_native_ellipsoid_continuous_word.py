import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_chwirut1_native_ellipsoid_continuous_word.py"
FIGURE = ROOT / "papers/51_Chwirut1原生椭球连续界/fig51_chwirut1_native_ellipsoid_continuous_bounds.png"


class FrontierChwirut1NativeEllipsoidContinuousWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing native ellipsoid Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_chwirut1_native_ellipsoid_continuous_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十四阶段：Chwirut1 原生椭球连续分母与保守预测界\n\n**日期**：2026-11-09  \n\n公式 \\(E\\)。\n\n图：`papers/51_Chwirut1原生椭球连续界/fig51_chwirut1_native_ellipsoid_continuous_bounds.png`。\n"
        result = module.prepare_chwirut1_native_ellipsoid_continuous_markdown(source)
        self.assertIn("![](papers/51_Chwirut1原生椭球连续界/fig51_chwirut1_native_ellipsoid_continuous_bounds.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 4, "images": 1, "tables": 4})
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

    def test_report_preserves_continuous_scope_width_and_center_boundary(self):
        self.load_builder()
        report = (ROOT / "docs/CHWIRUT1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["0.004322622", "170.146309", "19.222110", "165.679602", "62.233292，232.379602", "214／214 不能被写成概率覆盖率", "没有 Taylor 模型替换", "不是精确有理代数证明", "同研究同模型族", "不可用折数为 0"]:
            self.assertIn(text, report)
        self.assertNotIn("所有参数和所有距离均已证明安全", report)


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_enso_native_ellipsoid_radius_sensitivity_word.py"
FIGURE = ROOT / "papers/55_ENSO原生椭球半径敏感性/fig55_enso_native_ellipsoid_radius_sensitivity.png"


class FrontierEnsoNativeEllipsoidRadiusSensitivityWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing ENSO radius-sensitivity Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_enso_native_ellipsoid_radius_sensitivity_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十八阶段：ENSO 原生椭球半径敏感性与正周期失效边界\n\n**日期**：2026-11-09  \n\n公式 \\(\\rho\\)。\n\n图：`papers/55_ENSO原生椭球半径敏感性/fig55_enso_native_ellipsoid_radius_sensitivity.png`。\n"
        result = module.prepare_enso_native_ellipsoid_radius_sensitivity_markdown(source)
        self.assertIn("![](papers/55_ENSO原生椭球半径敏感性/fig55_enso_native_ellipsoid_radius_sensitivity.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 2, "images": 1, "tables": 5})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertEqual(document.count(b"<m:oMath>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counts_failures_baseline_and_width_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ENSO_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["1008", "942", "66", "141.135435", "109.854012", "75.547321", "26.766839", "enso:4:r32", "enso:5:r32", "5／5", "原协议未改写", "不是联合非线性最优界", "默认优化器未达原容差、认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("所有半径下五折均获得正周期证明", report)
        self.assertNotIn("选择最优半径", report)


if __name__ == "__main__":
    unittest.main()

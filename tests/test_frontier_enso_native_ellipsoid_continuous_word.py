import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_enso_native_ellipsoid_continuous_word.py"
FIGURE = ROOT / "papers/54_ENSO原生椭球连续界/fig54_enso_native_ellipsoid_continuous_bounds.png"


class FrontierEnsoNativeEllipsoidContinuousWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing ENSO ellipsoid Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_enso_native_ellipsoid_continuous_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十七阶段：ENSO 原生 Fourier 正周期与连续预测包络\n\n**日期**：2026-11-09  \n\n公式 \\(\\rho\\)。\n\n图：`papers/54_ENSO原生椭球连续界/fig54_enso_native_ellipsoid_continuous_bounds.png`。\n"
        result = module.prepare_enso_native_ellipsoid_continuous_markdown(source)
        self.assertIn("![](papers/54_ENSO原生椭球连续界/fig54_enso_native_ellipsoid_continuous_bounds.png)", result)
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
            from lxml import etree
            root = etree.fromstring(document)
            namespaces = {"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
            columns = root.xpath(".//m:mcPr", namespaces=namespaces)
            self.assertEqual(len(columns), 4)
            for properties in columns:
                self.assertEqual([etree.QName(child).localname for child in properties], ["count", "mcJc"])
            self.assertEqual(len(root.xpath("(.//m:oMathPara)[2]//m:m/m:mr", namespaces=namespaces)), 4)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_positive_period_width_and_center_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ENSO_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["26.766839", "168／168", "17.641929", "13.164436", "14.576766", "8.516812", "不能被写成概率覆盖率、外部实验验证或模型真实性证明", "没有固定周期或 Taylor 替换", "采用 80 位精度和外向数值舍入", "默认优化器未达原容差、认证参数前向通过"]:
            self.assertIn(text, report)
        self.assertNotIn("所有周期和所有月份均获得证明", report)


if __name__ == "__main__":
    unittest.main()

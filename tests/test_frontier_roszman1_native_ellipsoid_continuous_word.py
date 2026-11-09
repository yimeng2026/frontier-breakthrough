import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_roszman1_native_ellipsoid_continuous_word.py"
FIGURE = ROOT / "papers/53_Roszman1原生椭球奇异界/fig53_roszman1_native_ellipsoid_continuous_bounds.png"


class FrontierRoszman1NativeEllipsoidContinuousWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Roszman1 ellipsoid Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_roszman1_native_ellipsoid_continuous_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第四十六阶段：Roszman1 原生反正切椭球奇异证书与预测界\n\n**日期**：2026-11-09  \n\n公式 \\(d_{\\min}(x)\\)。\n\n图：`papers/53_Roszman1原生椭球奇异界/fig53_roszman1_native_ellipsoid_continuous_bounds.png`。\n"
        result = module.prepare_roszman1_native_ellipsoid_continuous_markdown(source)
        self.assertIn("![](papers/53_Roszman1原生椭球奇异界/fig53_roszman1_native_ellipsoid_continuous_bounds.png)", result)
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

    def test_report_preserves_unavailable_fold_width_and_center_scope(self):
        self.load_builder()
        report = (ROOT / "docs/ROSZMAN1_NATIVE_ELLIPSOID_CONTINUOUS_BOUNDS_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["2.828351", "+103.088753", "0.867292", "0.443391", "20／20", "5 个不可用点", "不能被写成概率覆盖率、外部实验验证或模型真实性证明", "采用 80 位精度和外向数值舍入", "没有 Taylor 替换", "第 5 折虽然实际 RMSE 最低"]:
            self.assertIn(text, report)
        self.assertNotIn("半径 4 全部折通过", report)


if __name__ == "__main__":
    unittest.main()

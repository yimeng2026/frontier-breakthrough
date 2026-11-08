import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_gauss1_bound_mechanism_word.py"
FIGURE = ROOT / "papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png"


class FrontierGauss1BoundMechanismWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing mechanism Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_gauss1_bound_mechanism_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第十七阶段：Gauss1 界失效机制与同点误差分解\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png`。\n"
        result = module.prepare_gauss1_bound_mechanism_markdown(source)
        self.assertIn("![](papers/21_Gauss1界失效机制/fig21_gauss1_bound_mechanism.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 9, "images": 1, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_decomposition_and_unavailable_scope(self):
        self.load_builder()
        report = (ROOT / "docs/GAUSS1_BOUND_MECHANISM_2026-11-09.md").read_text(encoding="utf-8")
        self.assertIn("97.561%", report)
        self.assertIn("0.688%", report)
        self.assertIn("不适用（无可用界）", report)
        self.assertIn("不把未认证称为已证明不安全", report)
        self.assertNotIn("250 点全部覆盖", report)


if __name__ == "__main__":
    unittest.main()

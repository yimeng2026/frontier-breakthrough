import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_repository_integrity_word.py"
FIGURE = ROOT / "papers/44_仓库完整性审计/fig44_repository_integrity.png"


class FrontierRepositoryIntegrityWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing repository integrity Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_repository_integrity_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十七阶段：全仓库一致性审计\n\n**日期**：2026-11-09  \n\n公式 \\(H(x)\\)。\n\n图：`papers/44_仓库完整性审计/fig44_repository_integrity.png`。\n"
        result = module.prepare_repository_integrity_markdown(source)
        self.assertIn("![](papers/44_仓库完整性审计/fig44_repository_integrity.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 1, "images": 1, "tables": 5})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 1)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counts_boundaries_and_negative_gates(self):
        self.load_builder()
        report = (ROOT / "docs/REPOSITORY_INTEGRITY_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["84", "44", "36", "161", "184", "407", "23", "22", "10 份、24 个输入记录", "不是科学真实性认证", "不是视觉渲染验收", "external_web_checked=false"]:
            self.assertIn(text if text != "external_web_checked=false" else "未进行外部联网核查", report)
        self.assertIn("scripts/audit_repository_integrity.py", report)


if __name__ == "__main__":
    unittest.main()

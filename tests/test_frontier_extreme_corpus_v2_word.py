import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_extreme_corpus_v2_word.py"
FIGURE = ROOT / "papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png"


class FrontierExtremeCorpusV2WordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 corpus Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_extreme_corpus_v2_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十六阶段：极值相关报告全集分级（第二版）\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png`。\n"
        result = module.prepare_extreme_corpus_v2_markdown(source)
        self.assertIn("![](papers/43_极值全集分级V2/fig43_extreme_corpus_v2.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("图：`papers/", result)

    def test_final_word_has_exact_figure_native_math_and_tables(self):
        module = self.load_builder()
        from build_total_word import audit_docx_package
        self.assertTrue(module.OUTPUT.is_file(), module.OUTPUT)
        self.assertEqual(audit_docx_package(module.OUTPUT, module.EXPECTED), [])
        self.assertEqual(module.EXPECTED, {"math": 2, "images": 1, "tables": 4})
        with zipfile.ZipFile(module.OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            document = archive.read("word/document.xml")
            self.assertEqual(document.count(b"<m:oMathPara>"), 2)
            self.assertIn(b"TOC", document)
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)

    def test_report_preserves_counts_classes_and_historical_files(self):
        self.load_builder()
        report = (ROOT / "docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md").read_text(encoding="utf-8")
        for text in ["23 份", "12 份", "7 份", "4 份", "22 份非接口文档哈希匹配", "旧 10 份联读原文未变", "原始 Markdown 与旧 Word 均不改写", "complete` 只表示文档包含其当前主张所需证据，不表示物理理论为真"]:
            self.assertIn(text, report)
        self.assertIn("docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md", report)
        self.assertIn("docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md", report)

    def test_word_gate_uses_v2_validator_and_rejects_incomplete_corpus(self):
        module = self.load_builder()
        saved = module.configure()
        try:
            module.base.enforce_extreme_reporting_gate()
            with self.assertRaises(ValueError):
                module.base.enforce_extreme_reporting_gate(corpus_text="")
        finally:
            module.restore(saved)


if __name__ == "__main__":
    unittest.main()

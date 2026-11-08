import hashlib
import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_extreme_reporting_word.py"
FIGURE = ROOT / "papers/34_最大界与全点组成/fig34_maximum_full_composition.png"


class FrontierExtremeReportingWordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing extreme reporting Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_extreme_reporting_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第二十七阶段：极值报告的分层写作与验收协议\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/34_最大界与全点组成/fig34_maximum_full_composition.png`。\n"
        result = module.prepare_extreme_reporting_markdown(source)
        self.assertIn("![](papers/34_最大界与全点组成/fig34_maximum_full_composition.png)", result)
        self.assertIn("顺序第 1 幅，共 1 幅", result)
        self.assertIn('date: "2026-11-09"', result)

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

    def test_protocol_defines_three_levels_and_prohibitions(self):
        self.load_builder()
        report = (ROOT / "docs/EXTREME_REPORTING_PROTOCOL.md").read_text(encoding="utf-8")
        for text in ["L0", "L1", "L2", "最大点不是典型点", "描述性百分位", "bound_max_to_median_ratio", "mechanism_interpretation"]:
            self.assertIn(text, report)


if __name__ == "__main__":
    unittest.main()

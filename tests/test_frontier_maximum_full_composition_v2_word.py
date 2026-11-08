import hashlib
import importlib.util
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_frontier_maximum_full_composition_v2_word.py"
FIGURE = ROOT / "papers/38_十组最大界与全点组成/fig38_maximum_full_composition_v2.png"


class FrontierMaximumFullCompositionV2WordTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 maximum/full composition Word builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_frontier_maximum_full_composition_v2_word", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_prepare_inserts_figure_and_source_date(self):
        module = self.load_builder()
        source = "# 前沿共生第三十一阶段：十组最大界与全点组成审计\n\n**日期**：2026-11-09  \n\n公式 \\(x\\)。\n\n图：`papers/38_十组最大界与全点组成/fig38_maximum_full_composition_v2.png`。\n"
        result = module.prepare_maximum_full_composition_v2_markdown(source)
        self.assertIn("![](papers/38_十组最大界与全点组成/fig38_maximum_full_composition_v2.png)", result)
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

    def test_report_separates_small_sample_percentile_and_probability(self):
        self.load_builder()
        report = (ROOT / "docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md").read_text(encoding="utf-8")
        for text in ["9／10", "6 组", "82.994", "13.33%", "1.220322", "100.00%", "只位于第 2 折", "不是 25 点概率覆盖", "不把最大点称为典型点"]:
            self.assertIn(text, report)
        self.assertIn("exports/maximum-full-composition-audit.json", report)
        self.assertNotIn("最大点代表典型机制", report)

    def test_word_gate_uses_v2_report_and_rejects_bad_claims(self):
        module = self.load_builder()
        saved = module.configure()
        try:
            module.base.enforce_extreme_reporting_gate()
            summary = json.loads((ROOT / "exports/maximum-full-composition-audit-v2.json").read_text(encoding="utf-8"))
            summary["decision"]["maximum_point_used_as_typical_claimed"] = True
            with self.assertRaises(ValueError):
                module.base.enforce_extreme_reporting_gate(summary)
        finally:
            module.restore(saved)


if __name__ == "__main__":
    unittest.main()

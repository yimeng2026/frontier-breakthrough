import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_cross_dataset_word import EXPECTED, OUTPUT, prepare_cross_dataset_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png"


class FrontierCrossDatasetWordTests(unittest.TestCase):
    def test_prepare_inserts_cross_dataset_figure_and_caption(self):
        source = "# 前沿共生第八阶段：有理模型统一验收内核与跨数据集综合\n\n公式 \\(f(x)=N(x)/D(x)\\)。\n\n图：`papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png`。\n"
        result = prepare_cross_dataset_markdown(source)
        self.assertIn("![](papers/12_跨数据集验收综合/fig12_rational_cross_dataset.png)", result)
        self.assertIn("**图 12｜有理模型跨数据集统一验收综合**", result)
        self.assertIn("§4「三个数据集的整体结果」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn("统一诊断内核、13／15 折验收与证据等级边界", result)
        self.assertNotIn("图：`papers/", result)

    def test_prepare_uses_source_date_and_schema_safe_math(self):
        source = (ROOT / "docs/CROSS_DATASET_2026-11-09.md").read_text(encoding="utf-8")
        result = prepare_cross_dataset_markdown(source)
        self.assertIn('date: "2026-11-09"', result)
        self.assertNotIn("\\text{", result)

    def test_final_cross_dataset_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 2, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_stress_word import EXPECTED, OUTPUT, prepare_stress_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/08_跨数据集压力测试/fig08_grouped_stress.png"


class FrontierStressWordTests(unittest.TestCase):
    def test_prepare_inserts_grouped_stress_figure_and_caption(self):
        source = "# 前沿共生第四阶段：跨数据集压力测试与失效边界\n\n公式 \\(x\\)。\n\n图：`papers/08_跨数据集压力测试/fig08_grouped_stress.png`。\n"
        result = prepare_stress_markdown(source)
        self.assertIn("![](papers/08_跨数据集压力测试/fig08_grouped_stress.png)", result)
        self.assertIn("**图 08｜跨数据集连续区间压力测试**", result)
        self.assertIn("§3「全部 15 折结果」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn("连续区间压力测试、Hahn1 第 1 折失败与稳健性边界", result)
        self.assertIn("\\(x\\)", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_stress_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 3, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            embedded_hash = hashlib.sha256(archive.read(media[0])).hexdigest()
            self.assertEqual(embedded_hash, hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_kirby2_word import EXPECTED, OUTPUT, prepare_kirby2_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png"


class FrontierKirby2WordTests(unittest.TestCase):
    def test_prepare_inserts_kirby2_figure_and_caption(self):
        source = "# 前沿共生第七阶段：Kirby2 跨次数前瞻验收\n\n公式 \\(D(x)=1+b_4x+b_5x^2\\)。\n\n图：`papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png`。\n"
        result = prepare_kirby2_markdown(source)
        self.assertIn("![](papers/11_Kirby2前瞻验收/fig11_kirby2_prospective_gate.png)", result)
        self.assertIn("**图 11｜Kirby2 二次有理模型五折前瞻验收**", result)
        self.assertIn("§5「阳性结果仍需保留的三个边界」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn("二次有理模型、五折有限支持与高条件数边界", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_kirby2_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 9, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

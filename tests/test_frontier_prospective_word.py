import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_prospective_word import EXPECTED, OUTPUT, prepare_prospective_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/10_Thurber前瞻验收/fig10_thurber_prospective_gate.png"


class FrontierProspectiveWordTests(unittest.TestCase):
    def test_prepare_inserts_thurber_figure_and_caption(self):
        source = "# 前沿共生第六阶段：Thurber 数据集前瞻验收\n\n公式 \\(D(x)=1+b_5x+b_6x^2+b_7x^3\\)。\n\n图：`papers/10_Thurber前瞻验收/fig10_thurber_prospective_gate.png`。\n"
        result = prepare_prospective_markdown(source)
        self.assertIn("![](papers/10_Thurber前瞻验收/fig10_thurber_prospective_gate.png)", result)
        self.assertIn("**图 10｜Thurber 数据集前瞻验收：极点、条件数与预测支持**", result)
        self.assertIn("§5「第 1 折失效位置」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn("预测区极点、最低数值可识别性与五折验收", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_prospective_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 13, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

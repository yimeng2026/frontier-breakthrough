import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_frontier_mechanism_word import EXPECTED, OUTPUT, prepare_mechanism_markdown
from build_total_word import audit_docx_package

FIGURE = ROOT / "papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png"


class FrontierMechanismWordTests(unittest.TestCase):
    def test_prepare_inserts_mechanism_figure_and_caption(self):
        source = "# 前沿共生第五阶段：Hahn1 第 1 折失效机制诊断\n\n公式 \\(D(x)=1+b_5x+b_6x^2+b_7x^3\\)。\n\n图：`papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png`。\n"
        result = prepare_mechanism_markdown(source)
        self.assertIn("![](papers/09_Hahn1失效机制/fig09_hahn1_fold1_identifiability.png)", result)
        self.assertIn("**图 09｜Hahn1 第 1 折局部条件、预测敏感度与双极点**", result)
        self.assertIn("§4「失效链条与不可转移的证明」之后；顺序第 1 幅，共 1 幅", result)
        self.assertIn("局部可识别性、两个低温极点与不可转移的分母证明", result)
        self.assertNotIn("图：`papers/", result)

    def test_final_mechanism_word_has_native_content_and_exact_figure(self):
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        self.assertEqual(audit_docx_package(OUTPUT, EXPECTED), [])
        self.assertEqual(EXPECTED, {"math": 14, "images": 1, "tables": 4})
        with zipfile.ZipFile(OUTPUT) as archive:
            media = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            self.assertEqual(len(media), 1)
            self.assertEqual(hashlib.sha256(archive.read(media[0])).hexdigest(), hashlib.sha256(FIGURE.read_bytes()).hexdigest())
            self.assertIn(b"TOC", archive.read("word/document.xml"))
            footer = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn(b"PAGE", footer)


if __name__ == "__main__":
    unittest.main()

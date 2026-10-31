import json
import re
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"


class PaperSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PAPERS / "manifest.json").read_text(encoding="utf-8"))
        cls.texts = {
            item["folder"]: (PAPERS / item["folder"] / item["file"]).read_text(encoding="utf-8")
            for item in cls.manifest["papers"]
        }

    def test_three_long_papers_have_required_structure(self):
        self.assertEqual(len(self.manifest["papers"]), 3)
        for item in self.manifest["papers"]:
            text = self.texts[item["folder"]]
            self.assertGreater(len(text), 8000)
            self.assertIn("### 1.4 本文的研究动机与内容安排", text)
            self.assertIn("未同行评议", text)
            self.assertEqual(text.count("## 参考文献"), 1)
            expected = 5 if item["folder"] == "01_乙酰唑胺跨库证据链" else 4
            self.assertEqual(item["figures"], expected)

    def test_no_known_draft_errors_or_placeholder_citations(self):
        forbidden = ["release 20", "唯一检出", "0.000031902", "20.8333333333333332", "【文献", "标准化学计量归一化"]
        for text in self.texts.values():
            for phrase in forbidden:
                self.assertNotIn(phrase, text)

    def test_paper_two_subsections_are_unique(self):
        text = self.texts["02_CA表观比值不稳定性"]
        sections = re.findall(r"^### (3\.\d) ", text, flags=re.M)
        self.assertEqual(len(sections), len(set(sections)))
        self.assertIn("### 3.3 不执行跨文献合并的理由", text)

    def test_figures_exist_and_collection_links_resolve(self):
        for item in self.manifest["papers"]:
            for filename in item["figureFiles"]:
                path = PAPERS / item["folder"] / filename
                self.assertTrue(path.is_file(), str(path))
                self.assertGreater(path.stat().st_size, 10000)
        collection = (PAPERS / "前沿共生研究简报_合订本.md").read_text(encoding="utf-8")
        for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)", collection):
            self.assertTrue((PAPERS / target).is_file(), target)

    def test_docx_is_real_package(self):
        path = PAPERS / "前沿共生研究简报_合订本.docx"
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as docx:
            self.assertIn("word/document.xml", docx.namelist())
            document = docx.read("word/document.xml").decode("utf-8")
            self.assertGreater(document.count("<w:p"), 100)
            self.assertNotIn("unverified_llm_draft", document)

    def test_garden_final_uploads_are_read_back(self):
        report = json.loads((ROOT / "garden" / "run-report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["serversStopped"])
        self.assertEqual(len(report["finalUploads"]), 3)
        self.assertTrue(all(item["readback"] for item in report["finalUploads"]))


if __name__ == "__main__":
    unittest.main()

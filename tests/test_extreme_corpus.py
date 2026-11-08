import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_extreme_corpus.py"
SPEC = ROOT / "validation/extreme-corpus-audit.json"
CORPUS = ROOT / "docs/EXTREME_REPORTING_CORPUS_AUDIT.md"
CHECK = ROOT / "validation/extreme-corpus-check.json"


class ExtremeCorpusTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing extreme corpus validator: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("validate_extreme_corpus", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_sixteen_documents_are_split_into_three_review_classes(self):
        module = self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        documents = spec["documents"]
        self.assertEqual(len(documents), 16)
        self.assertEqual(sum(item["review_status"] == "complete" for item in documents), 2)
        self.assertEqual(sum(item["review_status"] == "descriptive_only" for item in documents), 4)
        self.assertEqual(sum(item["review_status"] == "companion_required" for item in documents), 10)
        self.assertEqual(module.validate_corpus(), [])

    def test_empty_corpus_is_rejected_for_every_companion_document(self):
        module = self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        errors = module.validate_corpus(corpus_text="")
        for item in spec["documents"]:
            if item["review_status"] == "companion_required":
                self.assertTrue(any(item["file"] in error for error in errors), item["file"])

    def test_ten_original_documents_remain_byte_identical(self):
        self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        for item in spec["documents"]:
            if item["review_status"] == "companion_required":
                self.assertEqual(hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest(), item["original_sha256"])

    def test_final_check_file_is_current(self):
        module = self.load_module()
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        self.assertEqual(module.build_check(), stored)
        self.assertEqual(stored["status"], "passed")
        self.assertEqual(stored["document_count"], 16)
        self.assertEqual(stored["companion_required_count"], 10)
        self.assertEqual(stored["unchanged_original_count"], 10)
        self.assertEqual(stored["error_count"], 0)
        self.assertEqual(stored["corpus_document_sha256"], hashlib.sha256(CORPUS.read_bytes()).hexdigest())
        self.assertEqual(stored["spec_sha256"], hashlib.sha256(SPEC.read_bytes()).hexdigest())
        self.assertEqual(stored["validator_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

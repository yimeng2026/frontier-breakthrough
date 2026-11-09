import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_extreme_corpus_v2.py"
SPEC = ROOT / "validation/extreme-corpus-v2-audit.json"
CORPUS = ROOT / "docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md"
CHECK = ROOT / "validation/extreme-corpus-v2-check.json"


class ExtremeCorpusV2Tests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 corpus validator: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("validate_extreme_corpus_v2", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_23_documents_have_expected_classes(self):
        module = self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertEqual(len(spec["documents"]), 23)
        self.assertEqual(sum(item["review_status"] == "companion_required" for item in spec["documents"]), 12)
        self.assertEqual(sum(item["review_status"] == "descriptive_only" for item in spec["documents"]), 7)
        self.assertEqual(sum(item["review_status"] == "complete" for item in spec["documents"]), 4)
        self.assertEqual(module.validate_corpus(), [])

    def test_new_seven_documents_are_classified_by_content(self):
        self.load_module()
        documents = json.loads(SPEC.read_text(encoding="utf-8"))["documents"][-7:]
        self.assertEqual([item["review_status"] for item in documents], ["companion_required", "companion_required", "complete", "descriptive_only", "complete", "descriptive_only", "descriptive_only"])
        self.assertEqual(documents[2]["file"], "docs/MAXIMUM_FULL_COMPOSITION_V2_2026-11-09.md")
        self.assertEqual(documents[4]["file"], "docs/ROSZMAN1_NATIVE_IDENTIFIABILITY_2026-11-09.md")

    def test_empty_corpus_is_rejected_for_every_companion_document(self):
        module = self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        errors = module.validate_corpus(corpus_text="")
        for item in spec["documents"]:
            if item["review_status"] == "companion_required":
                self.assertTrue(any(item["file"] in error for error in errors), item["file"])

    def test_ten_historical_originals_remain_byte_identical(self):
        self.load_module()
        previous = json.loads((ROOT / "validation/extreme-corpus-audit.json").read_text(encoding="utf-8"))
        for item in previous["documents"]:
            if item["review_status"] == "companion_required":
                self.assertEqual(hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest(), item["original_sha256"])

    def test_hash_tampering_is_rejected(self):
        module = self.load_module()
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        spec["documents"][0]["original_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            altered = Path(directory) / "altered.json"
            altered.write_text(json.dumps(spec), encoding="utf-8")
            saved = module.SPEC
            module.SPEC = altered
            try:
                errors = module.validate_corpus()
            finally:
                module.SPEC = saved
        self.assertTrue(any("Document hash changed" in error for error in errors))

    def test_final_check_file_is_current(self):
        module = self.load_module()
        stored = json.loads(CHECK.read_text(encoding="utf-8"))
        self.assertEqual(module.build_check(), stored)
        self.assertEqual(stored["status"], "passed")
        self.assertEqual(stored["document_count"], 23)
        self.assertEqual(stored["companion_required_count"], 12)
        self.assertEqual(stored["complete_count"], 4)
        self.assertEqual(stored["descriptive_only_count"], 7)
        self.assertEqual(stored["hash_matched_document_count"], 22)
        self.assertEqual(stored["unchanged_original_count"], 10)
        self.assertEqual(stored["error_count"], 0)
        self.assertTrue(stored["previous_files_preserved"])
        self.assertEqual(stored["corpus_document_sha256"], hashlib.sha256(CORPUS.read_bytes()).hexdigest())
        self.assertEqual(stored["spec_sha256"], hashlib.sha256(SPEC.read_bytes()).hexdigest())
        self.assertEqual(stored["validator_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_external_scope_amendment.py"


class ExternalScopeAmendmentTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing external scope amendment builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_external_scope_amendment", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_three_corrected_documents_preserve_every_original_field_except_limitations(self):
        module = self.load_module()
        documents = module.build_corrected_documents()
        self.assertEqual([item["id"] for item in documents], ["mgh17", "gauss1", "misra1a"])
        for item in documents:
            original = json.loads((ROOT / item["source"]).read_text(encoding="utf-8"))
            corrected = item["corrected"]
            self.assertEqual(set(corrected), set(original) | {"scope_correction"})
            for key in original:
                if key != "limitations":
                    self.assertEqual(corrected[key], original[key], f"{item['id']} changed {key}")
            self.assertEqual(corrected["limitations"][1:], original["limitations"][1:])
            self.assertEqual(len(corrected["limitations"]), len(original["limitations"]))
            display_name = {"mgh17": "MGH17", "gauss1": "Gauss1", "misra1a": "Misra1a"}[item["id"]]
            self.assertIn(display_name, corrected["limitations"][0])
            self.assertNotIn("Filip", corrected["limitations"][0])
            self.assertEqual(hashlib.sha256((ROOT / item["source"]).read_bytes()).hexdigest(), item["source_sha256"])
            self.assertEqual(corrected["scope_correction"]["changed_json_pointer"], "/limitations/0")
            self.assertFalse(corrected["scope_correction"]["numeric_results_modified"])
            self.assertTrue(corrected["scope_correction"]["original_file_preserved"])

    def test_final_audit_matches_outputs_and_original_protocol_hashes(self):
        module = self.load_module()
        stored = json.loads(module.AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(module.analyze(), stored)
        self.assertEqual(stored["correction_count"], 3)
        self.assertFalse(stored["numeric_results_modified"])
        self.assertTrue(stored["original_files_preserved"])
        self.assertEqual(stored["amendment_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        for record in stored["corrections"]:
            self.assertEqual(hashlib.sha256((ROOT / record["output"]).read_bytes()).hexdigest(), record["corrected_sha256"])
            self.assertEqual(hashlib.sha256((ROOT / record["source"]).read_bytes()).hexdigest(), record["source_sha256"])
            self.assertEqual(hashlib.sha256((ROOT / record["protocol"]).read_bytes()).hexdigest(), record["protocol_sha256"])


if __name__ == "__main__":
    unittest.main()

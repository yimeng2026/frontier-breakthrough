import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/audit_repository_integrity.py"
REPORT = ROOT / "validation/repository-integrity-report.json"


class RepositoryIntegrityTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing repository integrity audit: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("audit_repository_integrity", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_repository_audit_is_clean_and_current(self):
        module = self.load_module()
        report = module.audit()
        self.assertEqual(report["error_count"], 0, report["errors"])
        self.assertGreaterEqual(report["groups"]["readme_local_links"]["count"], 84)
        self.assertGreaterEqual(report["groups"]["document_figure_links"]["count"], 44)
        self.assertGreaterEqual(report["groups"]["word_manifests"]["count"], 36)
        self.assertEqual(report["groups"]["protocol_inputs"]["count"], 20)
        self.assertTrue(report["groups"]["dynamic_counts"]["readme_consistent"])
        self.assertFalse(report["decision"]["visual_qa_claimed"])
        stored = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report, stored)

    def test_broken_readme_link_is_detected(self):
        module = self.load_module()
        report = module.audit(readme_text="# [broken](docs/missing-file.md)")
        self.assertTrue(any("Broken README link" in error for error in report["errors"]))

    def test_docx_manifest_tampering_is_detected(self):
        module = self.load_module()
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "fake-word.json"
            path.write_text(json.dumps({"status": "passed", "file": "missing.docx", "bytes": 1, "sha256": "0" * 64}), encoding="utf-8")
            errors = module.audit_docx_manifest(path)
        self.assertTrue(errors)

    def test_protocol_missing_input_is_detected(self):
        module = self.load_module()
        import tempfile
        rules = json.loads((ROOT / "validation/repository-integrity-rules.json").read_text(encoding="utf-8"))
        rules["protocols"][0] = "validation/missing-protocol-input.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "rules.json"
            path.write_text(json.dumps(rules), encoding="utf-8")
            saved = module.RULES
            module.RULES = path
            try:
                report = module.audit()
            finally:
                module.RULES = saved
        self.assertTrue(any("Missing protocol input" in error for error in report["errors"]))

    def test_dynamic_count_drift_is_detected(self):
        module = self.load_module()
        report = module.audit(readme_text="# no valid counts")
        self.assertTrue(any("README evidence count" in error or "README graph count" in error for error in report["errors"]))

    def test_refresh_preserves_previous_receipt(self):
        module = self.load_module()
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "refresh-report.json"
            previous = '{"status":"previous"}\n'
            output.write_text(previous, encoding="utf-8")
            saved_output = module.OUTPUT
            saved_argv = sys.argv[:]
            module.OUTPUT = output
            sys.argv = ["audit_repository_integrity.py", "--refresh"]
            try:
                module.main()
            finally:
                module.OUTPUT = saved_output
                sys.argv = saved_argv
            backup = output.with_name("refresh-report-v1.json")
            self.assertEqual(backup.read_text(encoding="utf-8"), previous)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["error_count"], 0)


if __name__ == "__main__":
    unittest.main()

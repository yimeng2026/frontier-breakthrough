import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/analyze_roszman1_ellipsoid_coverage.py"
ADAPTER = ROOT / "scripts/external_coverage_scoped.py"


class Roszman1EllipsoidCoverageTests(unittest.TestCase):
    def load_analysis_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Roszman1 analysis wrapper: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_roszman1_ellipsoid_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_scope_adapter_uses_roszman1_text_and_preserves_hashes(self):
        module = self.load_analysis_module()
        protocol = module.json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
        summary = {"analysis_scope": {}, "limitations": ["Wrong generic Filip text", "Keep this limitation"]}
        scoped = module.analyze(runner=lambda protocol_path, runner_path: summary)
        self.assertEqual(scoped["limitations"][0], protocol["candidate_rule"]["scope_limitation"])
        self.assertIn("Roszman1 four-parameter arctangent", scoped["limitations"][0])
        self.assertNotIn("Filip", scoped["limitations"][0])
        self.assertEqual(scoped["limitations"][1], "Keep this limitation")
        self.assertEqual(scoped["analysis_scope"]["scope_adapter_sha256"], hashlib.sha256(ADAPTER.read_bytes()).hexdigest())
        self.assertEqual(scoped["analysis_runner_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())

    def prepare_fake_main(self, module, directory):
        module.OUT = Path(directory) / "summary.json"
        module.FIGURE = Path(directory) / "figure.png"
        summary = {"status": "fake_without_fitting"}
        def render(received, path):
            self.assertEqual(received, summary)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")
        return summary, lambda: summary, render

    def test_main_writes_real_output_files(self):
        module = self.load_analysis_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            summary, analyze, render = self.prepare_fake_main(module, directory)
            module.main(analyze_func=analyze, render_func=render)
            self.assertEqual(module.json.loads(module.OUT.read_text(encoding="utf-8")), summary)
            self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_main_refuses_to_overwrite_existing_outputs(self):
        module = self.load_analysis_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            summary, analyze, render = self.prepare_fake_main(module, directory)
            module.OUT.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                module.main(analyze_func=analyze, render_func=render)
            self.assertEqual(module.OUT.read_text(encoding="utf-8"), "preserve")
            self.assertFalse(module.FIGURE.exists())


if __name__ == "__main__":
    unittest.main()

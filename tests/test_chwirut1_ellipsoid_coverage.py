import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_chwirut1_ellipsoid_coverage.py"


class Chwirut1EllipsoidCoverageTests(unittest.TestCase):
    def load_analysis_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing Chwirut1 analysis wrapper: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("analyze_chwirut1_ellipsoid_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_scope_limitation_names_chwirut1_not_filip(self):
        module = self.load_analysis_module()
        protocol = module.json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
        summary = {
            "analysis_scope": {},
            "limitations": ["The cubic/cubic candidate is not the native Filip model", "Keep this limitation"],
        }
        scoped = module.analyze(runner=lambda protocol_path, runner_path: summary)
        self.assertEqual(scoped["limitations"][0], protocol["candidate_rule"]["scope_limitation"])
        self.assertIn("Chwirut1", scoped["limitations"][0])
        self.assertNotIn("Filip", scoped["limitations"][0])
        self.assertEqual(scoped["limitations"][1], "Keep this limitation")
        self.assertFalse(scoped["analysis_scope"]["independent_model_family_test"])

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

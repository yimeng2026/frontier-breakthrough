import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_repository_integrity_figure.py"


class RepositoryIntegrityFigureTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing repository integrity figure builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_repository_integrity_figure", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_figure_title_uses_actual_counts(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.FIGURE = Path(directory) / "figure.png"
            module.render_figure()
            self.assertIn("8 audit groups", plt.gcf().axes[0].get_title())
            self.assertIn("0 errors", plt.gcf().axes[0].get_title())
        plt.close("all")

    def test_final_figure_is_real(self):
        module = self.load_module()
        self.assertTrue(module.FIGURE.is_file())
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

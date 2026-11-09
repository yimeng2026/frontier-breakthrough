import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/build_extreme_corpus_v2_figure.py"


class ExtremeCorpusV2FigureTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing v2 corpus figure builder: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("build_extreme_corpus_v2_figure", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_figure_titles_match_current_counts(self):
        module = self.load_module()
        import matplotlib.pyplot as plt
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            module.FIGURE = Path(directory) / "figure.png"
            module.render_figure()
            self.assertIn("12 companion / 7 descriptive / 4 complete", plt.gcf().axes[0].get_title())
            self.assertIn("New 7", plt.gcf().axes[1].get_title())
        plt.close("all")

    def test_final_figure_is_real(self):
        module = self.load_module()
        self.assertTrue(module.FIGURE.is_file())
        self.assertEqual(module.FIGURE.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

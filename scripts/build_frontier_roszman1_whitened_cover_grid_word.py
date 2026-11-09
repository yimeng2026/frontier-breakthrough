"""Build the native illustrated Roszman1 whitened-cover report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五十八阶段：Roszman1 协方差白化覆盖与全预测区间"
SOURCE = ROOT / "docs/ROSZMAN1_WHITENED_COVER_GRID_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Roszman1协方差白化覆盖_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-roszman1-whitened-cover-grid-word.json"
EXPECTED = {"math": 3, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "roszman1_whitened_cover_grid"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_roszman1_whitened_cover_grid_markdown(source):
    saved = configure()
    try:
        return base.prepare_frontier_markdown(source)
    finally:
        restore(saved)


def main():
    saved = configure()
    try:
        base.main()
    finally:
        restore(saved)


if __name__ == "__main__":
    main()

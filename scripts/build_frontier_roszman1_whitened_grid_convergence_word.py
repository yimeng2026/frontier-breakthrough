"""Build the native illustrated Roszman1 whitened-grid convergence report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五十九阶段：Roszman1 白化网格增量诊断与共享极值见证"
SOURCE = ROOT / "docs/ROSZMAN1_WHITENED_GRID_CONVERGENCE_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Roszman1白化网格收敛与共享见证_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-roszman1-whitened-grid-convergence-word.json"
EXPECTED = {"math": 3, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "roszman1_whitened_grid_convergence"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_roszman1_whitened_grid_convergence_markdown(source):
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

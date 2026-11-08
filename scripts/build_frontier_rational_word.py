"""Build the Hahn1 rational-model and denominator-boundary Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第三阶段：有理模型外推与分母边界"
SOURCE = ROOT / "docs/RATIONAL_2026-11-08.md"
OUTPUT = ROOT / "papers/前沿共生有理模型与分母边界_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-rational-word.json"
EXPECTED = {"math": 7, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "rational"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_rational_markdown(source):
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

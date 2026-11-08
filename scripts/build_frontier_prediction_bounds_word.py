"""Build the certified prediction-box bound Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第十一阶段：参数盒内预测误差界"
SOURCE = ROOT / "docs/PREDICTION_BOUNDS_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生参数盒预测界_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-prediction-bounds-word.json"
EXPECTED = {"math": 12, "images": 1, "tables": 3}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "prediction_bounds"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_prediction_bounds_markdown(source):
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

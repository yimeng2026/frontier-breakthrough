"""Build the native illustrated Chwirut1 prediction-proof dissociation report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第二十二阶段：Chwirut1 同族外部审计与预测—证明解离"
SOURCE = ROOT / "docs/CHWIRUT1_COVERAGE_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Chwirut1预测证明解离_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-chwirut1-coverage-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "chwirut1_coverage"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_chwirut1_coverage_markdown(source):
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

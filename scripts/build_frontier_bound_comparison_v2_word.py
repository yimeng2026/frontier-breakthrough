"""Build the native illustrated four-external and seven-dataset comparison report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第二十一阶段：四外部与七组界组成对照"
SOURCE = ROOT / "docs/BOUND_COMPARISON_V2_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生四外部与七组界组成对照_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-bound-comparison-v2-word.json"
EXPECTED = {"math": 2, "images": 2, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "bound_comparison_v2"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_bound_comparison_v2_markdown(source):
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

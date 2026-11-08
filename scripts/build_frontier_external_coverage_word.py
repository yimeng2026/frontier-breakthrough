"""Build the reusable external-coverage comparison Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第十五阶段：可复用外部覆盖协议与跨数据对照"
SOURCE = ROOT / "docs/EXTERNAL_COVERAGE_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生外部覆盖协议_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-external-coverage-word.json"
EXPECTED = {"math": 1, "images": 2, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "external_coverage"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_external_coverage_markdown(source):
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

"""Build the Gauss1 counterexample and three-dataset comparison Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第十六阶段：Gauss1 外部反例与三数据证据轴对照"
SOURCE = ROOT / "docs/GAUSS1_EXTERNAL_COVERAGE_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Gauss1外部反例_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-gauss1-coverage-word.json"
EXPECTED = {"math": 1, "images": 3, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "gauss1_coverage"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_gauss1_coverage_markdown(source):
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

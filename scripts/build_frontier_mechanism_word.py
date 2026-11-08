"""Build the Hahn1 fold-one mechanism-diagnosis Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五阶段：Hahn1 第 1 折失效机制诊断"
SOURCE = ROOT / "docs/MECHANISM_2026-11-08.md"
OUTPUT = ROOT / "papers/前沿共生Hahn1失效机制诊断_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-mechanism-word.json"
EXPECTED = {"math": 14, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "mechanism"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_mechanism_markdown(source):
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

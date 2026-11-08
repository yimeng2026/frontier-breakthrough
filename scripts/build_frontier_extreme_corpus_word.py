"""Build the native illustrated corpus-wide extreme-value classification report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第二十八阶段：既有报告极值表述的分级复核"
SOURCE = ROOT / "docs/EXTREME_REPORTING_CORPUS_AUDIT.md"
OUTPUT = ROOT / "papers/前沿共生既有报告极值表述分级复核_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-extreme-corpus-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "extreme_corpus"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_extreme_corpus_markdown(source):
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

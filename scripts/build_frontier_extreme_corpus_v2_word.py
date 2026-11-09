"""Build the native illustrated expanded extreme-corpus report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第三十六阶段：极值相关报告全集分级（第二版）"
SOURCE = ROOT / "docs/EXTREME_REPORTING_CORPUS_V2_AUDIT.md"
OUTPUT = ROOT / "papers/前沿共生极值报告全集分级V2_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-extreme-corpus-v2-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "extreme_corpus_v2"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_extreme_corpus_v2_markdown(source):
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

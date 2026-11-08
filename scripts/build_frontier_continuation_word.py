"""Build the continuation report as a separate native illustrated Word document."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生续展：双尾外推与求解器复核"
SOURCE = ROOT / "docs/CONTINUATION_2026-11-08.md"
OUTPUT = ROOT / "papers/前沿共生续展_双尾外推与求解器复核_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-continuation-word.json"
EXPECTED = {"math": 7, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "continuation"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_continuation_markdown(source):
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

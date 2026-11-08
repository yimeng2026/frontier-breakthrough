"""Build the native illustrated external bound-decomposition Word report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第十八阶段：三数据界组成对照与机制异质性"
SOURCE = ROOT / "docs/EXTERNAL_BOUND_DECOMPOSITION_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生外部界组成对照_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-external-bound-decomposition-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "external_bound_decomposition"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_external_bound_decomposition_markdown(source):
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

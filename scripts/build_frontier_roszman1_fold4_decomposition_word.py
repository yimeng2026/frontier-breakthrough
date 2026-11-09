"""Build the native illustrated Roszman1 fold-4 error decomposition."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第三十九阶段：Roszman1 第 4 折误差贡献分解"
SOURCE = ROOT / "docs/ROSZMAN1_NATIVE_FOLD4_ERROR_DECOMPOSITION_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Roszman1第4折误差分解_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-roszman1-fold4-decomposition-word.json"
EXPECTED = {"math": 3, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "roszman1_fold4_decomposition"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_roszman1_fold4_decomposition_markdown(source):
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

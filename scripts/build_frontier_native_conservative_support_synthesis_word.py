"""Build the native illustrated conservative-support synthesis report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第五十五阶段：三模型保守支撑与局部收紧综合"
SOURCE = ROOT / "docs/NATIVE_CONSERVATIVE_SUPPORT_SYNTHESIS_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生三模型保守支撑综合_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-native-conservative-support-synthesis-word.json"
EXPECTED = {"math": 3, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "native_conservative_support_synthesis"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_native_conservative_support_synthesis_markdown(source):
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

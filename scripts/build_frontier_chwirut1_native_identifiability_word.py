"""Build the native illustrated Chwirut1 identifiability and denominator report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第四十阶段：Chwirut1 原生参数可识别性与分母诊断"
SOURCE = ROOT / "docs/CHWIRUT1_NATIVE_IDENTIFIABILITY_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Chwirut1原生参数可识别性_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-chwirut1-native-identifiability-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 6}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "chwirut1_native_identifiability"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_chwirut1_native_identifiability_markdown(source):
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

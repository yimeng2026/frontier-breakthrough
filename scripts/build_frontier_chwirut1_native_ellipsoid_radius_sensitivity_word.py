"""Build the native illustrated Chwirut1 ellipsoid radius-sensitivity report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第四十五阶段：Chwirut1 原生椭球半径敏感性与临界半径"
SOURCE = ROOT / "docs/CHWIRUT1_NATIVE_ELLIPSOID_RADIUS_SENSITIVITY_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生Chwirut1原生椭球半径敏感性_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-chwirut1-native-ellipsoid-radius-sensitivity-word.json"
EXPECTED = {"math": 2, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "chwirut1_native_ellipsoid_radius_sensitivity"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_chwirut1_native_ellipsoid_radius_sensitivity_markdown(source):
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

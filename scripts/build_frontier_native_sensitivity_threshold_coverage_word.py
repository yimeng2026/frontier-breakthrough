"""Build the native illustrated sensitivity-threshold coverage report."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第四十三阶段：三模型局部敏感度固定阈值覆盖审计"
SOURCE = ROOT / "docs/NATIVE_SENSITIVITY_THRESHOLD_COVERAGE_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生三模型敏感度阈值覆盖_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-native-sensitivity-threshold-coverage-word.json"
EXPECTED = {"math": 1, "images": 1, "tables": 4}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "native_sensitivity_threshold_coverage"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_native_sensitivity_threshold_coverage_markdown(source):
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

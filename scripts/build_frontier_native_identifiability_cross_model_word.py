"""Build the native illustrated cross-model identifiability synthesis."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第四十二阶段：三模型局部可识别性受限综合"
SOURCE = ROOT / "docs/NATIVE_IDENTIFIABILITY_CROSS_MODEL_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生三模型局部可识别性综合_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-native-identifiability-cross-model-word.json"
EXPECTED = {"math": 1, "images": 1, "tables": 5}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "native_identifiability_cross_model"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_native_identifiability_cross_model_markdown(source):
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

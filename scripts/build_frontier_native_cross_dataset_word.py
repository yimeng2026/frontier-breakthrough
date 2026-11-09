"""Build the native illustrated three-dataset holdout synthesis."""

from pathlib import Path

import build_frontier_word as base

ROOT = Path(__file__).resolve().parents[1]
TITLE = "前沿共生第三十八阶段：三数据原生模型同折对照综合"
SOURCE = ROOT / "docs/NATIVE_CROSS_DATASET_SYNTHESIS_2026-11-09.md"
OUTPUT = ROOT / "papers/前沿共生三数据原生同折综合_图文完整版.docx"
VALIDATION = ROOT / "validation/frontier-native-cross-dataset-word.json"
EXPECTED = {"math": 7, "images": 1, "tables": 6}


def configure():
    saved = {name: getattr(base, name) for name in ["REPORT_MODE", "TITLE", "SOURCE", "OUTPUT", "VALIDATION", "EXPECTED"]}
    base.REPORT_MODE = "native_cross_dataset"
    base.TITLE = TITLE
    base.SOURCE = SOURCE
    base.OUTPUT = OUTPUT
    base.VALIDATION = VALIDATION
    base.EXPECTED = EXPECTED
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(base, name, value)


def prepare_native_cross_dataset_markdown(source):
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
